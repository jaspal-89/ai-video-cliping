import os
import json
import argparse
import subprocess
import cv2
import mediapipe as mp
from faster_whisper import WhisperModel
import ollama


def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        raise RuntimeError("FFmpeg system par install nahi hai. Pehle FFmpeg install karein.")


def transcribe_video(video_path: str, model_size: str = "base"):
    print(f"[1/4] Audio transcribe ho raha hai (Whisper '{model_size}')...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(video_path, word_timestamps=True)

    transcript_data = []
    for seg in segments:
        words = []
        if seg.words:
            words = [{"word": w.word.strip(), "start": w.start, "end": w.end} for w in seg.words]
        transcript_data.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
            "words": words
        })
    return transcript_data


def find_viral_clips(transcript_data: list, num_clips: int = 4, llm_model: str = "llama3.1"):
    print(f"[2/4] AI se top {num_clips} viral moments dhoondhe ja rahe hain...")
    formatted_transcript = "\n".join(
        [f"[{s['start']:.2f} - {s['end']:.2f}] {s['text']}" for s in transcript_data]
    )

    prompt = f"""
    You are an expert viral short-form video editor for YouTube Shorts, Instagram Reels, and TikTok.
    Analyze the timestamped transcript below and extract the top {num_clips} most engaging, high-retention moments.

    Rules:
    - Each clip MUST be between 25 and 60 seconds long.
    - Start each clip with a strong hook and end on a complete thought/punchline.
    - Clips must not overlap.
    - Return ONLY valid JSON with a top-level key "clips" containing a list of objects.
    - Each object must have exact keys: "title", "start" (float seconds), "end" (float seconds), "hook_reason".

    Transcript:
    {formatted_transcript}
    """

    response = ollama.chat(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}],
        format="json"
    )
    try:
        data = json.loads(response["message"]["content"])
    except (TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Ollama returned invalid JSON for clip selection.") from exc

    if isinstance(data, dict):
        clips = data.get("clips", [])
    elif isinstance(data, list):
        clips = data
    else:
        clips = []

    # Reject malformed, out-of-range, too-short, and overlapping suggestions.
    video_end = max((float(item.get("end", 0)) for item in transcript_data), default=0.0)
    valid_clips = []
    for item in clips:
        if not isinstance(item, dict):
            continue
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if start < 0 or end <= start or end > video_end + 1:
            continue
        if end - start < 5 or end - start > 60:
            continue
        item["start"], item["end"] = start, end
        valid_clips.append(item)

    valid_clips.sort(key=lambda item: item["start"])
    non_overlapping = []
    for item in valid_clips:
        if non_overlapping and item["start"] < non_overlapping[-1]["end"]:
            continue
        non_overlapping.append(item)
        if len(non_overlapping) >= num_clips:
            break
    return non_overlapping


def detect_speaker_x_center(video_path: str, start_sec: float, end_sec: float) -> float:
    mp_face = mp.solutions.face_detection.FaceDetection(min_detection_confidence=0.5)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_sec * fps))

    x_positions = []
    total_frames = int((end_sec - start_sec) * fps)
    step = max(1, int(fps))  # Sample 1 frame per second

    for _ in range(0, total_frames, step):
        ret, frame = cap.read()
        if not ret:
            break
        for _ in range(step - 1):
            cap.grab()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_face.process(rgb)
        if results.detections:
            bbox = results.detections[0].location_data.relative_bounding_box
            x_positions.append(bbox.xmin + bbox.width / 2.0)

    cap.release()
    return sum(x_positions) / len(x_positions) if x_positions else 0.5


def format_ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs == 100:
        secs += 1
        cs = 0
    return f"{hrs}:{mins:02d}:{secs:02d}.{cs:02d}"


