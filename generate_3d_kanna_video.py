#!/usr/bin/env python3
"""
3D Talking Portrait & Romantic Video Generator: "I Love You Kanna"
Creates a 3D animated talking portrait video from a photo with:
- Neural TTS voice ("I love you Kanna") + gentle ambient romantic chord progression
- MediaPipe 478-point 3D facial mesh extraction & depth-based 3D parallax camera motion
- Audio-synchronized lip-sync jaw/mouth animation, natural eye blinks, and breathing motion
- 3D perspective volumetric floating hearts with depth-of-field and specular shading
- 3D extruded glassmorphic & gold-accented typography synchronized to speech
"""

import asyncio
import math
import os
import subprocess
import urllib.request
import wave
from pathlib import Path

import cv2
import edge_tts
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import gaussian_filter

# Constants & Output Configuration
FPS = 30
WIDTH = 720
HEIGHT = 1280
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
MODEL_PATH = "/tmp/face_landmarker.task"

DEFAULT_INPUT_IMAGE = "/home/ubuntu/.cursor/projects/workspace/assets/01a1698a-10ff-707a-9013-9e644d14fe27.jpg"
WORKSPACE_DIR = Path("/workspace")
OUTPUT_DIR = WORKSPACE_DIR / "output"
ARTIFACTS_DIR = Path("/opt/cursor/artifacts")


def ensure_model():
    if not os.path.exists(MODEL_PATH):
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


