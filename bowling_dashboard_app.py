import streamlit as st
from ocr_ui import session_input_tab, compute_bowling_stats
from stats_ui import stats_tabs
from regression_ui import regression_tabs
# from prof_ui import professional_tab
from sheets import push_session_data, push_ground_truth, sync_aggregates_from_full
from data import load_sessions, filter_sessions
import pandas as pd

st.set_page_config("🎳 Andrew's Dashboard")
st.title("🎳 Andrew's Bowling Stats")
sync_aggregates_from_full()
# Tab: add session
tabs = st.tabs(["➕ Process Session",
                "📈 Stats",
                "📊 Regression", 
                #"🏅 Professional"
                ])
with tabs[0]:
    session_input_tab()

with tabs[1]:
    stats_tabs()

with tabs[2]:
    regression_tabs()

#with tabs[3]:
#    professional_tab()