def generate_ass_subtitles(transcript_data: list, clip_start: float, clip_end: float, ass_path: str, words_per_line: int = 3):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,78,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,60,60,340,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    clip_words = []
    for seg in transcript_data:
        for w in seg.get("words", []):
            if clip_start <= w["start"] <= clip_end:
                clip_words.append(w)

    events = []
    for i in range(0, len(clip_words), words_per_line):
        chunk = clip_words[i:i + words_per_line]
        if not chunk:
            continue
        chunk_start = chunk[0]["start"] - clip_start
        chunk_end = chunk[-1]["end"] - clip_start

        # Highlight active word in yellow (&H0000FFFF in BGR)
        for active_idx, active_word in enumerate(chunk):
            w_start = active_word["start"] - clip_start
            w_end = active_word["end"] - clip_start
            if w_end <= w_start:
                w_end = w_start + 0.12

            styled_tokens = []
            for j, token in enumerate(chunk):
                clean_txt = token["word"].upper()
                if j == active_idx:
                    styled_tokens.append(f"{{\\c&H0000FFFF&}}{clean_txt}{{\\c&H00FFFFFF&}}")
                else:
                    styled_tokens.append(clean_txt)

            line_text = " ".join(styled_tokens)
            events.append(
                f"Dialogue: 0,{format_ass_time(w_start)},{format_ass_time(w_end)},Default,,0,0,0,,{line_text}"
            )

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")


def render_vertical_short(video_path: str, clip: dict, transcript_data: list, output_path: str, temp_dir: str, idx: int):
    start = float(clip["start"])
    end = float(clip["end"])
    duration = end - start

    cap = cv2.VideoCapture(video_path)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    if orig_w <= 0 or orig_h <= 0:
        raise RuntimeError("Could not read the input video's dimensions.")

    x_center_ratio = detect_speaker_x_center(video_path, start, end)
    target_ratio = 9 / 16
    source_ratio = orig_w / orig_h
    if source_ratio > target_ratio:
        crop_h = orig_h
        crop_w = int(crop_h * target_ratio)
        x_center_px = int(x_center_ratio * orig_w)
        x1 = max(0, min(orig_w - crop_w, x_center_px - crop_w // 2))
        y1 = 0
    else:
        crop_w = orig_w
        crop_h = int(crop_w / target_ratio)
        x1 = 0
        y1 = max(0, (orig_h - crop_h) // 2)

    ass_path = os.path.join(temp_dir, f"captions_{idx}.ass")
    generate_ass_subtitles(transcript_data, start, end, ass_path)

    # Escape path for FFmpeg subtitles filter
    escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")

    vf_filter = f"crop={crop_w}:{crop_h}:{x1}:{y1},scale=1080:1920,ass='{escaped_ass}'"

    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}",
        "-i", video_path,
        "-t", f"{duration:.3f}",
        "-vf", vf_filter,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        output_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed to render clip {idx}: {result.stderr[-1500:]}")


def main():
    parser = argparse.ArgumentParser(description="Open-Source AI Viral Video Clipper (9:16 + Dynamic Captions)")
    parser.add_argument("video", help="Input video file path (e.g., input.mp4)")
    parser.add_argument("--clips", type=int, default=4, help="Number of viral shorts to generate (default: 4)")
    parser.add_argument("--whisper", default="base", help="Whisper model size: tiny, base, small, medium (default: base)")
    parser.add_argument("--llm", default="llama3.1", help="Local Ollama model name (default: llama3.1)")
    parser.add_argument("--out", default="output_shorts", help="Output folder (default: output_shorts)")
    args = parser.parse_args()

    check_ffmpeg()
    os.makedirs(args.out, exist_ok=True)
    temp_dir = os.path.join(args.out, ".temp")
    os.makedirs(temp_dir, exist_ok=True)

    transcript = transcribe_video(args.video, model_size=args.whisper)
    clips = find_viral_clips(transcript, num_clips=args.clips, llm_model=args.llm)

    if not clips:
        print("Koi viral clip detect nahi ho paaya. Transcript ya LLM model check karein.")
        return

    print(f"[3/4] {len(clips)} viral clips render kiye ja rahe hain...")
    metadata_out = []
    for idx, clip in enumerate(clips, start=1):
        out_file = os.path.join(args.out, f"viral_short_{idx}.mp4")
        print(f"   -> Clip {idx}: '{clip.get('title', 'Untitled')}' ({clip['start']}s - {clip['end']}s)")
        render_vertical_short(args.video, clip, transcript, out_file, temp_dir, idx)
        metadata_out.append({**clip, "file": out_file})

    with open(os.path.join(args.out, "clips_summary.json"), "w", encoding="utf-8") as f:
        json.dump(metadata_out, f, indent=2, ensure_ascii=False)

    print(f"[4/4] Done! Saare 9:16 shorts '{args.out}/' folder mein save ho gaye hain.")


if __name__ == "__main__":
    main()
