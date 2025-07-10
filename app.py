import streamlit as st
import cv2
import numpy as np
import tempfile
import time
import os
from moviepy.editor import VideoFileClip, clips_array, CompositeVideoClip, ColorClip

st.set_page_config(page_title="Anime + Cinematic Video Filters", page_icon="🎨")
st.title("🎨 Anime & Cinematic Style Video Transformation")

# ---------------------- Filter Functions ----------------------

def transform_soft_pastel_anime(frame):
    blur = cv2.bilateralFilter(frame, 9, 75, 75)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)
    s *= 0.6
    v *= 1.2
    pastel = cv2.merge([h, np.clip(s, 0, 255), np.clip(v, 0, 255)])
    pastel = cv2.cvtColor(pastel.astype(np.uint8), cv2.COLOR_HSV2BGR)
    return pastel

def transform_cinematic_warm(frame):
    lut = np.array([min(255, int(i * 1.1 + 10)) for i in range(256)]).astype("uint8")
    warm = cv2.LUT(frame, lut)
    hsv = cv2.cvtColor(warm, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)
    h = (h + 10) % 180
    s *= 1.1
    v *= 1.05
    final = cv2.merge([h, np.clip(s, 0, 255), np.clip(v, 0, 255)])
    return cv2.cvtColor(final.astype(np.uint8), cv2.COLOR_HSV2BGR)

def get_transform_function(option):
    return {
        "🌸 Soft Pastel Anime-Like Style": transform_soft_pastel_anime,
        "🎞️ Cinematic Warm Filter": transform_cinematic_warm,
    }.get(option, lambda x: x)

# ---------------------- UI ----------------------

st.markdown("## 🎨 Apply Style Filter to a Single Video")

uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4"], key="single")
style_option = st.selectbox("🎨 Choose a Style", (
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
), key="style_single")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_input:
        tmp_input.write(uploaded_file.read())
        input_path = tmp_input.name

    try:
        transform_func = get_transform_function(style_option)
        with st.spinner("✨ Applying style transformation..."):
            clip = VideoFileClip(input_path)
            styled_clip = clip.fl_image(transform_func)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_output:
                styled_clip.write_videofile(tmp_output.name, codec="libx264", audio_codec="aac", verbose=False, logger=None)
                output_path = tmp_output.name

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎥 Original")
            st.video(input_path)
        with col2:
            st.subheader("🎨 Styled")
            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button("💾 Download Styled Video", f, "styled_video.mp4", "video/mp4")

    except Exception as e:
        st.error(f"❌ Error: {e}")

# ---------------------- MERGE SIDE BY SIDE + STYLE ----------------------

st.markdown("---")
st.markdown("## 🎬 Merge 3 Vertical Shorts into One Landscape Video (Side by Side + Style)")

uploaded_files = st.file_uploader("📤 Upload 3 Vertical Videos", type=["mp4"], accept_multiple_files=True, key="merge")
style_merge = st.selectbox("🎨 Apply Style to Merged Video", (
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
), key="style_merge")

if uploaded_files and len(uploaded_files) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_paths = []
        for i, file in enumerate(uploaded_files):
            path = os.path.join(tmpdir, f"vid{i}.mp4")
            with open(path, "wb") as f:
                f.write(file.read())
            file_paths.append(path)

        # Load and resize
        clips = [VideoFileClip(p).resize(height=1080).crop(x_center=540, width=640) for p in file_paths]
        merged_clip = clips_array([[clips[0], clips[1], clips[2]]])

        merged_path = os.path.join(tmpdir, "merged.mp4")
        merged_clip.write_videofile(merged_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎥 Merged Video")
            st.video(merged_path)

        try:
            transform_func = get_transform_function(style_merge)
            styled_clip = VideoFileClip(merged_path).fl_image(transform_func)

            styled_path = os.path.join(tmpdir, "styled_merged.mp4")
            styled_clip.write_videofile(styled_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

            with col2:
                st.subheader("🎨 Styled Merged")
                st.video(styled_path)
                with open(styled_path, "rb") as f:
                    st.download_button("💾 Download Styled", f, "styled_merged.mp4", "video/mp4")
        except Exception as e:
            st.error(f"❌ Styling failed: {e}")
elif uploaded_files:
    st.warning("⚠️ Please upload exactly 3 vertical videos.")

# ---------------------- NEW FEATURE: One-by-One Side-by-Side ----------------------

st.markdown("---")
st.markdown("## 🆕 Play One-by-One in 16:9 Layout (Side by Side, Sequentially)")

uploaded_files_seq = st.file_uploader("📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sequential")

if uploaded_files_seq and len(uploaded_files_seq) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for i, file in enumerate(uploaded_files_seq):
            path = os.path.join(tmpdir, f"seq{i}.mp4")
            with open(path, "wb") as f:
                f.write(file.read())
            paths.append(path)

        clips = [VideoFileClip(p).resize(height=1080).crop(x_center=540, width=640) for p in paths]
        durations = [clip.duration for clip in clips]

        w, h = 1920, 1080
        black = ColorClip(size=(640, 1080), color=(0, 0, 0)).set_duration(max(durations))

        v1 = clips_array([[clips[0], black, black]])
        v2 = clips_array([[black, clips[1], black]])
        v3 = clips_array([[black, black, clips[2]]])

        final = concatenate_videoclips([v1, v2, v3], method="compose")

        final_path = os.path.join(tmpdir, "sequential_merged.mp4")
        final.write_videofile(final_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        st.subheader("🎬 One-by-One Playback in 16:9")
        st.video(final_path)
        with open(final_path, "rb") as f:
            st.download_button("💾 Download One-by-One Merged", f, "one_by_one_merged.mp4", "video/mp4")
