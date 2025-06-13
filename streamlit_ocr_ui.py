import streamlit as st
from PIL     import Image
from ocr_pipeline.ocr import run_pipeline
import pandas as pd

st.set_page_config("Bowling OCR Review")
st.title("🎳 Bowling OCR: Review & Correct")

# 1) Upload
uploaded = st.file_uploader("Upload a *cropped* row image", type=["png","jpg","jpeg"])
if not uploaded:
    st.info("Please upload a row crop from your phone.")
    st.stop()

# 2) Run OCR
img = Image.open(uploaded)
pred = run_pipeline(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))

# 3) Build a DataFrame for review
df = pd.DataFrame({
    "Frame": list(range(1,11)),
    "Predicted": pred,
    "Corrected": pred[:]  # initialize same
})

# 4) Let user edit
edited = st.experimental_data_editor(df, num_rows="dynamic")

# 5) Highlight mismatches
def highlight_diff(row):
    return ['background-color: pink' if row.Predicted != row.Corrected else '' for _ in row]

st.dataframe(edited.style.apply(highlight_diff, axis=1), use_container_width=True)

# 6) On submit, push to GSheet "Bowling-full"
if st.button("Submit ground truth"):
    # filter only corrected != predicted if you want
    records = edited.to_dict(orient="records")
    # connect as in bowling_dashboard_app.py, but .worksheet("Bowling-full")
    sheet = connect_to_sheet().parent.open("v4_resources").worksheet("Bowling-full")
    # overwrite or append—depends on your design:
    df_out = pd.DataFrame(records)
    set_with_dataframe(sheet, df_out)
    st.success("✅ Ground truth uploaded to Bowling-full")