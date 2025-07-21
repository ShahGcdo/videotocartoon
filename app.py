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

# === Cleanup ===
def clean_output_dir(directory, max_age_seconds=3600):
    now = time.time()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) and now - os.path.getmtime(file_path) > max_age_seconds:
            os.remove(file_path)

# === Style Filters ===
def pastel_filter(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    hsv[..., 1] = hsv[..., 1] * 0.5
    pastel = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    return pastel

def warm_filter(frame):
    lut = np.interp(np.arange(256), [0, 64, 128, 192, 255], [0, 80, 160, 220, 255]).astype("uint8")
    frame = cv2.LUT(frame, lut)
    return frame

def get_transform_function(style_name):
    if "Pastel" in style_name:
        return pastel_filter
    elif "Warm" in style_name:
        return warm_filter
    return None

# === Rain Effects ===
def add_rain(frame, intensity=0.3):
    rain_layer = np.random.rand(*frame.shape[:2]) < intensity
    frame[rain_layer] = [180, 180, 255]
    return frame

def get_rain_function(option):
    if "Extra" in option:
        return lambda f: add_rain(f, 0.1)
    elif "Ultra" in option:
        return lambda f: add_rain(f, 0.05)
    elif "Light" in option:
        return lambda f: add_rain(f, 0.2)
    return None

# === Watermark ===
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

# === Process Full Video ===
def process_video(input_path, output_path, transform_func=None, rain_func=None, max_duration=None):
    clip = VideoFileClip(input_path)
    if max_duration:
        clip = clip.subclip(0, max_duration)

    fps = clip.fps
    processed_frames = []

    for frame in clip.iter_frames():
        frame = transform_func(frame) if transform_func else frame
        frame = rain_func(frame) if rain_func else frame
        processed_frames.append(frame)

    temp_dir = tempfile.mkdtemp()
    frame_pattern = os.path.join(temp_dir, "frame_%05d.png")
    for i, f in enumerate(processed_frames):
        cv2.imwrite(os.path.join(temp_dir, f"frame_{i:05d}.png"), f[:, :, ::-1])

    raw_output = output_path.replace(".mp4", "_raw.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", frame_pattern,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-threads", "4", raw_output
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    apply_watermark(raw_output, output_path)
    shutil.rmtree(temp_dir)
    clip.close()

# === Streamlit App ===
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

st.markdown("✅ Full video will be processed.")
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
            process_video(temp_input_path, output_path, style_fn, rain_fn)
            st.success("✅ Done! Here's your preview:")
            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button("⬇️ Download Processed Video", f, file_name=output_filename)
        except Exception as e:
            st.error(f"❌ Error: {e}")

        os.remove(temp_input_path)

st.markdown("---")
st.caption("⚡ Built with Streamlit, MoviePy, FFmpeg, OpenCV. Auto-cleans temp files hourly.")
