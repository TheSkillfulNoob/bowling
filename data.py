import pandas as pd
import streamlit as st
from sheets import get_session_sheet

@st.cache_data(show_spinner=False)
def load_sessions() -> pd.DataFrame:
    records = get_session_sheet().get_all_records()
    df = pd.DataFrame(records)
    df = df.dropna(subset=["Date"])
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce").dt.date
    return df.dropna(subset=["Date"])

def filter_sessions(df: pd.DataFrame, start_date, end_date, location: str) -> pd.DataFrame:
    mask = (df["Date"] >= start_date) & (df["Date"] <= end_date)
    if location != "All":
        mask &= (df["Location"] == location)
    return df[mask]