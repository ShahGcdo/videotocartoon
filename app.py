import streamlit as st
import cv2
import numpy as np
import tempfile
import time
import os
from moviepy.editor import VideoFileClip, clips_array, concatenate_videoclips

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
        "🌸 Soft Pastel Anime-Like Style": transform_soft_pastel_anime,
        "🎞️ Cinematic Warm Filter": transform_cinematic_warm,
    }.get(option, lambda x: x)

# ---------------------- UI ----------------------

st.markdown("## 🎨 Apply Style Filter to a Single Video")

uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4", "mov", "avi"], key="single")

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
            transformed_clip = clip.fl_image(transform_func)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_output:
                output_path = tmp_output.name
                transformed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎥 Original Video")
            st.video(input_path)
        with col2:
            st.subheader("🧑‍🎨 Styled Video")
            with open(output_path, "rb") as f:
                video_bytes = f.read()
                st.video(video_bytes)
                st.download_button("💾 Download Styled Video", video_bytes, "styled_video.mp4", mime="video/mp4")

    except Exception as e:
        st.error(f"❌ Error: {e}")

# ---------------------- Merge Feature (Simultaneous Side-by-Side) ----------------------

st.markdown("---")
st.markdown("## 🎬 Merge 3 Vertical Shorts into One Landscape Video (16:9) + Apply Style")

uploaded_files = st.file_uploader("📤 Upload 3 Vertical Videos", type=["mp4"], accept_multiple_files=True, key="merge")

style_merge = st.selectbox("🎨 Apply Style to Merged Video", (
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
), key="style_merge")

if uploaded_files and len(uploaded_files) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_paths = []
        for i, file in enumerate(uploaded_files):
            file_path = os.path.join(tmpdir, f"input{i}.mp4")
            with open(file_path, "wb") as f:
                f.write(file.read())
            file_paths.append(file_path)

        merged_path = os.path.join(tmpdir, "merged_output.mp4")

        command = f"""
        ffmpeg -i {file_paths[0]} -i {file_paths[1]} -i {file_paths[2]} \
        -filter_complex "[0:v]scale=640:1080[v0];[1:v]scale=640:1080[v1];[2:v]scale=640:1080[v2];[v0][v1][v2]hstack=inputs=3,drawtext=text='@USMIKASHMIRI':x='w-(mod(t\,8)*w/8)':y=h-th-50:fontsize=36:fontcolor=white@0.5:shadowcolor=black:shadowx=2:shadowy=2" \
        -c:v libx264 -preset fast -crf 22 -y {merged_path}
        """

        result = os.system(command)

        if result == 0:
            st.success("✅ Merged video created!")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🎥 Merged Video (Before Style)")
                st.video(merged_path)

            try:
                transform_func = get_transform_function(style_merge)
                clip = VideoFileClip(merged_path)
                styled_clip = clip.fl_image(transform_func)

                styled_path = os.path.join(tmpdir, "styled_output.mp4")
                styled_clip.write_videofile(styled_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

                with col2:
                    st.subheader("🧑‍🎨 Styled Merged Video")
                    with open(styled_path, "rb") as f:
                        styled_bytes = f.read()
                        st.video(styled_bytes)
                        st.download_button("💾 Download Styled Merged Video", styled_bytes, "styled_merged_16x9.mp4", mime="video/mp4")
            except Exception as e:
                st.error(f"❌ Error styling merged video: {e}")
        else:
            st.error("❌ FFmpeg merge failed.")
elif uploaded_files and len(uploaded_files) != 3:
    st.warning("⚠️ Please upload exactly 3 vertical videos.")

# ---------------------- NEW: Sequential Playback in Side-by-Side Layout ----------------------

st.markdown("---")
st.markdown("## 🎬 Merge 3 Vertical Shorts Side-by-Side But Play One by One (Left to Right)")

seq_files = st.file_uploader("📤 Upload 3 Vertical Videos (Sequential Play)", type=["mp4"], accept_multiple_files=True, key="seq")

if seq_files and len(seq_files) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        clips = []
        for i, file in enumerate(seq_files):
            path = os.path.join(tmpdir, f"seq_input{i}.mp4")
            with open(path, "wb") as f:
                f.write(file.read())
            clip = VideoFileClip(path).resize(height=1080).resize(width=640)
            clips.append(clip)

        empty = VideoFileClip(paths[0]).fx(lambda c: c.set_opacity(0))

        layout = [
            clips_array([[clips[0], empty, empty]]),
            clips_array([[empty, clips[1], empty]]),
            clips_array([[empty, empty, clips[2]]])
        ]

        final_seq = concatenate_videoclips(layout)
        output_seq = os.path.join(tmpdir, "sequential_play.mp4")
        final_seq.write_videofile(output_seq, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        st.video(output_seq)
        with open(output_seq, "rb") as f:
            st.download_button("⬇️ Download Sequential Merged Video", f.read(), file_name="sequential_merged.mp4", mime="video/mp4")

elif seq_files and len(seq_files) != 3:
    st.warning("⚠️ Please upload exactly 3 vertical videos for sequential play.")
