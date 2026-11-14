# 🎬 AI Viral Video Clipper (Open-Source)

Ek 100% open-source, self-hosted AI video clipping tool jo kisi bhi long video se **3–4 sabse engaging/viral moments** dhoondhta hai, unhe **speaker face-tracking** ke saath **9:16 vertical format (1080x1920)** mein crop karta hai, aur **word-by-word yellow-highlighted captions** burn karta hai.

## ✨ Features
- **Zero API Cost / 100% Local:** `faster-whisper` + `Ollama` par chalta hai—koi credit limit ya watermark nahi.
- **Viral Hook Detection:** AI transcript padh kar 25–60s ke self-contained viral hooks aur punchlines select karta hai.
- **Smart 9:16 Face-Tracking:** `MediaPipe` speaker ke face ko track karke frame ke center mein rakhta hai.
- **Hormozi-Style Highlighted Captions:** `FFmpeg` + `.ass` subtitles se active word yellow mein highlight hota hai.
- **CLI + Web UI:** Terminal se ya browser (`Gradio` UI) dono se use kar sakte hain.

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
git clone https://github.com/<your-username>/ai-viral-clipper.git
cd ai-viral-clipper
pip install -r requirements.txt
```

---

## 🚀 Usage

### Option A: Browser Web UI (Easy Drag & Drop)
```bash
python app.py
```
Browser mein `http://127.0.0.1:7860` khulega—video upload karein aur 3–4 vertical shorts download karein.

### Option B: Command Line (CLI)
```bash
python clipper.py my_podcast.mp4 --clips 4 --whisper base --llm llama3.1
```
Output `output_shorts/` folder mein `viral_short_1.mp4` se `viral_short_4.mp4` tak save ho jayega.

---

## 📄 License
MIT License — Free for personal and commercial use.
