# 🎮 Kiro Arcade

> 🇪🇸 [Versión en español](README.md)

A browser-based arcade built for the Kiro AI workshop. Players choose from 4 mini-games using hand gestures via webcam, powered by MediaPipe hand detection and AWS Bedrock AI.

## Games

- **Flappy Kiro** ☝️ — Flappy Bird clone with the Kiro logo as the player sprite
- **Fruit Ninja** ✊ — Slice fruit before it falls off screen
- **Rock Paper Scissors** 👌 — Play against Kiro AI using hand gestures
- **Ghost Dodge** 🖐️ — Dodge incoming ghosts as long as you can

## Features

- Hand gesture game selection (no keyboard needed)
- Per-game leaderboards stored as JSON files on the server
- AI-generated comments and images via AWS Bedrock (Nova Lite + Nova Canvas)
- Text-to-speech via Amazon Polly
- "Aprende Kiro" modal with intro, guided demo, and learn-by-playing guide
- Bilingual UI (Spanish / English)

## Requirements

- Python 3.8+
- Firefox (recommended browser — required for webcam/MediaPipe compatibility)
- Port 8000 available on your machine
- AWS credentials configured with access to Bedrock and Polly (profile: `kiro-arcade`)

## Getting started

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the server:

```bash
python server.py
```

3. Open [http://localhost:8000](http://localhost:8000) in Firefox.

## Project structure

```
/
├── index.html        # Main arcade menu
├── server.py         # Static file server + AI API endpoints
├── src/              # Game files (flappy, fruit-ninja, rps, ghost-dodge)
├── images/           # Sprites and assets
├── videos/           # Demo and tutorial videos
├── docs/             # Playbook and project docs
└── rankings/         # Per-game leaderboard JSON files
```

## Disclaimer

This project is an independent demo created for educational and workshop purposes. It is not affiliated with, endorsed by, or representative of Amazon Web Services (AWS) or any of its products. Any use of AWS services (Amazon Bedrock, Amazon Polly, etc.) is solely the responsibility of the user. AWS is not responsible for the content, functionality, or any outcomes resulting from the use of this project.