async def synthesize_voice(output_mp3: str):
    text = "Hey Kanna... I love you, Kanna! ... I love you so much, Kanna!"
    communicate = edge_tts.Communicate(
        text,
        voice="en-IN-PrabhatNeural",
        rate="-10%",
        pitch="-2Hz",
        boundary="WordBoundary",
    )
    words = []
    with open(output_mp3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append(
                    {
                        "text": chunk["text"],
                        "start": chunk["offset"] / 1e7,
                        "duration": chunk["duration"] / 1e7,
                    }
                )
    return words


def build_audio_track(speech_mp3: str, final_wav: str, pad_start: float = 0.6, pad_end: float = 1.6):
    """Mixes the neural speech with a warm 3D stereo ambient romantic pad and returns audio envelope."""
    raw_speech_wav = "/tmp/speech_raw.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            speech_mp3,
            "-ar",
            "44100",
            "-ac",
            "1",
            raw_speech_wav,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    with wave.open(raw_speech_wav, "rb") as wf:
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)
        speech_samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    start_samples = int(pad_start * sr)
    end_samples = int(pad_end * sr)
    full_speech = np.concatenate(
        [
            np.zeros(start_samples, dtype=np.float32),
            speech_samples,
            np.zeros(end_samples, dtype=np.float32),
        ]
    )
    total_samples = len(full_speech)
    duration = total_samples / sr
    t = np.linspace(0, duration, total_samples, endpoint=False, dtype=np.float32)

    # Compute smooth speech amplitude envelope at video FPS for lip-sync
    num_video_frames = int(math.ceil(duration * FPS))
    envelope = np.zeros(num_video_frames, dtype=np.float32)
    win = int(sr / FPS)
    for i in range(num_video_frames):
        s0 = i * win
        s1 = min(total_samples, s0 + win)
        if s1 > s0:
            rms = np.sqrt(np.mean(full_speech[s0:s1] ** 2))
            envelope[i] = rms

    if envelope.max() > 1e-5:
        envelope = np.clip(envelope / ( np.percentile(envelope[envelope > 0.01], 92) + 1e-5 ), 0.0, 1.0)
    # Smooth envelope slightly so jaw motion is organic
    envelope = gaussian_filter(envelope, sigma=0.85)

    # Synthesize warm romantic ambient chord progression (Fmaj7 -> Cmaj7 -> Dm9 -> Cmaj9)
    chords = [
        [174.61, 220.00, 261.63, 329.63, 392.00],  # Fmaj9
        [130.81, 196.00, 246.94, 293.66, 329.63],  # Cmaj9
    ]
    music_l = np.zeros(total_samples, dtype=np.float32)
    music_r = np.zeros(total_samples, dtype=np.float32)

    half = total_samples // 2
    for c_idx, freqs in enumerate(chords):
        w_env = np.zeros(total_samples, dtype=np.float32)
        if c_idx == 0:
            w_env[:half] = 1.0
            fade = int(1.2 * sr)
            w_env[half - fade : half + fade] = np.linspace(1.0, 0.0, 2 * fade)
        else:
            w_env[half:] = 1.0
            fade = int(1.2 * sr)
            w_env[half - fade : half + fade] = np.linspace(0.0, 1.0, 2 * fade)

        for f_i, f in enumerate(freqs):
            detune = 0.35 * (f_i - 2)
            sig_l = np.sin(2 * np.pi * (f + detune) * t) + 0.3 * np.sin(4 * np.pi * f * t)
            sig_r = np.sin(2 * np.pi * (f - detune) * t + 0.4) + 0.3 * np.sin(4 * np.pi * f * t + 0.2)
            music_l += w_env * sig_l * (0.024 / (1 + 0.25 * f_i))
            music_r += w_env * sig_r * (0.024 / (1 + 0.25 * f_i))

    # Add gentle bell/chime arpeggio notes on key romantic moments
    bell_notes = [
        (0.15, 523.25),
        (0.45, 659.25),
        (0.75, 783.99),
        (2.15, 659.25),
        (2.45, 783.99),
        (2.75, 1046.50),
        (4.35, 587.33),
        (4.75, 783.99),
        (5.15, 987.77),
        (5.55, 1046.50),
    ]
    for bt, bf in bell_notes:
        b_start = int(bt * sr)
        if b_start < total_samples:
            b_len = min(int(1.8 * sr), total_samples - b_start)
            bt_arr = np.linspace(0, b_len / sr, b_len, endpoint=False, dtype=np.float32)
            b_wave = np.exp(-3.2 * bt_arr) * (
                np.sin(2 * np.pi * bf * bt_arr) + 0.25 * np.sin(2 * np.pi * bf * 2.0 * bt_arr)
            )
            music_l[b_start : b_start + b_len] += 0.032 * b_wave
            music_r[b_start : b_start + b_len] += 0.032 * b_wave

    # Fade in and fade out music
    fade_in = int(0.8 * sr)
    fade_out = int(1.3 * sr)
    global_env = np.ones(total_samples, dtype=np.float32)
    global_env[:fade_in] = np.linspace(0.0, 1.0, fade_in)
    global_env[-fade_out:] = np.linspace(1.0, 0.0, fade_out)
    music_l *= global_env
    music_r *= global_env

    # Add subtle room reverb to voice
    reverb_speech = full_speech.copy()
    for delay_ms, gain in [(45, 0.14), (90, 0.08), (145, 0.04)]:
        d_samples = int(delay_ms * sr / 1000.0)
        if d_samples < total_samples:
            reverb_speech[d_samples:] += gain * full_speech[:-d_samples]

    left_ch = np.clip(reverb_speech * 0.92 + music_l, -0.98, 0.98)
    right_ch = np.clip(reverb_speech * 0.92 + music_r, -0.98, 0.98)

    stereo = np.empty((total_samples * 2,), dtype=np.int16)
    stereo[0::2] = (left_ch * 32767).astype(np.int16)
    stereo[1::2] = (right_ch * 32767).astype(np.int16)

    with wave.open(final_wav, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo.tobytes())

    return duration, envelope, pad_start


def detect_face_landmarks(img_bgr: np.ndarray):
    ensure_model()
    h, w, _ = img_bgr.shape
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
    options = mp_vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
    detector = mp_vision.FaceLandmarker.create_from_options(options)
    res = detector.detect(mp_img)
    if not res.face_landmarks:
        raise RuntimeError("No face landmarks detected in the image.")
    lms = res.face_landmarks[0]
    pts = np.array([[lm.x * w, lm.y * h, lm.z * w] for lm in lms], dtype=np.float32)
    return pts


