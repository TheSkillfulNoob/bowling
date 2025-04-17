# bowling_dashboard_app.py (Refactored & Cleaned)

import gspread
from scipy import stats
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import statsmodels.api as sm
import seaborn as sns
import numpy as np
from gspread_dataframe import set_with_dataframe
from datetime import datetime

# === Google Sheet Functions ===
def connect_to_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)
    return client.open("bowling_db").sheet1

def load_data():
    sheet = connect_to_sheet()
    df = pd.DataFrame(sheet.get_all_records())
    df = df.dropna(subset=["Date"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    return df.dropna(subset=["Date"])

def update_data(date, location, games):
    df = load_data()
    date = pd.to_datetime(date).date()
    new_rows = [{
        "Date": date,
        "Location": location,
        "Game": i+1,
        "Spare": s, "Strike": t, "Pins": p, "Total": score
    } for i, (s, t, p, score) in enumerate(games)]

    df = df[~((df["Date"] == date) & (df["Location"].str.lower() == location.lower()))]
    updated_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    set_with_dataframe(connect_to_sheet(), updated_df)
    st.success(f"✅ Updated session on {date} at {location}")

# === Helper Functions ===
def format_avg(series):
    return pd.Series({
        "Spare": round(series.get("Spare", 0), 3),
        "Strike": round(series.get("Strike", 0), 3),
        "Pins": round(series.get("Pins", 0), 2),
        "Total": round(series.get("Total", 0), 2)
    })

def comparison_emoji(base, compare):
    if pd.notna(base) and pd.notna(compare):
        ratio = (compare - base) / base
        if ratio > 0.03: return "🟢⬆️"
        if ratio < -0.03: return "🔴⬇️"
    return ""

def plot_residuals_with_fit(x, y, xlabel, color):
    coeffs = np.polyfit(x, y, 1)
    reg_line = np.poly1d(coeffs)
    residuals = y - reg_line(x)

    fig1, ax1 = plt.subplots()
    ax1.scatter(x, y, alpha=0.6, color=color)
    ax1.plot(np.sort(x), reg_line(np.sort(x)), 'k--')
    ax1.text(0.05, 0.95, f"y = {coeffs[0]:.2f}x + {coeffs[1]:.2f}", transform=ax1.transAxes,
             fontsize=9, bbox=dict(boxstyle="round", fc="white", ec="gray"))
    ax1.set(title=f"Total Score vs. {xlabel}", xlabel=xlabel, ylabel="Total Score")

    fig2, ax2 = plt.subplots()
    ax2.scatter(x, residuals, alpha=0.6, color="gray")
    ax2.axhline(0, linestyle="--", color="black")
    ax2.set(title=f"Residuals vs. {xlabel}", xlabel=xlabel, ylabel="Residuals")

    return fig1, fig2

def plot_hist_with_normal(y):
    mu, sigma = np.mean(y), np.std(y)
    fig, ax1 = plt.subplots()
    counts, bins, _ = ax1.hist(y, bins=20, color="skyblue", edgecolor="black", alpha=0.7)
    ax2 = ax1.twinx()
    ax2.plot(bins, stats.norm.pdf(bins, mu, sigma), 'k--', label=f"N({mu:.1f}, {sigma:.2f}²)")
    ax2.legend(loc="upper right")
    ax1.set(title="Histogram with Normal Fit", xlabel="Total Score", ylabel="Frequency")
    ax2.set_ylabel("Density")
    return fig, mu, sigma

# === Streamlit UI ===
st.title("🎳 Bowling Dashboard")

# Data Entry
st.sidebar.header("➕ Add New Game Session")
with st.sidebar.form("entry_form", clear_on_submit=False):
    date_input = st.date_input("Date")
    location = st.text_input("Location")
    num_games = st.number_input("Games", min_value=1, step=1)
    games = []
    for i in range(int(num_games)):
        st.markdown(f"**Game {i+1}**")
        s = st.number_input(f"Spare {i+1}", 0, 10, key=f"sp_{i}")
        t = st.number_input(f"Strike {i+1}", 0, 10, key=f"st_{i}")
        p = st.number_input(f"Pins {i+1}", 0, 100, key=f"pi_{i}")
        score = st.number_input(f"Total {i+1}", 0, 300, key=f"to_{i}")
        games.append((s, t, p, score))
    if st.form_submit_button("Add to Database"):
        update_data(date_input, location, games)

# Load and Process Data
df = load_data()
df["Bonus"] = df["Spare"] + df["Strike"]
start_default, end_default = df["Date"].min(), df["Date"].max()

# === Analysis Section ===
if len(df) >= 5:
    tab_analysis, tab_dist, tab_scatter, tab_summary, tab_coef = st.tabs([
        "📈 Time Series", "🎯 Distribution", "📊 Dot Plots", "📜 OLS Summary", "📈 Coefficients"])

    with tab_analysis:
        locations = df['Location'].dropna().unique()
        col1, col2, col3 = st.columns(3)
        with col1:
            loc = st.selectbox("Filter location", ["All"] + list(locations))
        with col2:
            start = st.date_input("Start Date", value=start_default)
        with col3:
            end = st.date_input("End Date", value=end_default)

        data = df[(df['Date'] >= start) & (df['Date'] <= end)]
        if loc != "All":
            data = data[data['Location'] == loc]

        avg_by_date = data.groupby('Date')[['Spare', 'Strike', 'Pins', 'Total']].mean()
        col1, col2 = st.columns(2)
        with col1:
            fig1, ax1 = plt.subplots()
            avg_by_date[['Spare', 'Strike']].plot(marker='o', ax=ax1)
            ax1.set_title("Spare & Strike Over Time")
            st.pyplot(fig1)
        with col2:
            fig2, ax2 = plt.subplots()
            avg_by_date[['Pins', 'Total']].plot(marker='o', ax=ax2)
            ax2.set_title("Pins & Total Over Time")
            st.pyplot(fig2)

    with tab_dist:
        st.markdown("### 🧾 Score Summary")
        desc = df['Total'].describe()[["min", "25%", "50%", "75%", "max"]]
        st.dataframe(pd.DataFrame(desc.rename({"min":"Min", "25%":"Q1", "50%":"Median", "75%":"Q3", "max":"Max"})).T)
        col1, col2 = st.columns(2)
        with col1:
            fig, mu, sigma = plot_hist_with_normal(df["Total"])
            st.pyplot(fig)
        with col2:
            fig_kde, ax = plt.subplots()
            sns.kdeplot(df["Total"], fill=True, ax=ax, color="purple")
            ax.set_title("KDE of Total Scores")
            st.pyplot(fig_kde)

    with tab_scatter:
        for metric, color in zip(["Strike", "Bonus", "Pins"], ["blue", "green", "pink"]):
            col1, col2 = st.columns(2)
            x = df["Strike"] + df["Spare"] if metric == "Bonus" else df[metric]
            fig1, fig2 = plot_residuals_with_fit(x, df["Total"], metric, color)
            with col1: st.pyplot(fig1)
            with col2: st.pyplot(fig2)

    with tab_summary:
        X = sm.add_constant(df[["Spare", "Strike", "Pins"]])
        y = df["Total"]
        model = sm.OLS(y, X).fit()
        st.text(model.summary())

    with tab_coef:
        st.dataframe(model.params.rename("Coefficient").to_frame())

else:
    st.warning("Not enough data for analysis.")