import os
import tempfile
import gradio as gr
from clipper import check_ffmpeg, transcribe_video, find_viral_clips, render_vertical_short


def process_video_ui(video_file, num_clips, whisper_model, llm_model):
    if not video_file:
        return [], "Please upload a video first."

    check_ffmpeg()
    out_dir = tempfile.mkdtemp(prefix="viral_shorts_")
    temp_dir = os.path.join(out_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    transcript = transcribe_video(video_file, model_size=whisper_model)
    clips = find_viral_clips(transcript, num_clips=int(num_clips), llm_model=llm_model)

    generated_files = []
    summary_lines = []
    for idx, clip in enumerate(clips, start=1):
        out_path = os.path.join(out_dir, f"viral_short_{idx}.mp4")
        render_vertical_short(video_file, clip, transcript, out_path, temp_dir, idx)
        generated_files.append(out_path)
        summary_lines.append(
            f"**Short #{idx}: {clip.get('title', 'Clip')}** (`{clip['start']}s` - `{clip['end']}s`)\n"
            f"- *Hook Reason:* {clip.get('hook_reason', 'High engagement moment')}"
        )

    return generated_files, "\n\n".join(summary_lines)


with gr.Blocks(title="AI Viral Shorts Clipper") as demo:
    gr.Markdown("# 🎬 Open-Source AI Viral Clipper (9:16 + Dynamic Captions)")
    gr.Markdown("Long video upload karein — AI best 3-4 viral moments nikaal kar 9:16 vertical shorts with highlighted captions bana dega.")

    with gr.Row():
        with gr.Column():
            video_input = gr.Video(label="Upload Long Video (.mp4)")
            num_clips = gr.Slider(1, 6, value=4, step=1, label="Number of Viral Shorts")
            whisper_model = gr.Dropdown(["tiny", "base", "small", "medium"], value="base", label="Whisper Model")
            llm_model = gr.Textbox(value="llama3.1", label="Ollama Local LLM Model")
            run_btn = gr.Button("Generate Viral Shorts 🚀", variant="primary")

        with gr.Column():
            output_gallery = gr.Gallery(label="Generated 9:16 Viral Shorts", columns=2)
            summary_md = gr.Markdown(label="Detected Hooks & Timestamps")

    run_btn.click(
        fn=process_video_ui,
        inputs=[video_input, num_clips, whisper_model, llm_model],
        outputs=[output_gallery, summary_md]
    )

if __name__ == "__main__":
    demo.launch()
