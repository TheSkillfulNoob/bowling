import streamlit as st
import pandas as pd
import cv2, numpy as np
from PIL import Image
from sheets import push_session_data, push_ground_truth
from result_ocr.ocr import run_pipeline
from result_ocr.preprocess import to_gray, remove_red_circles
from result_ocr.segment   import crop_row, split_frames

def compute_bowling_stats(frames):
    rolls, strikes, spares = [], 0, 0
    for fr in frames:
        if fr == "X":
            rolls.append(10); strikes += 1
        elif "/" in fr:
            first = int(fr[0])
            rolls += [first, 10 - first]; spares += 1
        else:
            a,b = fr[0], fr[1]
            rolls += [
                int(a) if a.isdigit() else 0,
                int(b) if b.isdigit() else 0
            ]
    total = sum(rolls)
    return {"Date": None, "Location": None, "Game": None,
            "Total": total, "Pins": total,
            "Strikes": strikes, "Spares": spares}

def session_input_tab():
    """Renders the entire ➕ Add Session flow."""
    st.subheader("➕ Input with OCR Review")

    # ─── Metadata ───────────────────────────────────────────────
    date   = st.date_input("Date")
    loc    = st.text_input("Location")
    game_n = st.number_input("Game number", min_value=1, step=1)

    # ─── File Upload & Frame Preview ───────────────────────────
    uploaded = st.file_uploader("Upload a *cropped* row image", type=["png","jpg","jpeg"])
    if not uploaded:
        st.info("Please upload a row-crop image.")
        return

    # load & deskew inside run_pipeline if you like,
    # but here we just preview the raw frames:
    pil = Image.open(uploaded)
    bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    row = crop_row(bgr)
    cleaned = remove_red_circles(row)
    frames = split_frames(cleaned)

    cols = st.columns(10)
    for i, f in enumerate(frames):
        with cols[i]:
            st.image(to_gray(f), use_column_width=True, clamp=True)
            st.caption(f"F{i+1}")

    # ─── OCR + Editable Table ───────────────────────────────────
    preds = run_pipeline(bgr)
    df = pd.DataFrame({
        "Frame":     list(range(1,11)),
        "Predicted": preds,
        "Corrected": preds[:]   # initial copy
    })
    editor = getattr(st, "data_editor", st.experimental_data_editor)
    edited = editor(df)

    # ─── Compute Totals ────────────────────────────────────────
    if st.button("Compute Totals"):
        final_frames = edited["Corrected"].tolist()
        stats = compute_bowling_stats(final_frames)
        # override metadata
        stats["Date"], stats["Location"], stats["Game"] = (
            date.strftime("%Y-%m-%d"), loc, int(game_n)
        )
        st.metric("🏆 Total Score", stats["Total"])
        st.metric("💥 Strikes",     stats["Strikes"])
        st.metric("🔄 Spares",      stats["Spares"])
        st.metric("🎳 Pins",        stats["Pins"])
        # stash for submit
        st.session_state["ocr_stats"]  = stats
        st.session_state["ocr_frames"] = final_frames

    # ─── Submit Session ────────────────────────────────────────
    if st.session_state.get("ocr_stats") and st.button("Submit Session"):
        s = st.session_state["ocr_stats"]
        # 1) aggregate row to Bowling
        row_df = pd.DataFrame([{
            "Date":     s["Date"],
            "Location": s["Location"],
            "Game":     s["Game"],
            "Total":    s["Total"],
            "Pins":     s["Pins"],
            "Strikes":  s["Strikes"],
            "Spares":   s["Spares"],
        }])
        push_session_data(row_df)

        # 2) detailed frames to Bowling-full
        frames_dict = {f"F{i+1}": f for i, f in enumerate(st.session_state["ocr_frames"])}
        detail_df = pd.DataFrame([{
            "Date":     s["Date"],
            "Location": s["Location"],
            "Game":     s["Game"],
            **frames_dict
        }])
        push_ground_truth(detail_df)

        st.success("✅ Session & frames saved to Google Sheets!")