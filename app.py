import glob
import os
import tempfile
from urllib.parse import urlparse

import gradio as gr
import yt_dlp
from clipper import check_ffmpeg, transcribe_video, find_viral_clips, render_vertical_short


def download_youtube_video(url, download_dir):
    parsed = urlparse((url or '').strip())
    host = (parsed.hostname or '').lower()
    allowed = {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com', 'youtu.be', 'www.youtube-nocookie.com', 'youtube-nocookie.com'}
    if parsed.scheme not in {'http', 'https'} or host not in allowed:
        raise ValueError('Please enter a valid YouTube video URL.')
    options = {
        'format': 'bestvideo*+bestaudio/best',
        'outtmpl': os.path.join(download_dir, 'source.%(ext)s'),
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(options) as downloader:
        downloader.extract_info(url.strip(), download=True)
    candidates = [p for p in glob.glob(os.path.join(download_dir, 'source.*')) if not p.endswith(('.part', '.ytdl'))]
    if not candidates:
        raise RuntimeError('YouTube download completed but no video file was found. Check FFmpeg installation and the video URL.')
    return max(candidates, key=os.path.getsize)


def process_video_ui(video_file, youtube_url, num_clips, whisper_model, llm_model):
    if bool(video_file) == bool((youtube_url or '').strip()):
        return [], 'Please provide either a video upload or a YouTube URL, not both.'
    try:
        check_ffmpeg()
        out_dir = tempfile.mkdtemp(prefix='viral_shorts_')
        temp_dir = os.path.join(out_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        source_path = video_file if video_file else download_youtube_video(youtube_url, temp_dir)
        transcript = transcribe_video(source_path, model_size=whisper_model)
        clips = find_viral_clips(transcript, num_clips=int(num_clips), llm_model=llm_model)
        if not clips:
            return [], 'No valid clips were found. Try another video or a different Ollama model.'
        generated_files = []
        summary_lines = []
        for idx, clip in enumerate(clips, start=1):
            out_path = os.path.join(out_dir, f'viral_short_{idx}.mp4')
            render_vertical_short(source_path, clip, transcript, out_path, temp_dir, idx)
            generated_files.append(out_path)
            summary_lines.append(
                f"**Short #{idx}: {clip.get('title', 'Clip')}** ({clip['start']:.1f}s - {clip['end']:.1f}s)\n"
                f"- Hook reason: {clip.get('hook_reason', 'High engagement moment')}"
            )
        return generated_files, '\n\n'.join(summary_lines)
    except Exception as exc:
        return [], f'Processing failed: {type(exc).__name__}: {exc}'


with gr.Blocks(title='AI Video Clipper') as demo:
    gr.Markdown('# AI Video Clipper')
    gr.Markdown('Upload a video or paste a YouTube video URL. Generate vertical 9:16 clips with word-highlighted captions.')
    with gr.Row():
        with gr.Column():
            video_input = gr.Video(label='Upload a video file')
            youtube_input = gr.Textbox(label='Or paste a YouTube URL', placeholder='https://www.youtube.com/watch?v=...')
            num_clips = gr.Slider(1, 6, value=4, step=1, label='Number of Shorts')
            whisper_model = gr.Dropdown(['tiny', 'base', 'small', 'medium'], value='base', label='Whisper model')
            llm_model = gr.Textbox(value='llama3.1', label='Ollama model name')
            run_btn = gr.Button('Generate Shorts', variant='primary')
        with gr.Column():
            output_gallery = gr.Gallery(label='Generated Shorts', columns=2)
            summary_md = gr.Markdown(label='Clip details')
    run_btn.click(
        fn=process_video_ui,
        inputs=[video_input, youtube_input, num_clips, whisper_model, llm_model],
        outputs=[output_gallery, summary_md],
    )

if __name__ == "__main__":
    # Gradio's free share tunnel gives a temporary public URL while this process runs.
    # Set GRADIO_SHARE=false to disable it. Optional basic auth protects the shared URL.
    share_enabled = os.getenv("GRADIO_SHARE", "true").strip().lower() in {"1", "true", "yes"}
    username = os.getenv("APP_USERNAME")
    password = os.getenv("APP_PASSWORD")
    auth = (username, password) if username and password else None
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=share_enabled,
        auth=auth,
    )
