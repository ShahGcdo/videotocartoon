import streamlit as st
import cv2
import numpy as np
import tempfile
import time
import os
from moviepy.editor import (
    VideoFileClip,
    CompositeVideoClip,
    ColorClip,
    concatenate_videoclips,
    ImageClip
)

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

# ---------------------- Feature 3: Sequential Side-by-Side ----------------------
st.markdown("---")
st.header("▶️ Play 3 Videos One by One in Side-by-Side Frame (16:9)")

uploaded_seq = st.file_uploader("📤 Upload 3 Vertical Videos (Sequential Style)", type=["mp4"], accept_multiple_files=True, key="sequential")

if uploaded_seq and len(uploaded_seq) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for i, f in enumerate(uploaded_seq):
            p = os.path.join(tmpdir, f"seq{i}.mp4")
            with open(p, "wb") as out:
                out.write(f.read())
            paths.append(p)

        try:
            # Load all 3 videos
            clips = [VideoFileClip(p).resize(height=1080) for p in paths]
            widths = [clip.w for clip in clips]
            target_w = 640
            resized_clips = [clip.resize(width=target_w) for clip in clips]

            # Create static images for side positions
            frozen_images = [clip.get_frame(0) for clip in resized_clips]
            image_clips = [ImageClip(img).set_duration(1).resize(width=target_w) for img in frozen_images]

            final_clips = []
            for i in range(3):
                comp = CompositeVideoClip([
                    image_clips[0].set_position((0, 0)) if i != 0 else resized_clips[0].set_position((0, 0)),
                    image_clips[1].set_position((640, 0)) if i != 1 else resized_clips[1].set_position((640, 0)),
                    image_clips[2].set_position((1280, 0)) if i != 2 else resized_clips[2].set_position((1280, 0))
                ], size=(1920, 1080)).set_duration(resized_clips[i].duration)
                final_clips.append(comp)

            final_video = concatenate_videoclips(final_clips, method="compose")

            out_path = os.path.join(tmpdir, "sequential_output_visible.mp4")
            final_video.write_videofile(out_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

            st.success("✅ Sequential video created with side-by-side paused clips!")
            st.video(out_path)
            with open(out_path, "rb") as f:
                st.download_button("💾 Download Sequential Video", data=f.read(), file_name="sequential_visible_16x9.mp4", mime="video/mp4")

        except Exception as e:
            st.error(f"❌ Error processing sequential video: {e}")
elif uploaded_seq and len(uploaded_seq) != 3:
    st.warning("⚠️ Please upload exactly 3 videos.")
