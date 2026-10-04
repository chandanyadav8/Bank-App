import AVFoundation
import Speech
import Foundation

@MainActor
final class SpeechManager: NSObject, ObservableObject {
    @Published var isSpeaking = false
    @Published var isListening = false
    @Published var transcript = ""
    @Published var permissionGranted = false
    @Published var errorMessage: String?

    private let synthesizer = AVSpeechSynthesizer()
    private let speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()

    override init() {
        super.init()
        synthesizer.delegate = self
    }

    func requestPermissions() async {
        let micStatus = await AVAudioApplication.requestRecordPermission()
        let speechStatus = await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status == .authorized)
            }
        }
        permissionGranted = micStatus && speechStatus
        if !permissionGranted {
            errorMessage = "Microphone and speech recognition permissions are required."
        }
    }

    func speak(_ text: String) async {
        guard !text.isEmpty else { return }

        stopListening()
        isSpeaking = true

        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate * 0.9
        utterance.pitchMultiplier = 1.0

        synthesizer.speak(utterance)

        await withCheckedContinuation { continuation in
            self.speakContinuation = continuation
        }
    }

    private var speakContinuation: CheckedContinuation<Void, Never>?

    func listen() async -> String? {
        guard permissionGranted else { return nil }
        guard let speechRecognizer, speechRecognizer.isAvailable else {
            errorMessage = "Speech recognition is not available."
            return nil
        }

        stopListening()
        transcript = ""
        isListening = true
        errorMessage = nil

        let audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession.setCategory(.playAndRecord, mode: .measurement, options: [.duckOthers, .defaultToSpeaker])
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            errorMessage = "Audio session error: \(error.localizedDescription)"
            isListening = false
            return nil
        }

        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest else { return nil }
        recognitionRequest.shouldReportPartialResults = true

        if #available(iOS 13, *) {
            recognitionRequest.requiresOnDeviceRecognition = speechRecognizer.supportsOnDeviceRecognition
        }

        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)

        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            recognitionRequest.append(buffer)
        }

        audioEngine.prepare()

        do {
            try audioEngine.start()
        } catch {
            errorMessage = "Could not start audio engine."
            isListening = false
            return nil
        }

        return await withCheckedContinuation { continuation in
            self.listenContinuation = continuation
            self.recognitionTask = speechRecognizer.recognitionTask(with: recognitionRequest) { [weak self] result, error in
                guard let self else { return }

                if let result {
                    Task { @MainActor in
                        self.transcript = result.bestTranscription.formattedString
                    }
                    if result.isFinal {
                        self.finishListening(with: result.bestTranscription.formattedString)
                    }
                }

                if error != nil {
                    Task { @MainActor in
                        self.finishListening(with: self.transcript.isEmpty ? nil : self.transcript)
                    }
                }
            }
        }
    }

    func stopListening() {
        if audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()
        recognitionRequest = nil
        recognitionTask = nil
        isListening = false
    }

    private var listenContinuation: CheckedContinuation<String?, Never>?

    private func finishListening(with text: String?) {
        stopListening()
        listenContinuation?.resume(returning: text)
        listenContinuation = nil
    }

    func stopSpeaking() {
        synthesizer.stopSpeaking(at: .immediate)
        isSpeaking = false
        speakContinuation?.resume()
        speakContinuation = nil
    }
}

extension SpeechManager: AVSpeechSynthesizerDelegate {
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor in
            self.isSpeaking = false
            self.speakContinuation?.resume()
            self.speakContinuation = nil
        }
    }
}
