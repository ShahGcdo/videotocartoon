import streamlit as st
import os
import tempfile
import subprocess
import time
from moviepy.editor import VideoFileClip
from PIL import Image
import numpy as np
import cv2
import shutil
import random

st.set_page_config(page_title="🎨 AI Video Effects App", layout="centered")
st.title("🎨 AI Video Effects App")

def clean_output_dir(path="processed_videos", max_age_seconds=3600):
    now = time.time()
    if not os.path.exists(path):
        os.makedirs(path)
    for f in os.listdir(path):
        fp = os.path.join(path, f)
        if os.path.isfile(fp) and now - os.path.getmtime(fp) > max_age_seconds:
            os.remove(fp)

def get_transform_function(style_name):
    if style_name == "🌸 Soft Pastel Anime-Like Style":
        def pastel_style(frame):
            frame = frame.astype(np.float32)
            frame[:, :, 0] = np.clip(frame[:, :, 0] * 1.08 + 20, 0, 255)
            frame[:, :, 1] = np.clip(frame[:, :, 1] * 1.06 + 15, 0, 255)
            frame[:, :, 2] = np.clip(frame[:, :, 2] * 1.15 + 25, 0, 255)
            blurred = cv2.GaussianBlur(frame, (7, 7), 0)
            tint = np.array([10, -5, 15], dtype=np.float32)
            result = np.clip(blurred + tint, 0, 255).astype(np.uint8)
            return result
        return pastel_style
    elif style_name == "🎮 Cinematic Warm Filter":
        def warm_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.15 + 15, 0, 255)
            g = np.clip(g * 1.08 + 8, 0, 255)
            b = np.clip(b * 0.95, 0, 255)
            frame = np.stack([r, g, b], axis=2).astype(np.float32)
            rows, cols = frame.shape[:2]
            Y, X = np.ogrid[:rows, :cols]
            vignette = 1 - ((X - cols/2)**2 + (Y - rows/2)**2) / (1.5 * (cols/2) * (rows/2))
            vignette = np.clip(vignette, 0.3, 1)[..., np.newaxis]
            grain = np.random.normal(0, 3, frame.shape).astype(np.float32)
            return np.clip(frame * vignette + grain, 0, 255).astype(np.uint8)
        return warm_style
    return lambda f: f

def add_rain_effect(frame, density=0.002):
    frame = frame.copy()
    h, w, _ = frame.shape
    num_drops = int(h * w * density)
    for _ in range(num_drops):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 20)
        length = random.randint(10, 20)
        cv2.line(frame, (x, y), (x, y + length), (200, 200, 255), 1)
    return frame

def get_rain_function(option):
    if option == "☂️ Light Rain (Default)":
        return lambda f: add_rain_effect(f, density=0.002)
    elif option == "🌦️ Extra Light Rain":
        return lambda f: add_rain_effect(f, density=0.0008)
    elif option == "🌤️ Ultra Light Rain":
        return lambda f: add_rain_effect(f, density=0.0004)
    else:
        return lambda f: f
def apply_watermark(input_path, output_path, watermark_text="My Watermark"):
    watermark_filter = f"drawtext=text='{watermark_text}':x=10:y=H-th-10:fontsize=24:fontcolor=white:shadowcolor=black:shadowx=2:shadowy=2"
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", watermark_filter,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-threads", "4",
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def process_video(input_path, output_path, transform_func=None, rain_func=None, max_duration=20):
    clip = VideoFileClip(input_path).subclip(0, max_duration)
    fps = clip.fps
    processed_frames = []

    for frame in clip.iter_frames():
        frame = transform_func(frame) if transform_func else frame
        frame = rain_func(frame) if rain_func else frame
        processed_frames.append(frame)

    temp_dir = tempfile.mkdtemp()
    frame_files = []
    for i, f in enumerate(processed_frames):
        frame_path = os.path.join(temp_dir, f"frame_{i:05d}.png")
        cv2.imwrite(frame_path, f[:, :, ::-1])
        frame_files.append(frame_path)

    out_path_raw = output_path.replace(".mp4", "_raw.mp4")
    frame_pattern = os.path.join(temp_dir, "frame_%05d.png")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", frame_pattern,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-threads", "4", out_path_raw
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    apply_watermark(out_path_raw, output_path)
    shutil.rmtree(temp_dir)
    clip.close()

# === Main App Logic ===
output_dir = "processed_videos"
os.makedirs(output_dir, exist_ok=True)
clean_output_dir(output_dir, 3600)

st.markdown("### Upload a video to apply styles & effects")
uploaded_file = st.file_uploader("📹 Upload a video", type=["mp4", "mov", "avi", "mkv"])

style_option = st.selectbox("🎨 Choose a video style:", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎮 Cinematic Warm Filter"
])

rain_option = st.selectbox("🌧️ Add rain overlay:", [
    "None",
    "☂️ Light Rain (Default)",
    "🌦️ Extra Light Rain",
    "🌤️ Ultra Light Rain"
])

duration = st.slider("⏱️ Trim Video Duration (sec)", 5, 30, 20)
generate = st.button("✨ Generate Stylized Video")
if uploaded_file and generate:
    with st.spinner("⏳ Processing... Please wait"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
            temp_input.write(uploaded_file.read())
            temp_input_path = temp_input.name

        output_filename = f"stylized_{int(time.time())}.mp4"
        output_path = os.path.join(output_dir, output_filename)

        style_fn = get_transform_function(style_option)
        rain_fn = get_rain_function(rain_option)

        try:
            process_video(temp_input_path, output_path, style_fn, rain_fn, max_duration=duration)
            st.success("✅ Done! Here's your preview:")
            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button("⬇️ Download Processed Video", f, file_name=output_filename)
        except Exception as e:
            st.error(f"❌ Error: {e}")

        os.remove(temp_input_path)

st.markdown("---")
st.caption("⚡ Built with Streamlit, MoviePy, FFmpeg, OpenCV. Auto-cleans temp files hourly.")