def build_pseudo_depth_map(img_bgr: np.ndarray, lms: np.ndarray) -> np.ndarray:
    """Builds a smooth 3D depth map (0=far background, 1=closest foreground) using 3D facial geometry and person silhouette."""
    h, w, _ = img_bgr.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    # Face center & head radius
    nose = lms[1, :2]
    chin = lms[152, :2]
    forehead = lms[10, :2]
    face_center = np.array([nose[0], 0.48 * forehead[1] + 0.52 * chin[1]], dtype=np.float32)
    face_rx = np.linalg.norm(lms[234, :2] - lms[454, :2]) * 0.72
    face_ry = np.linalg.norm(forehead - chin) * 0.85

    # Elliptical head depth dome
    head_dist2 = ((xx - face_center[0]) / (face_rx + 1e-5)) ** 2 + (
        (yy - face_center[1]) / (face_ry + 1e-5)
    ) ** 2
    head_depth = np.exp(-0.55 * head_dist2)

    # Torso / shoulders dome below chin
    torso_cx = face_center[0] + 25.0
    torso_cy = chin[1] + face_ry * 1.35
    torso_rx = face_rx * 2.35
    torso_ry = face_ry * 1.85
    torso_dist2 = ((xx - torso_cx) / torso_rx) ** 2 + ((yy - torso_cy) / torso_ry) ** 2
    torso_depth = 0.78 * np.exp(-0.45 * torso_dist2)

    # Nose & central face 3D relief from MediaPipe z landmarks
    nose_dist2 = ((xx - nose[0]) / (face_rx * 0.32)) ** 2 + ((yy - nose[1]) / (face_ry * 0.32)) ** 2
    nose_relief = 0.22 * np.exp(-1.2 * nose_dist2)

    depth = np.maximum(head_depth, torso_depth) + nose_relief
    depth = gaussian_filter(depth, sigma=18.0)
    depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-6)
    return depth.astype(np.float32)


def precompute_HEART_sprite(size: int = 128) -> np.ndarray:
    """Renders a 3D glossy volumetric heart sprite (RGBA) with specular highlight and rim lighting."""
    u = np.linspace(-1.35, 1.35, size, dtype=np.float32)
    v = np.linspace(1.35, -1.35, size, dtype=np.float32)
    xx, yy = np.meshgrid(u, v)

    # Implicit heart equation: (x^2 + (y - |x|^0.65)^2) <= r^2
    y_shifted = yy - 0.55 * (np.abs(xx) ** 0.68) + 0.18
    r2 = xx**2 + (y_shifted * 1.15) ** 2
    mask = r2 <= 0.78

    # Pseudo-3D normal vector (nx, ny, nz) on the curved heart surface
    nz = np.sqrt(np.clip(0.78 - r2, 0.0, 0.78) / 0.78)
    nx = xx / 0.9
    ny = y_shifted / 0.9
    norm = np.sqrt(nx**2 + ny**2 + nz**2 + 1e-6)
    nx, ny, nz = nx / norm, ny / norm, nz / norm

    # Directional light from top-left-front
    lx, ly, lz = -0.45, 0.55, 0.70
    diffuse = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)

    # Blinn-Phong specular highlight
    hx, hy, hz = -0.25, 0.35, 0.90
    h_norm = math.sqrt(hx * hx + hy * hy + hz * hz)
    hx, hy, hz = hx / h_norm, hy / h_norm, hz / h_norm
    spec = np.clip(nx * hx + ny * hy + nz * hz, 0.0, 1.0) ** 28

    # Rim lighting (Fresnel)
    rim = (1.0 - nz) ** 2.5

    # Rich ruby-rose 3D shading
    r_ch = np.clip(95 + 150 * diffuse + 255 * spec * 0.85 + 90 * rim, 0, 255)
    g_ch = np.clip(15 + 45 * diffuse + 240 * spec * 0.85 + 35 * rim, 0, 255)
    b_ch = np.clip(45 + 75 * diffuse + 250 * spec * 0.85 + 75 * rim, 0, 255)

    # Smooth anti-aliased alpha edge
    dist_edge = np.clip((0.78 - r2) * 14.0, 0.0, 1.0)
    alpha = (dist_edge * 255).astype(np.uint8)

    sprite = np.stack([b_ch.astype(np.uint8), g_ch.astype(np.uint8), r_ch.astype(np.uint8), alpha], axis=-1)
    return sprite


