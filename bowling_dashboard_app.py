import streamlit as st
from ocr_ui import ocr_review_tab, run_ocr_and_get_frames, compute_bowling_stats
from stats_ui import stats_tabs
from regression_ui import regression_tabs
from sheets import push_session_data, push_ground_truth
from data import load_sessions, filter_sessions
import pandas as pd

st.set_page_config("Andrew's 🎳 Dashboard")
st.title("🎳 Andrew's Bowling Tracker")

# Tab: add session
tabs = st.tabs(["➕ Add Session","📈 Stats","📊 Regression"])
with tabs[0]:
    # … inside tabs[0] …
    st.subheader("➕ Input with OCR Review")

    # 1️⃣ Metadata inputs
    date   = st.date_input("Date")
    loc    = st.text_input("Location")
    game_n = st.number_input("Game number", min_value=1, step=1)

    # 2️⃣ Upload & OCR
    uploaded = st.file_uploader("Upload a *cropped* row image", type=["png","jpg","jpeg"])
    if uploaded:
        # run_pipeline + preview + correction all in one helper
        frame_strings = run_ocr_and_get_frames(uploaded)
        st.write("Corrected frames:", frame_strings)

        # 3️⃣ Compute stats from frames
        stats = compute_bowling_stats(frame_strings)
        st.write("→ Total:",  stats["total"],
                "Spares:",     stats["spares"],
                "Strikes:",    stats["strikes"],
                "Pins:",       stats["pins"])

        if st.button("Submit Session"):
            # a) write aggregate row to `Bowling`
            row = {
            "Date": date.strftime("%Y-%m-%d"),
            "Location": loc,
            "Game": game_n,
            **stats
            }
            push_session_data(pd.DataFrame([row]))

            # b) write detailed frames + metadata to `Bowling-full`
            df_ft = pd.DataFrame({
            "Date":      date.strftime("%Y-%m-%d"),
            "Location":  loc,
            "Game":      game_n,
            **{f"F{i+1}": s for i,s in enumerate(frame_strings)}
            }, index=[0])
            push_ground_truth(df_ft)

            st.success("Session saved!")
    else:
        st.info("Please upload a cropped scoreboard row.")

with tabs[1]:
    stats_tabs()

with tabs[2]:
    regression_tabs()