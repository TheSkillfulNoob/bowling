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