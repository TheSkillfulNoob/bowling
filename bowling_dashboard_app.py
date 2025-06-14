import streamlit as st
from ocr_ui import ocr_review_tab
from stats_ui import stats_tabs
from regression_ui import regression_tabs
from sheets import push_session_data
from data import load_sessions, filter_sessions
import pandas as pd

st.set_page_config("Andrew's 🎳 Dashboard")
st.title("🎳 Andrew's Bowling Tracker")

# Tab: add session
tabs = st.tabs(["➕ Add Session","📈 Stats","📊 Regression","✏️ OCR Review"])
with tabs[0]:
    st.subheader("➕ Add New Game Session")
    # (your sidebar form logic here)
    # on submit: push_session_data(df)

with tabs[1]:
    stats_tabs()

with tabs[2]:
    regression_tabs()

with tabs[3]:
    ocr_review_tab()