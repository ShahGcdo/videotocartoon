import streamlit as st
import cv2
import numpy as np
import tempfile
import time
from moviepy.editor import VideoFileClip

st.set_page_config(page_title="Anime Style Video Filters", page_icon="✨")
st.title("🎨 Anime & Cartoon Style Video Transformation")

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

def transform_pencil_sketch(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    inv = 255 - gray
    blur = cv2.GaussianBlur(inv, (21, 21), 0)
    sketch = cv2.divide(gray, 255 - blur, scale=256)
    return cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)

def transform_pop_art(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)
    s *= 2.0
    v *= 1.2
    poster = cv2.merge([h, np.clip(s, 0, 255), np.clip(v, 0, 255)])
    poster = cv2.cvtColor(poster.astype(np.uint8), cv2.COLOR_HSV2BGR)
    poster = cv2.medianBlur(poster, 5)
    return poster

def transform_vhs_anime(frame):
    frame = cv2.resize(frame, None, fx=0.98, fy=0.98)
    b, g, r = cv2.split(frame)
    b = np.roll(b, 1, axis=1)
    r = np.roll(r, -1, axis=1)
    glitch = cv2.merge([b, g, r])

    blur = cv2.bilateralFilter(glitch, 9, 90, 90)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)
    s *= 0.7
    v *= 1.2
    pastel = cv2.merge([h, np.clip(s, 0, 255), np.clip(v, 0, 255)])
    return cv2.cvtColor(pastel.astype(np.uint8), cv2.COLOR_HSV2BGR)

def transform_toon_shader(frame):
    Z = frame.reshape((-1, 3)).astype(np.float32)
    _, label, center = cv2.kmeans(Z, 8, None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0), 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    quantized = center[label.flatten()].reshape(frame.shape)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.adaptiveThreshold(cv2.medianBlur(gray, 7), 255,
                                  cv2.ADAPTIVE_THRESH_MEAN_C,
                                  cv2.THRESH_BINARY, 9, 2)
    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    return cv2.bitwise_and(quantized, edges_colored)

def transform_edge_glow_cartoon(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    blur = cv2.bilateralFilter(frame, 9, 150, 150)
    glow = cv2.addWeighted(blur, 0.8, frame, 0.2, 0)

    return cv2.subtract(glow, edges_colored)

# ---------------------- Style Selector ----------------------

def get_transform_function(option):
    return {
        "🌸 Soft Pastel Anime-Like Style": transform_soft_pastel_anime,
        "🎞️ Cinematic Warm Filter": transform_cinematic_warm,
        "✏️ Pencil Sketch (Storyboard Style)": transform_pencil_sketch,
        "🧃 Pop Art Style (High Saturation)": transform_pop_art,
        "🌀 VHS Retro Anime": transform_vhs_anime,
        "🖊️ Toon Shader (Cel-Shaded Look)": transform_toon_shader,
        "🌠 Glow Outline Cartoon": transform_edge_glow_cartoon
    }.get(option, lambda x: x)

# ---------------------- UI ----------------------

st.markdown("Upload a video and choose your desired anime/cartoon-style transformation.")

uploaded_file = st.file_uploader("📤 Upload Video", type=["mp4", "mov", "avi"])

style_option = st.selectbox("🎨 Choose a Style", (
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter",
    "✏️ Pencil Sketch (Storyboard Style)",
    "🧃 Pop Art Style (High Saturation)",
    "🌀 VHS Retro Anime",
    "🖊️ Toon Shader (Cel-Shaded Look)",
    "🌠 Glow Outline Cartoon"
))

# ---------------------- Video Processing ----------------------

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

        end_time = time.time()
        elapsed = end_time - start_time
        st.info(f"✅ Completed in {elapsed:.2f} seconds")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎥 Original")
            st.video(input_path)
        with col2:
            st.subheader("🧑‍🎨 Transformed")
            with open(output_path, "rb") as f:
                video_bytes = f.read()
                st.video(video_bytes)
                st.download_button(
                    label="💾 Download Transformed Video",
                    data=video_bytes,
                    file_name="styled_video.mp4",
                    mime="video/mp4"
                )

    except Exception as e:
        st.error(f"❌ Error: {e}")
