import streamlit as st
import cv2
import numpy as np
import tempfile
import time
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips

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
        "🎮 Cinematic Warm Filter": transform_cinematic_warm,
    }.get(option, lambda x: x)

# ---------------------- Single Video Filter ----------------------
st.markdown("## 🎨 Apply Style Filter to a Single Video")
uploaded_file = st.file_uploader("📄 Upload a Video", type=["mp4", "mov", "avi"], key="single")
style_option = st.selectbox("🎨 Choose a Style", list(get_transform_function.__annotations__.keys()), key="style_single")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_input:
        tmp_input.write(uploaded_file.read())
        input_path = tmp_input.name

    try:
        transform_func = get_transform_function(style_option)
        start_time = time.time()
        with st.spinner("✨ Applying style transformation... Please wait."):
            clip = VideoFileClip(input_path)
            transformed_clip = clip.fl_image(transform_func)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_output:
                output_path = tmp_output.name
                transformed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        elapsed = time.time() - start_time
        st.success(f"✅ Completed in {elapsed:.2f} seconds")
        st.video(output_path)
        with open(output_path, "rb") as f:
            st.download_button("💾 Download Styled Video", f.read(), "styled_video.mp4")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# ---------------------- Merge 3 Videos Side-by-Side ----------------------
st.markdown("---")
st.markdown("## 🎮 Merge 3 Vertical Shorts into One Landscape Video (16:9) + Apply Style")
uploaded_files = st.file_uploader("📄 Upload 3 Vertical Videos", type=["mp4"], accept_multiple_files=True, key="merge")
style_merge = st.selectbox("🎨 Apply Style to Merged Video", list(get_transform_function.__annotations__.keys()), key="style_merge")

if uploaded_files and len(uploaded_files) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for i, f in enumerate(uploaded_files):
            p = os.path.join(tmpdir, f"input{i}.mp4")
            with open(p, "wb") as fp:
                fp.write(f.read())
            paths.append(p)

        merged_path = os.path.join(tmpdir, "merged_output.mp4")
        watermark_text = "@USMIKASHMIRI"

        command = f"""
        ffmpeg -y -i {paths[0]} -i {paths[1]} -i {paths[2]} \
        -filter_complex \
        \"[0:v]scale=640:1080:force_original_aspect_ratio=decrease,pad=640:1080:(ow-iw)/2:(oh-ih)/2[v0]; \
           [1:v]scale=640:1080:force_original_aspect_ratio=decrease,pad=640:1080:(ow-iw)/2:(oh-ih)/2[v1]; \
           [2:v]scale=640:1080:force_original_aspect_ratio=decrease,pad=640:1080:(ow-iw)/2:(oh-ih)/2[v2]; \
           [v0][v1][v2]hstack=inputs=3[stacked]; \
           [stacked]drawtext=text='{watermark_text}':x='w-mod(t*120\,w+text_w)':y='h-100':fontsize=40:fontcolor=white@0.4:shadowcolor=black:shadowx=2:shadowy=2[outv]\" \
        -map \"[outv]\" -c:v libx264 -preset fast -crf 22 -pix_fmt yuv420p {merged_path}
        """

        if os.system(command) == 0:
            st.success("✅ Merged video created!")
            st.video(merged_path)
            with open(merged_path, "rb") as f:
                st.download_button("💾 Download Merged Video", f.read(), "merged_styled.mp4")
        else:
            st.error("❌ FFmpeg merge failed.")

elif uploaded_files:
    st.warning("⚠️ Please upload exactly 3 vertical videos.")

# ---------------------- Play Sequentially Left to Right ----------------------
st.markdown("---")
st.markdown("## ▶️ Merge 3 Vertical Shorts Playing Sequentially (Left to Right)")
uploaded_seq = st.file_uploader("📤 Upload 3 Vertical Videos for Sequential Play", type=["mp4"], accept_multiple_files=True, key="merge_seq")

if uploaded_seq and len(uploaded_seq) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        clips = []
        for i, f in enumerate(uploaded_seq):
            path = os.path.join(tmpdir, f"clip{i}.mp4")
            with open(path, "wb") as fp:
                fp.write(f.read())
            clips.append(VideoFileClip(path).resize(height=1080).fx(lambda c: c.set_position((640 * i, 0))))

        final_clip = concatenate_videoclips(clips, method="compose")
        output_seq = os.path.join(tmpdir, "sequential_output.mp4")
        final_clip.write_videofile(output_seq, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        st.success("✅ Sequential video created!")
        st.video(output_seq)
        with open(output_seq, "rb") as f:
            st.download_button("💾 Download Sequential Video", f.read(), "sequential_video.mp4")
elif uploaded_seq:
    st.warning("⚠️ Please upload exactly 3 vertical videos.")