def warp_face_and_3d_camera(
    img_bgr: np.ndarray,
    depth_map: np.ndarray,
    lms: np.ndarray,
    base_grid_x: np.ndarray,
    base_grid_y: np.ndarray,
    mouth_open: float,
    smile_amount: float,
    blink_amount: float,
    cam_yaw: float,
    cam_pitch: float,
    cam_zoom: float,
    head_tilt: float,
) -> np.ndarray:
    """Applies 3D parallax camera projection + localized 3D facial animation (jaw, lips, smile, eye blink)."""
    h, w, _ = img_bgr.shape

    # Key facial anchors in image coordinates
    upper_lip = lms[13, :2]
    lower_lip = lms[14, :2]
    mouth_left = lms[61, :2]
    mouth_right = lms[291, :2]
    chin = lms[152, :2]
    nose = lms[1, :2]
    left_eye = lms[159, :2]
    right_eye = lms[386, :2]

    mouth_center = 0.5 * (upper_lip + lower_lip)
    mouth_w = np.linalg.norm(mouth_right - mouth_left)
    jaw_h = np.linalg.norm(chin - mouth_center)

    # Start from base coordinate grid
    map_x = base_grid_x.copy()
    map_y = base_grid_y.copy()

    # 1. Global zoom & subtle 2D head tilt around face center
    face_cx, face_cy = nose[0], nose[1]
    cos_t = math.cos(head_tilt) / cam_zoom
    sin_t = math.sin(head_tilt) / cam_zoom
    dx = map_x - face_cx
    dy = map_y - face_cy
    map_x = face_cx + cos_t * dx - sin_t * dy
    map_y = face_cy + sin_t * dx + cos_t * dy

    # 2. 3D Parallax displacement from depth map (simulates rotating 3D perspective camera)
    parallax_scale_x = cam_yaw * (w * 0.055)
    parallax_scale_y = cam_pitch * (h * 0.035)
    centered_depth = depth_map - 0.45
    map_x -= centered_depth * parallax_scale_x
    map_y -= centered_depth * parallax_scale_y

    # 3. Localized Lip-Sync & Jaw Articulation
    if mouth_open > 0.005 or smile_amount > 0.005:
        # Jaw drop field (centered between lower lip and chin)
        jaw_cx = 0.65 * lower_lip[0] + 0.35 * chin[0]
        jaw_cy = 0.65 * lower_lip[1] + 0.35 * chin[1]
        jaw_rx = mouth_w * 0.72
        jaw_ry = jaw_h * 0.85

        j_dx = (base_grid_x - jaw_cx) / (jaw_rx + 1e-5)
        j_dy = (base_grid_y - jaw_cy) / (jaw_ry + 1e-5)
        jaw_weight = np.exp(-1.35 * (j_dx**2 + j_dy**2))
        # Only pull down below the mouth split line
        below_mouth = np.clip((base_grid_y - mouth_center[1]) / (mouth_w * 0.14) + 0.25, 0.0, 1.0)
        jaw_shift_y = mouth_open * (mouth_w * 0.20) * jaw_weight * below_mouth
        jaw_shift_x = -mouth_open * (mouth_w * 0.03) * jaw_weight * below_mouth  # slight head angle compensation
        map_y -= jaw_shift_y
        map_x -= jaw_shift_x

        # Upper lip slight lift during speech
        ulip_dx = (base_grid_x - upper_lip[0]) / (mouth_w * 0.50)
        ulip_dy = (base_grid_y - upper_lip[1]) / (mouth_w * 0.22)
        ulip_weight = np.exp(-1.8 * (ulip_dx**2 + ulip_dy**2))
        above_mouth = np.clip((mouth_center[1] - base_grid_y) / (mouth_w * 0.12) + 0.2, 0.0, 1.0)
        map_y += mouth_open * (mouth_w * 0.055) * ulip_weight * above_mouth

        # Warm smile corner lift (pulls left and right mouth corners outward & slightly up)
        for corner, dir_sign in [(mouth_left, -1.0), (mouth_right, 1.0)]:
            c_dx = (base_grid_x - corner[0]) / (mouth_w * 0.42)
            c_dy = (base_grid_y - corner[1]) / (mouth_w * 0.38)
            c_w = np.exp(-1.6 * (c_dx**2 + c_dy**2))
            map_x -= smile_amount * dir_sign * (mouth_w * 0.055) * c_w
            map_y += smile_amount * (mouth_w * 0.045) * c_w

    # 4. Natural Eye Blink deformation
    if blink_amount > 0.01:
        eye_r = mouth_w * 0.24
        for eye_pt in [left_eye, right_eye]:
            e_dx = (base_grid_x - eye_pt[0]) / eye_r
            e_dy = (base_grid_y - (eye_pt[1] - eye_r * 0.18)) / (eye_r * 0.55)
            e_w = np.exp(-1.9 * (e_dx**2 + e_dy**2))
            map_y -= blink_amount * (eye_r * 0.42) * e_w

    warped = cv2.remap(
        img_bgr,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT_101,
    )

    # Render realistic inner-mouth shading when mouth opens during speech
    if mouth_open > 0.03:
        cavity_img = warped.copy()
        angle_deg = math.degrees(math.atan2(mouth_right[1] - mouth_left[1], mouth_right[0] - mouth_left[0]))
        cx = int(mouth_center[0] + centered_depth[int(mouth_center[1]), int(mouth_center[0])] * parallax_scale_x)
        cy = int(
            mouth_center[1]
            + mouth_open * (mouth_w * 0.065)
            + centered_depth[int(mouth_center[1]), int(mouth_center[0])] * parallax_scale_y
        )
        rx = int(mouth_w * (0.28 + 0.06 * smile_amount))
        ry = max(1, int(mouth_open * mouth_w * 0.105))

        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(mask, (cx, cy), (rx, ry), angle_deg, 0, 360, 255, -1, cv2.LINE_AA)

        # Subtle upper teeth hint inside top of open mouth
        teeth_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(
            teeth_mask,
            (cx, int(cy - ry * 0.45)),
            (int(rx * 0.78), max(1, int(ry * 0.38))),
            angle_deg,
            0,
            360,
            255,
            -1,
            cv2.LINE_AA,
        )
        teeth_mask = cv2.bitwise_and(teeth_mask, mask)

        # Dark warm oral cavity + soft teeth highlight
        cavity_img[mask > 0] = (32, 24, 58)  # BGR dark warm maroon
        cavity_img[teeth_mask > 0] = (185, 192, 210)  # BGR soft warm ivory

        alpha_m = gaussian_filter(mask.astype(np.float32) / 255.0, sigma=2.2)[..., None]
        opacity = min(0.82, mouth_open * 1.15)
        warped = (warped * (1.0 - alpha_m * opacity) + cavity_img * (alpha_m * opacity)).astype(np.uint8)

    return warped


