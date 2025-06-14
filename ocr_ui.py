import streamlit as st
import pandas as pd
import cv2, numpy as np
from PIL import Image
from sheets import push_ground_truth
from result_ocr.ocr import run_pipeline
from result_ocr.preprocess import to_gray, remove_red_circles
from result_ocr.segment import crop_row, split_frames

def ocr_review_tab():
    st.subheader("✏️ OCR Review")
    uploaded = st.file_uploader("Upload a *cropped* row image", type=["png","jpg","jpeg"])
    if not uploaded:
        st.info("Please upload a row crop.")
        return

    pil = Image.open(uploaded)
    bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    # Preview frames
    row = crop_row(bgr)
    clean = remove_red_circles(row)
    frames = split_frames(clean)
    cols = st.columns(10)
    for i,f in enumerate(frames):
        with cols[i]:
            st.image(to_gray(f), clamp=True)
            st.caption(f"F{i+1}")

    # OCR
    preds = run_pipeline(bgr)
    df = pd.DataFrame({"Frame":range(1,11),"Predicted":preds,"Corrected":preds[:]})

    if hasattr(st, 'data_editor'):
        edited = st.data_editor(df)
    else:
        edited = st.experimental_data_editor(df)

    if st.button("Submit ground truth"):
        push_ground_truth(edited)
        st.success("✅ Updated Bowling-full sheet.")

def run_ocr_and_get_frames(uploaded_file) -> list[str]:
    """Uploads → previews → data_editor → returns final 10-frame strings."""
    pil = Image.open(uploaded_file)
    bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    # Preview frames
    row = crop_row(bgr)
    clean = remove_red_circles(row)
    frames = split_frames(clean)
    cols = st.columns(10)
    for i,f in enumerate(frames):
        with cols[i]:
            st.image(to_gray(f), clamp=True)
            st.caption(f"F{i+1}")
    
    # For brevity, assume run_pipeline returns initial preds
    preds = run_pipeline(bgr)
    # then show preds in editable table and get back `corrected`
    # (you can refactor your existing code into here)
    df = pd.DataFrame({"Frame":range(1,11),"Predicted":preds,"Corrected":preds[:]})
    if hasattr(st, 'data_editor'):
        corrected = st.data_editor(df)
    else:
        corrected = st.experimental_data_editor(df)

    if st.button("Submit ground truth"):
        push_ground_truth(corrected)
        st.success("✅ Updated Bowling-full sheet.")
    corrected = preds  # <-- after user edits
    return corrected

def compute_bowling_stats(frames: list[str]) -> dict:
    """Given 10 frame‐strings like 'X','9/','81',… compute total, strikes, spares, pins."""
    rolls = []
    for fr in frames:
        if fr == "X":
            rolls.append(10)
        elif "/" in fr:
            first = int(fr[0])
            rolls.append(first)
            rolls.append(10 - first)
        else:
            # e.g. '81','9-','--'
            a, b = fr[0], fr[1]
            rolls.append(int(a) if a.isdigit() else 0)
            rolls.append(int(b) if b.isdigit() else 0)
    # compute total pins
    pins = sum(rolls)
    # count strikes/spares
    strikes = sum(1 for fr in frames if fr == "X")
    spares  = sum(1 for fr in frames if "/" in fr)
    return {"total": pins, "pins": pins, "strikes": strikes, "spares": spares}