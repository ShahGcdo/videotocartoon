# -*- coding: utf-8 -*-
import streamlit as st
import cv2
import numpy as np
import tempfile
import time
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip

st.set_page_config(page_title="Anime + Cinematic Video Filters")
st.title("Anime & Cinematic Style Video Transformation")

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
        "Soft Pastel Anime-Like Style": transform_soft_pastel_anime,
        "Cinematic Warm Filter": transform_cinematic_warm,
    }.get(option, lambda x: x)

# ---------------------- UI ----------------------

st.markdown("## Apply Style Filter to a Single Video")

uploaded_file = st.file_uploader("Upload a Video", type=["mp4", "mov", "avi"], key="single")
style_option = st.selectbox("Choose a Style", (
    "Soft Pastel Anime-Like Style",
    "Cinematic Warm Filter"
), key="style_single")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_input:
        tmp_input.write(uploaded_file.read())
        input_path = tmp_input.name

    try:
        transform_func = get_transform_function(style_option)
        start_time = time.time()

        with st.spinner("Applying style transformation..."):
            clip = VideoFileClip(input_path)
            transformed_clip = clip.fl_image(transform_func)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_output:
                output_path = tmp_output.name
                transformed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        end_time = time.time()
        st.info(f"Completed in {end_time - start_time:.2f} seconds")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original Video")
            st.video(input_path)
        with col2:
            st.subheader("Styled Video")
            with open(output_path, "rb") as f:
                video_bytes = f.read()
                st.video(video_bytes)
                st.download_button("Download Styled Video", video_bytes, file_name="styled_video.mp4")

    except Exception as e:
        st.error(f"Error: {e}")

# ---------------------- Sequential Playback Merge ----------------------

st.markdown("## Merge 3 Vertical Shorts into One Landscape Video (16:9) - Sequential Playback")

uploaded_seq = st.file_uploader("Upload 3 Vertical Videos", type=["mp4"], accept_multiple_files=True, key="seq")
style_seq = st.selectbox("Apply Style to Sequential Video", (
    "Soft Pastel Anime-Like Style",
    "Cinematic Warm Filter"
), key="style_seq")

if uploaded_seq and len(uploaded_seq) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for i, file in enumerate(uploaded_seq):
            path = os.path.join(tmpdir, f"seq_{i}.mp4")
            with open(path, "wb") as f:
                f.write(file.read())
            paths.append(path)

        transform_func = get_transform_function(style_seq)

        clips = [VideoFileClip(p).resize(height=1080) for p in paths]
        for i in range(len(clips)):
            clips[i] = clips[i].fl_image(transform_func)

        width = 1920 // 3
        new_clips = []

        for idx, clip in enumerate(clips):
            canvases = []
            for j in range(3):
                if j == idx:
                    v = clip.resize(width=width)
                else:
                    v = clips[j].resize(width=width).fx(lambda c: c.set_opacity(0.2))
                v = v.set_position((width * j, 0))
                canvases.append(v)

            new_clips.append(CompositeVideoClip(canvases, size=(1920, 1080)).set_duration(clip.duration))

        final = concatenate_videoclips(new_clips, method="compose")

        final_path = os.path.join(tmpdir, "sequential_final.mp4")
        final.write_videofile(final_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        st.video(final_path)
        with open(final_path, "rb") as f:
            st.download_button("Download Sequential Merged Video", f.read(), file_name="sequential_merged_16x9.mp4")

elif uploaded_seq and len(uploaded_seq) != 3:
    st.warning("Please upload exactly 3 vertical videos.")