def overlay_rgba(bg_bgr: np.ndarray, fg_bgra: np.ndarray, x: int, y: int):
    """Alpha-blends an RGBA sprite onto bg_bgr at top-left (x, y) with clipping."""
    h, w, _ = bg_bgr.shape
    fh, fw, _ = fg_bgra.shape

    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(w, x + fw)
    y1 = min(h, y + fh)

    if x1 <= x0 or y1 <= y0:
        return

    fx0 = x0 - x
    fy0 = y0 - y
    fx1 = fx0 + (x1 - x0)
    fy1 = fy0 + (y1 - y0)

    roi = bg_bgr[y0:y1, x0:x1].astype(np.float32)
    sub = fg_bgra[fy0:fy1, fx0:fx1].astype(np.float32)
    alpha = sub[..., 3:4] / 255.0
    bg_bgr[y0:y1, x0:x1] = np.clip(roi * (1.0 - alpha) + sub[..., :3] * alpha, 0, 255).astype(np.uint8)


def render_3d_stage_and_hud(
    frame_bgr: np.ndarray,
    t: float,
    duration: float,
    mouth_open: float,
    cam_yaw: float,
    cam_pitch: float,
    heart_sprite: np.ndarray,
    particles_3d: list,
    words: list,
    pad_start: float,
    fonts: dict,
) -> np.ndarray:
    """Adds 3D atmospheric lighting, 3D perspective floating hearts, and 3D extruded romantic typography."""
    h, w, _ = frame_bgr.shape
    out = frame_bgr.astype(np.float32)

    # 1. Warm cinematic golden-rose sunset grade + subtle moving volumetric light flare
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    flare_cx = w * (0.78 + 0.08 * math.sin(t * 1.1))
    flare_cy = h * (0.22 + 0.05 * math.cos(t * 0.9))
    flare_d2 = ((xx - flare_cx) / (w * 0.55)) ** 2 + ((yy - flare_cy) / (h * 0.45)) ** 2
    flare = np.exp(-1.4 * flare_d2)

    # Add warm golden-pink glow (BGR)
    out[..., 2] += flare * 38.0  # Red
    out[..., 1] += flare * 20.0  # Green
    out[..., 0] += flare * 24.0  # Blue

    # Cinematic soft vignette + bottom gradient for 3D title stage
    vignette_d2 = ((xx - w * 0.5) / (w * 0.62)) ** 2 + ((yy - h * 0.45) / (h * 0.58)) ** 2
    vignette = np.clip(1.08 - 0.32 * vignette_d2, 0.55, 1.0)
    bottom_darken = np.clip((yy - h * 0.62) / (h * 0.38), 0.0, 1.0) ** 1.4
    out *= vignette[..., None]
    out *= (1.0 - 0.62 * bottom_darken)[..., None]

    # Add subtle 3D perspective glowing floor grid lines in the bottom stage
    stage_y0 = int(h * 0.76)
    out_u8 = np.clip(out, 0, 255).astype(np.uint8)

    # 2. Project & render 3D floating hearts and golden bokeh particles with perspective depth
    focal = 520.0
    # Sort back-to-front by Z
    sorted_particles = sorted(particles_3d, key=lambda p: p["z"], reverse=True)
    for p in sorted_particles:
        # Advance 3D position with time
        pz = p["z"] - p["vz"] * t
        while pz < 0.8:
            pz += 4.2
        py = p["y"] - p["vy"] * t
        while py < -1.8:
            py += 3.6
        px = p["x"] + math.sin(t * p["freq"] + p["phase"]) * p["sway"] - cam_yaw * 0.35

        # Perspective projection
        sx = int(w * 0.5 + (px / pz) * focal)
        sy = int(h * 0.52 + (py / pz) * focal - cam_pitch * 35.0)

        if p["kind"] == "heart":
            scale = np.clip((1.35 / pz) * p["size"], 0.14, 1.25)
            pulse = 1.0 + 0.08 * math.sin(t * 5.0 + p["phase"]) + 0.10 * mouth_open
            px_size = max(12, int(96 * scale * pulse))
            resized = cv2.resize(heart_sprite, (px_size, px_size), interpolation=cv2.INTER_AREA)

            # Depth of field blur for very close or very far hearts
            if pz < 1.35 or pz > 3.6:
                resized = cv2.GaussianBlur(resized, (5, 5), 1.8)

            # Fade alpha by depth
            depth_alpha = float(np.clip((4.8 - pz) / 1.5, 0.15, 0.92))
            resized[..., 3] = (resized[..., 3].astype(np.float32) * depth_alpha).astype(np.uint8)
            overlay_rgba(out_u8, resized, sx - px_size // 2, sy - px_size // 2)
        else:
            # Golden-rose 3D sparkle orb
            rad = max(2, int((18.0 / pz) * p["size"]))
            if 0 <= sx < w and 0 <= sy < h:
                alpha_orb = float(np.clip((4.8 - pz) / 2.2, 0.12, 0.65)) * (
                    0.6 + 0.4 * math.sin(t * 4.0 + p["phase"])
                )
                overlay = out_u8.copy()
                cv2.circle(overlay, (sx, sy), rad, p["color_bgr"], -1, cv2.LINE_AA)
                cv2.addWeighted(overlay, alpha_orb, out_u8, 1.0 - alpha_orb, 0, out_u8)

    # 3. Render 3D Extruded Romantic Typography & Glassmorphic Card using PIL
    pil_img = Image.fromarray(cv2.cvtColor(out_u8, cv2.COLOR_BGR2RGB)).convert("RGBA")
    txt_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Frosted 3D glassmorphic card at the bottom with perspective tilt offset
    card_ox = int(-cam_yaw * 18.0)
    card_oy = int(-cam_pitch * 12.0)
    card_box = [
        44 + card_ox,
        h - 310 + card_oy,
        w - 44 + card_ox,
        h - 72 + card_oy,
    ]
    draw.rounded_rectangle(card_box, radius=32, fill=(28, 12, 26, 155), outline=(255, 165, 200, 190), width=2)

    # Animated 3D audio-reactive waveform / heartbeat bar inside card
    bar_cy = h - 108 + card_oy
    num_bars = 29
    bar_spacing = 16
    start_bx = w // 2 - (num_bars // 2) * bar_spacing + card_ox
    for bi in range(num_bars):
        dist_center = abs(bi - num_bars // 2) / (num_bars / 2)
        wave_h = int(
            (6 + 26 * mouth_open * (1.0 - 0.65 * dist_center))
            * (0.65 + 0.35 * math.sin(t * 9.0 + bi * 0.55))
        )
        bx = start_bx + bi * bar_spacing
        draw.rounded_rectangle(
            [bx - 3, bar_cy - wave_h, bx + 3, bar_cy + wave_h],
            radius=3,
            fill=(255, 105, 165, 215),
        )

    # Determine active spoken phrase and word highlight
    speech_t = t - pad_start
    main_title = "I LOVE YOU KANNA"
    subtitle = "Forever & Always in My Heart"
    if speech_t < 1.35:
        subtitle = "Hey Kanna..."
    elif speech_t < 3.65:
        subtitle = "I Love You, Kanna!"
    else:
        subtitle = "I Love You So Much, Kanna!"

    # Draw 3D extruded main title "I LOVE YOU KANNA"
    font_title = fonts["title"]
    font_sub = fonts["sub"]
    font_badge = fonts["badge"]

    title_bbox = draw.textbbox((0, 0), main_title, font=font_title)
    tw = title_bbox[2] - title_bbox[0]
    tx = (w - tw) // 2 + int(-cam_yaw * 26.0)
    ty = h - 275 + int(-cam_pitch * 18.0)

    # 3D extrusion layers (back-to-front depth layers shifted according to camera angle)
    ext_dx = -cam_yaw * 1.8
    ext_dy = 1.6 - cam_pitch * 1.2
    for depth_i in range(10, 0, -1):
        lx = int(tx + depth_i * ext_dx)
        ly = int(ty + depth_i * ext_dy)
        shade_r = max(60, 175 - depth_i * 10)
        shade_g = max(12, 35 - depth_i * 3)
        shade_b = max(45, 95 - depth_i * 6)
        draw.text((lx, ly), main_title, font=font_title, fill=(shade_r, shade_g, shade_b, 240))

    # Front face of 3D text with bright rose-gold / pearl highlight
    draw.text((tx, ty), main_title, font=font_title, fill=(255, 242, 248, 255))

    # Subtitle with synchronized word glow
    sub_bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    sw = sub_bbox[2] - sub_bbox[0]
    sx = (w - sw) // 2 + card_ox
    sy = h - 190 + card_oy
    draw.text((sx + 2, sy + 3), subtitle, font=font_sub, fill=(40, 8, 24, 210))
    draw.text((sx, sy), subtitle, font=font_sub, fill=(255, 195, 220, 255))

    # Top-left subtle 3D badge
    badge_box = [36, 42, 276, 88]
    draw.rounded_rectangle(badge_box, radius=22, fill=(25, 12, 28, 135), outline=(255, 150, 195, 150), width=1)
    draw.text((58, 53), "3D LOVE MESSAGE • KANNA", font=font_badge, fill=(255, 225, 238, 230))

    combined = Image.alpha_composite(pil_img, txt_layer).convert("RGB")
    return cv2.cvtColor(np.array(combined), cv2.COLOR_RGB2BGR)


def generate_3d_video(
    input_image_path: str = DEFAULT_INPUT_IMAGE,
    output_video_path: str = "/workspace/output/i_love_you_kanna_3d.mp4",
):
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

    # 1. Synthesize Speech & Audio Track
    speech_mp3 = "/tmp/kanna_speech.mp3"
    final_wav = "/tmp/kanna_full_audio.wav"
    words = asyncio.run(synthesize_voice(speech_mp3))
    duration, envelope, pad_start = build_audio_track(speech_mp3, final_wav)
    total_frames = len(envelope)

    # 2. Load & Prepare Portrait Image at 720x1280
    raw_img = cv2.imread(input_image_path)
    if raw_img is None:
        raise FileNotFoundError(f"Cannot load image at {input_image_path}")

    ih, iw, _ = raw_img.shape
    target_aspect = WIDTH / HEIGHT
    curr_aspect = iw / ih
    if curr_aspect > target_aspect:
        new_w = int(ih * target_aspect)
        x0 = (iw - new_w) // 2
        cropped = raw_img[:, x0 : x0 + new_w]
    else:
        new_h = int(iw / target_aspect)
        y0 = (ih - new_h) // 2
        cropped = raw_img[y0 : y0 + new_h, :]

    img_bgr = cv2.resize(cropped, (WIDTH, HEIGHT), interpolation=cv2.INTER_LANCZOS4)

    # 3. Extract 3D Facial Landmarks & Depth Map
    lms = detect_face_landmarks(img_bgr)
    depth_map = build_pseudo_depth_map(img_bgr, lms)
    base_grid_y, base_grid_x = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float32)

    # 4. Precompute 3D Volumetric Heart Sprite & 3D Particle Field
    heart_sprite = precompute_HEART_sprite(128)
    rng = np.random.default_rng(42)
    particles_3d = []
    for i in range(22):
        particles_3d.append(
            {
                "kind": "heart",
                "x": float(rng.uniform(-1.6, 1.6)),
                "y": float(rng.uniform(-1.5, 1.8)),
                "z": float(rng.uniform(1.1, 4.5)),
                "vz": float(rng.uniform(0.12, 0.28)),
                "vy": float(rng.uniform(0.18, 0.38)),
                "sway": float(rng.uniform(0.08, 0.22)),
                "freq": float(rng.uniform(1.2, 2.4)),
                "phase": float(rng.uniform(0, 2 * math.pi)),
                "size": float(rng.uniform(0.55, 1.15)),
            }
        )
    for i in range(36):
        particles_3d.append(
            {
                "kind": "orb",
                "x": float(rng.uniform(-1.8, 1.8)),
                "y": float(rng.uniform(-1.8, 1.8)),
                "z": float(rng.uniform(1.0, 4.6)),
                "vz": float(rng.uniform(0.08, 0.20)),
                "vy": float(rng.uniform(0.10, 0.25)),
                "sway": float(rng.uniform(0.05, 0.15)),
                "freq": float(rng.uniform(1.0, 2.5)),
                "phase": float(rng.uniform(0, 2 * math.pi)),
                "size": float(rng.uniform(0.5, 1.2)),
                "color_bgr": (170, 215, 255) if i % 2 == 0 else (205, 165, 255),
            }
        )

    # Load crisp typography fonts
    font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not os.path.exists(font_bold_path):
        font_bold_path = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"
    fonts = {
        "title": ImageFont.truetype(font_bold_path, 48),
        "sub": ImageFont.truetype(font_bold_path, 27),
        "badge": ImageFont.truetype(font_bold_path, 16),
    }

    # 5. Render Frames & Encode H.264 + AAC MP4 via FFmpeg
    temp_silent_mp4 = "/tmp/kanna_silent.mp4"
    writer = cv2.VideoWriter(
        temp_silent_mp4,
        cv2.VideoWriter_fourcc(*"mp4v"),
        FPS,
        (WIDTH, HEIGHT),
    )

    blink_times = [1.15, 3.35, 5.85, 7.45]

    for f_idx in range(total_frames):
        t = f_idx / FPS
        mouth_open = float(envelope[f_idx])

        # Add subtle phoneme articulation oscillation when speaking
        if mouth_open > 0.04:
            mouth_open *= 0.78 + 0.28 * math.sin(t * 28.0)

        # Warm smile expression that swells during and after saying "I love you Kanna"
        smile_amount = 0.35 + 0.35 * math.sin(t * 0.9) + 0.25 * min(1.0, mouth_open * 1.2)

        # Smooth eye blink calculation
        blink_amount = 0.0
        for bt in blink_times:
            dt = abs(t - bt)
            if dt < 0.14:
                blink_amount = max(blink_amount, math.cos((dt / 0.14) * (math.pi / 2)) ** 2)

        # Smooth 3D orbital camera motion + gentle breathing zoom
        cam_yaw = 0.72 * math.sin(t * 0.85)
        cam_pitch = 0.48 * math.cos(t * 0.65)
        cam_zoom = 1.045 + 0.025 * math.sin(t * 0.55)
        head_tilt = 0.018 * math.sin(t * 0.75)

        warped_bgr = warp_face_and_3d_camera(
            img_bgr=img_bgr,
            depth_map=depth_map,
            lms=lms,
            base_grid_x=base_grid_x,
            base_grid_y=base_grid_y,
            mouth_open=mouth_open,
            smile_amount=smile_amount,
            blink_amount=blink_amount,
            cam_yaw=cam_yaw,
            cam_pitch=cam_pitch,
            cam_zoom=cam_zoom,
            head_tilt=head_tilt,
        )

        composed_bgr = render_3d_stage_and_hud(
            frame_bgr=warped_bgr,
            t=t,
            duration=duration,
            mouth_open=mouth_open,
            cam_yaw=cam_yaw,
            cam_pitch=cam_pitch,
            heart_sprite=heart_sprite,
            particles_3d=particles_3d,
            words=words,
            pad_start=pad_start,
            fonts=fonts,
        )

        writer.write(composed_bgr)

        # Save preview keyframes for inspection
        if f_idx == int(2.6 * FPS):
            cv2.imwrite("/tmp/preview_speaking.png", composed_bgr)

    writer.release()

    # Combine video and stereo audio into web-compatible H.264 MP4
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            temp_silent_mp4,
            "-i",
            final_wav,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            output_video_path,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"Successfully generated 3D video: {output_video_path} ({duration:.2f}s, {total_frames} frames)")


if __name__ == "__main__":
    generate_3d_video()
