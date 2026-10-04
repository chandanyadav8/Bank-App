# Voice Mock Test Assistant

Interactive mock test tutor for Java interviews. Ask → Listen → Correct → Next.

Works as a **web app**, **native iOS app**, or **Cursor chat agent**.

## Features

- **Web app** (`voice-mock-test/`) — Chat Mode (iPhone) + Voice Mode (desktop)
- **iOS app** (`ios-mock-test/`) — Native SwiftUI with local speech (speaks questions, listens to answers)
- **Cursor agent** (`.cursor/rules/mock-test-tutor.mdc`) — Run mock tests in Cursor chat

## Topics included

- Java Collection Framework (10 questions, ~3 years experience level)

## Web app

```bash
cd voice-mock-test
python3 -m http.server 8765
```

Open `http://localhost:8765` in Chrome, Edge, or Safari.

### GitHub Pages

Enable **Settings → Pages → GitHub Actions** in this repo. The app deploys to:

`https://<your-username>.github.io/voice-mock-test-assistant/`

## iOS app

Requires a Mac with Xcode 15+ and iPhone with iOS 17+.

See [ios-mock-test/SETUP.txt](ios-mock-test/SETUP.txt) for step-by-step instructions.

## Cursor agent

In any Cursor chat, say:

> Start mock test on Java Collection Framework

Use voice dictation (mic icon) to answer without typing.

## Project structure

```
voice-mock-test-assistant/
├── voice-mock-test/     # Web app (HTML/JS/CSS)
├── ios-mock-test/       # Native iOS SwiftUI app
├── .cursor/rules/       # Cursor mock-test tutor rule
└── .github/workflows/   # GitHub Pages deploy
```

## Push to your own GitHub repo

The Cloud Agent cannot create GitHub repos automatically. Do one of the following:

### Option A — iPhone GitHub app (30 seconds)

1. Open **GitHub** app → tap **+** → **New repository**
2. Name: `voice-mock-test-assistant`
3. Visibility: **Public**
4. Do **not** add README (already included)
5. Tap **Create repository**

Then on a machine with this code, run:

```bash
cd voice-mock-test-assistant
git remote add origin https://github.com/chandanyadav8/voice-mock-test-assistant.git
git push -u origin main
```

### Option B — Mac with GitHub CLI

```bash
cd voice-mock-test-assistant
chmod +x scripts/bootstrap-github.sh
./scripts/bootstrap-github.sh
```

## License

MIT
