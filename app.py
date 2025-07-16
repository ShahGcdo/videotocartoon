import streamlit as st
import cv2
import numpy as np
import tempfile
from moviepy.editor import VideoFileClip
from helpers.style_transfer import get_transform_function
from utils.watermark import add_watermark_to_clip

def add_rain_effect(frame):
    h, w = frame.shape[:2]
    rain_layer = np.zeros((h, w, 3), dtype=np.uint8)

    for _ in range(300):  # Number of raindrops
        x = np.random.randint(0, w)
        y = np.random.randint(0, h)
        length = np.random.randint(10, 20)
        color = (200, 200, 255)  # Light blue-gray color for rain
        thickness = 1
        cv2.line(rain_layer, (x, y), (x, y + length), color, thickness)

    alpha = 0.15  # Transparency of rain
    blended = cv2.addWeighted(frame, 1.0, rain_layer, alpha, 0)
    return blended

def feature_1_cartoon_style_transfer():
    st.title("🎨 Feature 1: Cartoon Style Transfer")
    
    style = st.selectbox("Choose a Cartoon Style", ["Hayao", "Hosoda", "Paprika", "Shinkai"])
    add_watermark = st.checkbox("Add Watermark", value=True)
    add_rain = st.checkbox("🌧️ Add Light Rain Effect", value=False, key="add_rain")
    
    uploaded_file = st.file_uploader("Upload a Video", type=["mp4", "mov", "avi"])
    
    generate = st.button("Generate Cartoon Video")
    
    if uploaded_file and generate:
        with st.spinner("Processing..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
                temp_input.write(uploaded_file.read())
                temp_input_path = temp_input.name

            clip = VideoFileClip(temp_input_path)
            transform_func = get_transform_function(style)

            if add_rain:
                def combined_transform(frame):
                    styled = transform_func(frame)
                    return add_rain_effect(styled)
                styled_clip = clip.fl_image(combined_transform)
            else:
                styled_clip = clip.fl_image(transform_func)

            if add_watermark:
                styled_clip = add_watermark_to_clip(styled_clip)

            output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            styled_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        st.video(output_path)
        st.success("Cartoon style video generated successfully!")




# ========== FEATURE 2 (Side-by-Side: Raw Unstyled & Final Styled+Watermarked) ==========
st.markdown("---")
st.header("📱 Side-by-Side (1280x720, 3 Videos) with Watermark")

# Initialize session state
if "sbs_raw_output" not in st.session_state:
    st.session_state["sbs_raw_output"] = None
if "sbs_final_output" not in st.session_state:
    st.session_state["sbs_final_output"] = None

uploaded_files = st.file_uploader(
    "📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sidebyside"
)

style_sbs = st.selectbox(
    "🎨 Style for Final Video",
    ["None", "🌸 Soft Pastel Anime-Like Style", "🎞️ Cinematic Warm Filter"],
    key="style_sbs"
)

if uploaded_files and len(uploaded_files) == 3:
    if st.button("🚀 Generate Side-by-Side Video"):
        with st.spinner("Processing..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                paths = []
                for i, file in enumerate(uploaded_files):
                    path = os.path.join(tmpdir, f"video{i}.mp4")
                    with open(path, "wb") as f:
                        f.write(file.read())
                    paths.append(path)

                target_size = (426, 720)
                transform_func = get_transform_function(style_sbs)

                # Load raw unstyled clips
                raw_clips = []
                styled_clips = []
                min_duration = None

                for path in paths:
                    clip_raw = VideoFileClip(path).resize(target_size)
                    clip_styled = clip_raw.fl_image(transform_func)

                    duration = clip_raw.duration
                    if min_duration is None or duration < min_duration:
                        min_duration = duration

                    raw_clips.append(clip_raw)
                    styled_clips.append(clip_styled)

                # Trim both sets to shortest clip duration
                raw_clips = [c.subclip(0, min_duration) for c in raw_clips]
                styled_clips = [c.subclip(0, min_duration) for c in styled_clips]

                # Create raw (unstyled) side-by-side
                raw_combined = CompositeVideoClip([
                    raw_clips[0].set_position((0, 0)),
                    raw_clips[1].set_position((426, 0)),
                    raw_clips[2].set_position((852, 0))
                ], size=(1280, 720)).set_duration(min_duration)

                raw_output = os.path.join(tmpdir, "sbs_raw.mp4")
                raw_combined.write_videofile(raw_output, codec="libx264", audio_codec="aac")

                # Create styled + watermark version
                styled_combined = CompositeVideoClip([
                    styled_clips[0].set_position((0, 0)),
                    styled_clips[1].set_position((426, 0)),
                    styled_clips[2].set_position((852, 0))
                ], size=(1280, 720)).set_duration(min_duration)

                styled_temp = os.path.join(tmpdir, "styled_temp.mp4")
                styled_combined.write_videofile(styled_temp, codec="libx264", audio_codec="aac")

                final_output = os.path.join(tmpdir, "sbs_final.mp4")
                apply_watermark(styled_temp, final_output)

                # Save to session state
                with open(raw_output, "rb") as f:
                    st.session_state["sbs_raw_output"] = f.read()
                with open(final_output, "rb") as f:
                    st.session_state["sbs_final_output"] = f.read()

            st.success("✅ Raw and Final videos generated successfully!")

# Show raw and final output
if st.session_state["sbs_raw_output"]:
    st.subheader("🎬 Raw Video (No Style, No Watermark)")
    st.video(st.session_state["sbs_raw_output"])
    st.download_button("⬇️ Download Raw", st.session_state["sbs_raw_output"], file_name="raw_unstyled.mp4")

if st.session_state["sbs_final_output"]:
    st.subheader("🌟 Final Video (Styled + Watermark)")
    st.video(st.session_state["sbs_final_output"])
    st.download_button("⬇️ Download Final", st.session_state["sbs_final_output"], file_name="styled_watermarked.mp4")

# ========== FEATURE 3 (Sequential Playback with 1-Second Triple Intro) ==========
st.markdown("---")
st.header("🕒 Play 3 Videos Sequentially with 1s Intro & Watermark")

# Initialize session state
st.session_state.setdefault("seq_raw_output", None)
st.session_state.setdefault("seq_final_output", None)

uploaded_seq = st.file_uploader(
    "📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sequential"
)

style_seq = st.selectbox(
    "🎨 Style for Final Video",
    ["None", "🌸 Soft Pastel Anime-Like Style", "🎞️ Cinematic Warm Filter"],
    key="style_seq"
)

if uploaded_seq and len(uploaded_seq) == 3:
    if st.button("🚀 Generate Sequential Video"):
        with st.spinner("Processing..."):
            import os, tempfile
            from moviepy.editor import VideoFileClip, CompositeVideoClip, concatenate_videoclips

            with tempfile.TemporaryDirectory() as tmpdir:
                # Save uploaded videos
                paths = []
                for i, file in enumerate(uploaded_seq):
                    file_path = os.path.join(tmpdir, f"seq{i}.mp4")
                    with open(file_path, "wb") as out:
                        out.write(file.read())
                    paths.append(file_path)

                # Prepare transform and video clips
                transform = get_transform_function(style_seq)
                width, height = int(1280 / 3), 720

                video_raw = [VideoFileClip(p).resize((width, height)) for p in paths]
                video_styled = [VideoFileClip(p).fl_image(transform).resize((width, height)) for p in paths]

                raw_clips, styled_clips = [], []

                # ========== SEGMENT 0: Intro - 1 second, all 3 play normally ==========
                intro_duration = 1
                raw_intro = CompositeVideoClip([
                    video_raw[0].subclip(0, intro_duration).set_position((0, 0)),
                    video_raw[1].subclip(0, intro_duration).set_position((width, 0)),
                    video_raw[2].subclip(0, intro_duration).set_position((2 * width, 0))
                ], size=(1280, height))

                styled_intro = CompositeVideoClip([
                    video_styled[0].subclip(0, intro_duration).set_position((0, 0)),
                    video_styled[1].subclip(0, intro_duration).set_position((width, 0)),
                    video_styled[2].subclip(0, intro_duration).set_position((2 * width, 0))
                ], size=(1280, height))

                raw_clips.append(raw_intro)
                styled_clips.append(styled_intro)

                # ========== SEGMENTS 1-3: One plays, others frozen & faded ==========
                for i in range(3):
                    # Full duration of the current main video
                    dur = video_raw[i].duration

                    # Raw parts
                    raw_parts = []
                    styled_parts = []

                    for j in range(3):
                        if j == i:
                            # Play full
                            raw_clip = video_raw[j]
                            styled_clip = video_styled[j]
                        else:
                            # Frozen + faded image
                            raw_clip = video_raw[j].to_ImageClip(t=1).set_duration(dur).set_opacity(0.4)
                            styled_clip = video_styled[j].to_ImageClip(t=1).set_duration(dur).set_opacity(0.4)

                        raw_parts.append(raw_clip.set_position((j * width, 0)))
                        styled_parts.append(styled_clip.set_position((j * width, 0)))

                    raw_clips.append(CompositeVideoClip(raw_parts, size=(1280, height)).set_duration(dur))
                    styled_clips.append(CompositeVideoClip(styled_parts, size=(1280, height)).set_duration(dur))

                # ========== CONCATENATE ==========
                raw_sequence = concatenate_videoclips(raw_clips)
                styled_sequence = concatenate_videoclips(styled_clips)

                # ========== EXPORT RAW ==========
                raw_output_path = os.path.join(tmpdir, "seq_raw.mp4")
                raw_sequence.write_videofile(raw_output_path, codec="libx264", audio_codec="aac")

                # ========== EXPORT STYLED + WATERMARK ==========
                styled_temp_path = os.path.join(tmpdir, "seq_styled_temp.mp4")
                styled_sequence.write_videofile(styled_temp_path, codec="libx264", audio_codec="aac")

                final_output_path = os.path.join(tmpdir, "seq_final.mp4")
                apply_watermark(styled_temp_path, final_output_path)

                # ========== SAVE TO SESSION ==========
                with open(raw_output_path, "rb") as f:
                    st.session_state["seq_raw_output"] = f.read()
                with open(final_output_path, "rb") as f:
                    st.session_state["seq_final_output"] = f.read()

        st.success("✅ Sequential videos generated with 1-second intro + full playback + watermark!")

# ========== DISPLAY ==========
if st.session_state["seq_raw_output"]:
    st.subheader("🎬 Raw Sequential Video (No Style, No Watermark)")
    st.video(st.session_state["seq_raw_output"])
    st.download_button("⬇️ Download Raw", st.session_state["seq_raw_output"], file_name="sequential_raw.mp4")

if st.session_state["seq_final_output"]:
    st.subheader("🌟 Final Sequential Video (Styled + Watermark)")
    st.video(st.session_state["seq_final_output"])
    st.download_button("⬇️ Download Final", st.session_state["seq_final_output"], file_name="sequential_styled.mp4")


from io import BytesIO  # ✅ Add this import at the top of your file

# ========== FEATURE 4 ==========
st.markdown("---")
st.header("🖼️ Combine Thumbnails from 3 Videos (1280x720)")

uploaded_thumb_files = st.file_uploader(
    "📤 Upload 3 Videos", 
    type=["mp4"], 
    accept_multiple_files=True, 
    key="thumbnails"
)

if uploaded_thumb_files and len(uploaded_thumb_files) == 3:
    st.subheader("⏱️ Select timestamps (in seconds) for each video")
    timestamps = [
        st.number_input(
            f"Timestamp for video {i+1}",
            min_value=0.0,
            value=1.0,
            step=0.5,
            key=f"ts_{i}"
        )
        for i in range(3)
    ]

    if st.button("🧩 Generate Combined Thumbnail"):
        with tempfile.TemporaryDirectory() as tmpdir:
            images = []

            for idx, file in enumerate(uploaded_thumb_files):
                path = os.path.join(tmpdir, f"thumb{idx}.mp4")
                with open(path, "wb") as f:
                    f.write(file.read())

                clip = VideoFileClip(path)
                frame = clip.get_frame(timestamps[idx])
                img = Image.fromarray(frame).resize((426, 720))
                images.append(img)
                clip.close()

            combined = Image.new("RGB", (1280, 720))
            for i, img in enumerate(images):
                combined.paste(img, (i * 426, 0))

            buffer = BytesIO()
            combined.save(buffer, format="JPEG")
            buffer.seek(0)  # ✅ Make sure the buffer is at the start

            st.image(buffer.getvalue(), caption="Combined Thumbnail (1280x720)", use_container_width=True)
            st.download_button(
                "💾 Download Thumbnail", 
                buffer.getvalue(), 
                file_name="combined_thumbnail.jpg", 
                mime="image/jpeg"
            )
