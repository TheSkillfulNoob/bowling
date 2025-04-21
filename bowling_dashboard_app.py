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
    credentials_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open("bowling_db").sheet1

def load_data_from_gsheet():
    sheet = connect_to_sheet()
    df = pd.DataFrame(sheet.get_all_records())
    df = df.dropna(subset=["Date"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    return df.dropna(subset=["Date"])

def update_data_to_gsheet(date_str, location_str, games):
    df = load_data_from_gsheet()
    date_parsed = pd.to_datetime(date_str, dayfirst=True).date()
    new_rows = [
        {"Date": date_parsed, "Location": location_str, "Game": i+1, "Spare": g[0], "Strike": g[1], "Pins": g[2], "Total": g[3]}
        for i, g in enumerate(games)
    ]
    df = df[~((df["Date"] == date_parsed) & (df["Location"].str.lower() == location_str.lower()))]
    updated_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    set_with_dataframe(connect_to_sheet(), updated_df)
    st.success(f"✅ Session for {date_parsed} at {location_str} added/replaced.")

# === Streamlit UI ===
st.set_page_config(page_title="Andrew's Bowling Dashboard")
st.title("🎳 Andrew's Bowling Dashboard")

st.sidebar.header("➕ Add New Game Session")
with st.sidebar.form("entry_form", clear_on_submit=False):
    date_input = st.date_input("Date")
    location_input = st.text_input("Location")
    num_games = st.number_input("Number of Games", min_value=1, step=1)
    games_input = [
        (st.number_input(f"Spare {i+1}", key=f"sp_{i}", min_value=0, max_value=10),
         st.number_input(f"Strike {i+1}", key=f"st_{i}", min_value=0, max_value=12),
         st.number_input(f"Pins {i+1}", key=f"pi_{i}", min_value=0, max_value=100),
         st.number_input(f"Total {i+1}", key=f"to_{i}", min_value=0, max_value=300))
        for i in range(int(num_games))
    ]
    write_key = st.text_input("🔐 Write Access Password", type="password")
    
    submitted = st.form_submit_button("Add to Database")
    if submitted:
        if write_key == st.secrets["access"]["write_password"]:
            update_data_to_gsheet(date_input, location_input, games_input)
        else:
            st.error("🚫 Invalid password. Write access denied.")
        
# === Load Data and Apply Filters ===
df = load_data_from_gsheet()
start_date_default, end_date_default = df['Date'].min(), df['Date'].max()
locations = df['Location'].dropna().unique()
col1, col2, col3 = st.columns(3)
with col1:
    location = st.selectbox("Select location (optional)", ["All"] + list(locations))
with col2:
    start_date = st.date_input("Start Date", value=start_date_default)
with col3:
    end_date = st.date_input("End Date", value=end_date_default)
filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
if location != "All":
    filtered = filtered[filtered['Location'] == location]

# Helper Functions
def format_avg(series): # For tab_ts
    return pd.Series({
        "Spare": round(series.get("Spare", 0), 3),
        "Strike": round(series.get("Strike", 0), 3),
        "Pins": round(series.get("Pins", 0), 2),
        "Total": round(series.get("Total", 0), 2)
    })

def comparison_emoji(base_val, compare_val): # For tab_ts
    if pd.notna(base_val) and pd.notna(compare_val):
        ratio = (compare_val - base_val) / base_val
        if ratio > 0.03: return " 🟢⬆️"
        elif ratio < -0.03: return " 🔴⬇️"
    return ""

def plot_residuals_with_fit(x, y, xlabel, color): # For tab_dotplot
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

def plot_hist_with_normal(y): # For tab_scoredist
    mu, sigma = np.mean(y), np.std(y)
    fig, ax1 = plt.subplots()
    counts, bins, _ = ax1.hist(y, bins=20, color="skyblue", edgecolor="black", alpha=0.7)
    ax2 = ax1.twinx()
    ax2.plot(bins, stats.norm.pdf(bins, mu, sigma), 'k--', label=f"N({mu:.1f}, {sigma:.2f}²)")
    ax2.legend(loc="upper right")
    ax1.set(title="Histogram with Normal Fit", xlabel="Total Score", ylabel="Frequency")
    ax2.set_ylabel("Density")
    return fig, mu, sigma

# === Analysis Tabs ===
if len(filtered) >= 5:
    X = filtered[['Spare', 'Strike', 'Pins']]
    X = sm.add_constant(X)
    y = filtered['Total']
    model = sm.OLS(y, X).fit()

    tab_ts, tab_scorestats, tab_dotplot, tab_regression = st.tabs(["📈 Time Series and Dist.", "🎯 Key Statistics", "📊 Dot Plots", "📜 Reg. Summary"])
    with tab_ts:
        st.subheader("📈 Time Series Trends")

        avg_by_date = filtered.groupby('Date')[['Spare', 'Strike', 'Pins', 'Total']].mean()
        dates = avg_by_date.index

        col1, col2 = st.columns(2)

        # Left plot: Spare & Strike
        with col1:
            fig1, ax1 = plt.subplots()
            avg_by_date[['Spare', 'Strike']].plot(marker='o', ax=ax1)
            ax1.set_title("Spare & Strike")
            ax1.set_ylabel("Count")

            # Choose 5 evenly spaced x-ticks based on index positions
            tick_indices = np.linspace(0, len(dates) - 1, 5, dtype=int)
            tick_labels = [dates[i].strftime("%d/%m") for i in tick_indices]
            ax1.set_xticks([dates[i] for i in tick_indices])
            ax1.set_xticklabels(tick_labels, rotation=45)

            st.pyplot(fig1)

        # Right plot: Pins & Total
        with col2:
            fig2, ax2 = plt.subplots()
            avg_by_date[['Pins', 'Total']].plot(marker='o', ax=ax2)
            ax2.set_title("Pins & Total")
            ax2.set_ylabel("Score")

            # Same strategy: 5 spaced ticks
            ax2.set_xticks([dates[i] for i in tick_indices])
            ax2.set_xticklabels(tick_labels, rotation=45)

            st.pyplot(fig2)
            
        st.subheader("📊 Histogram and Normal Density Plot")
        col1, col2 = st.columns(2)
        with col1:
            fig, mu, sigma = plot_hist_with_normal(filtered["Total"])
            st.pyplot(fig)
        with col2:
            fig_kde, ax = plt.subplots()
            sns.kdeplot(filtered["Total"], fill=True, ax=ax, color="purple")
            ax.set_title("KDE of Total Scores")
            st.pyplot(fig_kde)
        
    with tab_scorestats:
        st.markdown("### 🧾 Score Summary")
        desc = filtered['Total'].describe()[["min", "25%", "50%", "75%", "max"]]
        st.dataframe(pd.DataFrame(desc.rename({"min":"Min", "25%":"Q1", "50%":"Median", "75%":"Q3", "max":"Max"})).T)
        
        st.subheader("🎯 Key Statistics")
        last_5_dates = filtered['Date'].drop_duplicates().sort_values(ascending=False).head(5)
        last_10_dates = filtered['Date'].drop_duplicates().sort_values(ascending=False).head(10)

        overall = filtered[['Spare', 'Strike', 'Pins', 'Total']].mean()
        avg_5d = filtered[filtered['Date'].isin(last_5_dates)][['Spare', 'Strike', 'Pins', 'Total']].mean()
        avg_10d = filtered[filtered['Date'].isin(last_10_dates)][['Spare', 'Strike', 'Pins', 'Total']].mean()

        final_overall = format_avg(overall).rename(f"n = {filtered.shape[0]} games")
        final_avg_5d = format_avg(avg_5d).rename("5MA")
        emojis_5d = [comparison_emoji(avg_10d[x], avg_5d[x]) for x in avg_5d.index]

        theoretical_max = {"Spare": 10, "Strike": 12, "Pins": 100, "Total": 300}
        pb_rows = []
        for stat, max_val in theoretical_max.items():
            pb_val = df[stat].max()
            pb_date = df[df[stat] == pb_val]["Date"].iloc[0].strftime("%d/%m/%Y")
            pb_rows.append([f"{pb_val} ({max_val})", pb_date])

        avg_by_date = df.groupby('Date')[['Total']].mean()
        max_avg_total = avg_by_date['Total'].max()
        avg_pb_date = avg_by_date['Total'].idxmax().strftime("%d/%m/%Y")
        pb_rows.append([f"{round(max_avg_total, 2)} (300)", avg_pb_date])

        final_max = pd.DataFrame(pb_rows, columns=["PB (out of)", "Date"], index=["Spare", "Strike", "Pins", "Total", "Day"])

        col1, col2, col3 = st.columns([9, 11, 14])
        with col1:
            st.markdown("**Overall: Average**")
            st.dataframe(final_overall.to_frame())
        with col2:
            st.markdown("**Moving Avg.**")
            st.dataframe(final_avg_5d.to_frame().assign(Trend=emojis_5d))
        with col3:
            st.markdown("**Personal Best**")
            st.dataframe(final_max)

        st.markdown("🟢⬆️ = 5MA > 10MA by more than 3%; 🔴⬇️ = 5MA < 10MA by more than 3%")

    with tab_dotplot:
        for metric, color in zip(["Strike", "Bonus", "Pins"], ["blue", "green", "pink"]):
            col1, col2 = st.columns(2)
            x = filtered["Strike"] + filtered["Spare"] if metric == "Bonus" else filtered[metric]
            fig1, fig2 = plot_residuals_with_fit(x, filtered["Total"], metric, color)
            with col1: st.pyplot(fig1)
            with col2: st.pyplot(fig2)

    with tab_regression:
        X = sm.add_constant(filtered[["Spare", "Strike"]])
        y = filtered["Total"]
        model = sm.OLS(y, X).fit()
        st.text(model.summary())

        st.dataframe(model.params.rename("Coefficient").to_frame())
else:
    st.warning("Not enough data!")