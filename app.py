import streamlit as st
import cv2
import numpy as np
import tempfile
import time
import os
from moviepy.editor import VideoFileClip, CompositeVideoClip, concatenate_videoclips

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

# ---------------------- Style Selector ----------------------

def get_transform_function(option):
    return {
        "\ud83c\udf38 Soft Pastel Anime-Like Style": transform_soft_pastel_anime,
        "\ud83c\udfae Cinematic Warm Filter": transform_cinematic_warm,
    }.get(option, lambda x: x)

# ---------------------- Sequential Play Function ----------------------

def sequential_side_by_side_play(file_paths, output_path):
    standard_height = 1080
    standard_width = 640

    clips = [VideoFileClip(p).resize(height=standard_height).resize(width=standard_width) for p in file_paths]
    composite_segments = []

    for i, main_clip in enumerate(clips):
        frozen_clips = []
        for j, clip in enumerate(clips):
            if i == j:
                frozen_clips.append(clip.set_start(0))
            else:
                freeze_frame = clip.to_ImageClip(t=0).set_duration(main_clip.duration)
                frozen_clips.append(freeze_frame)

        positioned_clips = [
            frozen_clips[0].set_position((0, 0)),
            frozen_clips[1].set_position((standard_width, 0)),
            frozen_clips[2].set_position((standard_width * 2, 0))
        ]

        composite = CompositeVideoClip(positioned_clips, size=(standard_width * 3, standard_height)).set_duration(main_clip.duration)
        composite_segments.append(composite)

    final = concatenate_videoclips(composite_segments, method="compose")
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False)

# ---------------------- Streamlit UI ----------------------

st.markdown("---")
st.markdown("## \ud83c\udfae Merge 3 Vertical Shorts into One Landscape Video (16:9) - Sequential Playback")

uploaded_seq_files = st.file_uploader("\ud83d\udcc4 Upload 3 Vertical Videos", type=["mp4"], accept_multiple_files=True, key="seq_merge")

if uploaded_seq_files and len(uploaded_seq_files) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_paths = []
        for i, file in enumerate(uploaded_seq_files):
            file_path = f"{tmpdir}/input_seq_{i}.mp4"
            with open(file_path, "wb") as f:
                f.write(file.read())
            file_paths.append(file_path)

        output_seq_path = f"{tmpdir}/output_sequential.mp4"

        with st.spinner("\u23f3 Processing sequential merge..."):
            try:
                sequential_side_by_side_play(file_paths, output_seq_path)
                st.success("\u2705 Sequentially merged video ready!")

                with open(output_seq_path, "rb") as f:
                    video_bytes = f.read()
                    st.video(video_bytes)
                    st.download_button(
                        label="\ud83d\udcbe Download Sequential Merged Video",
                        data=video_bytes,
                        file_name="sequential_merged_16x9.mp4",
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error(f"\u274c Error: {e}")

elif uploaded_seq_files and len(uploaded_seq_files) != 3:
    st.warning("\u26a0\ufe0f Please upload exactly 3 vertical videos.")
