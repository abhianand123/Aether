# Aether 🦋

<div align="center">

  ![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
  ![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)
  ![Python](https://img.shields.io/badge/Python-3.8%2B-yellow?style=for-the-badge)
  ![Frontend](https://img.shields.io/badge/Frontend-Vanilla%20JS%20%7C%20CSS3-orange?style=for-the-badge)

  <h3 align="center">Quintessence. Pure Air. The Ultimate YouTube Experience.</h3>

  <p align="center">
    A next-generation media downloader featuring a stunning <b>3D Glassmorphism UI</b>, interactive <b>butterfly effects</b>, and immersive <b>neon aesthetics</b>.
  </p>
</div>

---

## 📑 Table of Contents
- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [Project Structure](#-project-structure)

---

## 🌟 Overview

**Aether** transforms the mundane task of downloading media into a visual journey. Built with a robust **Flask** backend and a highly optimized **Vanilla JS** frontend, it delivers performance without compromising on beauty.

The interface is alive—reacting to your mouse movements, tilting in 3D space, and trailing your cursor with a swarm of digital butterflies, all set against a responsive, animated neon mesh gradient.

## ✨ Key Features

### 🎨 Visual & UI
- **3D Glassmorphism Interface**: Premium frosted glass cards with dynamic lighting and depth.
- **Reactive Tilt Effects**: UI elements physically respond to mouse position and mobile gyroscope data.
- **Butterfly Particle System**:
  - **Ghost Cursor Trail**: A magical trail of butterflies follows your every interaction.
  - **Nebula Background**: dynamic floating orbs creating a deep space atmosphere.
- **Neon Mesh Background**: A living, breathing background that shifts through the Aether color palette (`#8b5cf6`, `#06b6d4`, `#ec4899`).

### ⚡ Core Functionality
- **Smart URL Detection**: Automatically distinguishes between Single Videos, Music, Playlists, and Instagram Reels.
- **High-Fidelity Downloads**:
  - **YouTube Video**: Up to **4K Resolution**.
  - **YouTube/Instagram Audio**: **320kbps MP3** conversion with metadata integration.
  - **Instagram Reels**: Download High Quality Video or Audio Only.
- **Playlist Architecture**: One-click bulk downloads, automatically zipped for convenience.
- **Real-Time Telemetry**: Live Websocket-style updates for download speed, ETA, and progress.
- **Resilient Bypass Engine**: Advanced cookie management to access age-gated and premium content.

> [!WARNING]
> **Important**: Do not refresh the page while a download is in progress! Doing so will interrupt the connection to the server and the download will fail. The server will automatically clean up temporary files, but your download will be lost.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **Backend** | Python & Flask | Robust server-side logic and request handling. |
| **Engine** | yt-dlp | The gold standard for media extraction. |
| **Frontend** | HTML5 & CSS3 | Semantic structure with advanced animations. |
| **Scripting** | Vanilla JavaScript | Lightweight, dependency-free interactions. |
| **Effects** | Vanilla-Tilt.js | 3D parallax hover effects. |

---

## 🚀 Getting Started

### Prerequisites

*   **Python 3.8+** represents the core runtime.
*   **FFmpeg** is critical for audio conversion and video merging.
    *   [Download FFmpeg](https://ffmpeg.org/download.html)
    *   *Note: Ensure FFmpeg is added to your system's PATH.*

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/abhianand123/aether-downloader.git
    cd aether-downloader
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Launch Aether**
    ```bash
    python app.py
    ```
    *Terminal Tip: If `python` fails, try `py` or `python3`.*

4.  **Experience**
    Open your browser and traverse to:
    `http://localhost:5000`

---

## ⚙️ Configuration

Aether works out of the box, but you can customize it:

- **Download Location**:
  By default, all media is saved to the `downloads/` folder in the project root.
  To change this, modify `app.py`:
  ```python
  DOWNLOAD_FOLDER = 'path/to/your/folder'
  ```

- **Port**:
  Runs on port `5000` by default. Change the `app.run` call in `app.py` to use a different port.

---

## 🔧 Troubleshooting

| Issue | Possible Solution |
|-------|-------------------|
| **Audio Conversion Failed** | FFmpeg is likely missing from your PATH. Install it and restart your terminal. |
| **Download Stuck at 0%** | Check your internet connection or try updating `yt-dlp` (`pip install -U yt-dlp`). |
| **403 Forbidden Error** | The video might be region-locked or premium. Aether tries to bypass this, but valid cookies may be needed. |
| **"Spoke" Artifact** | Fixed in v2.1. Ensure your templates don't contain the `.spoke` class. |

---

## 🗺️ Roadmap

- [x] **v1.0**: Core downloader, basic UI.
- [x] **v2.0**: Aether Rebranding, 3D UI, Butterfly System.
- [x] **v2.1**: Nebula Background, Performance Optimizations.
- [ ] **v2.2**: Dark/Light mode toggle.
- [ ] **v3.0**: User Accounts & Cloud Sync.
- [ ] **v3.1**: Spotify & SoundCloud support.

---

## 🤝 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📂 Project Structure

```text
Aether/
├── app.py              # Application Entry Point & Route Handlers
├── downloads/          # Media Destination (Auto-generated)
├── static/
│   ├── style.css       # The Design System (Glassmorphism & Gradients)
│   └── script.js       # The Brains (Butterfly System & API Logic)
├── templates/
│   └── index.html      # The Canavs (HTML Structure)
└── requirements.txt    # Dependency Manifest
```

---

<div align="center">
  
  **Created with ❤️ by Abhi Anand**
  
  [Instagram](https://instagram.com/chessbasebgs) • [GitHub](https://github.com/abhianand123)

  *© 2025 Aether Project. All Rights Reserved.*
</div>
