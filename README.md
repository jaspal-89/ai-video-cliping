# 🎬 AI Viral Video Clipper (Open-Source)

Ek 100% open-source, self-hosted AI video clipping tool jo kisi bhi long video se **3–4 sabse engaging/viral moments** dhoondhta hai, unhe **face-aware cropping** ke saath **9:16 vertical format (1080x1920)** mein crop karta hai, aur **word-by-word yellow-highlighted captions** burn karta hai.

## ✨ Features
- **Zero API Cost / 100% Local:** `faster-whisper` + `Ollama` par chalta hai—koi credit limit ya watermark nahi.
- **Viral Hook Detection:** AI transcript padh kar 25–60s ke self-contained viral hooks aur punchlines select karta hai.
- **Smart 9:16 Face-Aware Crop:** `MediaPipe` sampled frames se face position estimate karta hai aur uske aas-paas vertical crop set karta hai. (Continuous frame-by-frame tracking nahi.)
- **Hormozi-Style Highlighted Captions:** `FFmpeg` + `.ass` subtitles se active word yellow mein highlight hota hai.
- **CLI + Web UI:** Terminal se ya browser (`Gradio` UI) dono se use kar sakte hain.
- **Video Input:** Local video upload ya supported YouTube video URL (`yt-dlp`) se import.

---

## 🛠️ Installation (GitHub Clone ke baad)

### 1. Prerequisites
- **Python 3.10+**
- **FFmpeg** (System PATH mein installed hona chahiye)
  - Windows: `winget install Gyan.FFmpeg`
  - Mac: `brew install ffmpeg`
  - Ubuntu/Linux: `sudo apt install ffmpeg`
- **Ollama** ([ollama.com](https://ollama.com) se install karein) aur model pull karein:
  ```bash
  ollama pull llama3.1
  ```

### 2. Project Setup
```bash
git clone https://github.com/jaspal-89/ai-video-cliping.git
cd ai-video-cliping
pip install -r requirements.txt
```

---

## ⚠️ Current limitations
- The temporary share URL is public to anyone who has it. Set `APP_USERNAME` and `APP_PASSWORD` before launch to enable basic login, and do not share the URL publicly. Set `GRADIO_SHARE=false` to disable the tunnel.
- YouTube downloads depend on YouTube availability, video permissions, and `yt-dlp` compatibility. Only download videos you own or are authorized to use.
- The app can create a temporary public Gradio share URL when launched (`GRADIO_SHARE=true`, the default). The URL works only while the app is running on your computer; this is a tunnel, not permanent cloud hosting.
- Ollama and the selected model must be installed and running on the same machine as the app.
- Processing speed depends on your CPU, available RAM, video length, and Whisper model size.

## 🚀 Usage

### Quick start on macOS
Install Homebrew first from https://brew.sh, then download/clone this repository and run:

```bash
bash start_mac.sh
```

The script installs/checks FFmpeg, Ollama and Python 3.11, installs the Python requirements, downloads the local `llama3.1` model, and launches the app. On first run, downloads can take time. Keep the Terminal window open while generating clips and while using the temporary public URL.

### Option A: Browser Web UI (Upload or YouTube URL)
```bash
python app.py
```
Terminal mein Gradio ka `https://....gradio.live` share URL dikhega. Us URL ko browser mein kholkar video upload karein **ya YouTube URL paste karein**, phir vertical shorts generate karein. Local access `http://127.0.0.1:7860` par bhi rahega.

### Option B: Command Line (CLI)
```bash
python clipper.py my_podcast.mp4 --clips 4 --whisper base --llm llama3.1
```
Output `output_shorts/` folder mein `viral_short_1.mp4` se `viral_short_4.mp4` tak save ho jayega.

---

## 📄 License
MIT License — Free for personal and commercial use.

## 🐳 Run with Docker (App + Local Ollama)

Prerequisites: Docker Desktop / Docker Engine with Docker Compose.

```bash
git clone https://github.com/jaspal-89/ai-video-cliping.git
cd ai-video-cliping
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1
docker compose up --build -d app
```

Open `http://localhost:7860` in your browser. The first run may take time because the Ollama model and Whisper model need to download. Video processing needs sufficient RAM/CPU; Docker does not make hosting or compute free.

To stop the app: `docker compose down`.
