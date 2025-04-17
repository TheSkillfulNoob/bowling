import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import statsmodels.api as sm
import seaborn as sns
import numpy as np
from gspread_dataframe import set_with_dataframe
from datetime import datetime
import json

# Connect to Google Sheet
def connect_to_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("bowling_db").sheet1
    return sheet

# Load game records from sheet
def load_data_from_gsheet():
    sheet = connect_to_sheet()
    df = pd.DataFrame(sheet.get_all_records())
    df = df.dropna(subset=["Date"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df = df.dropna(subset=["Date"])  # remove rows where parsing failed
    return df

# Add new games and overwrite by date/location
def update_data_to_gsheet(date_str, location_str, games):
    df = load_data_from_gsheet()
    date_parsed = pd.to_datetime(date_str, dayfirst=True).date()

    new_rows = []
    for i, g in enumerate(games, 1):
        spare, strike, pins, total = g
        new_rows.append({
            "Date": date_parsed,
            "Location": location_str,
            "Game": i,
            "Spare": spare,
            "Strike": strike,
            "Pins": pins,
            "Total": total
        })

    df = df[~((df["Date"] == date_parsed) & (df["Location"].str.lower() == location_str.lower()))]
    updated_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    sheet = connect_to_sheet()
    set_with_dataframe(sheet, updated_df)
    st.success(f"✅ Added new session for {date_parsed} at {location_str} (replacing previous if existed).")

# UI
st.title("🎳 Bowling Dashboard")

st.sidebar.header("➕ Add New Game Session")
with st.sidebar.form("entry_form", clear_on_submit=False):
    date_input = st.date_input("Date")
    location_input = st.text_input("Location")
    num_games = st.number_input("Number of Games", min_value=1, step=1)

    games_input = []
    for i in range(int(num_games)):
        st.markdown(f"**Game {i+1}**")
        spare = st.number_input(f"Spare {i+1}", key=f"sp_{i}", min_value=0, max_value=10)
        strike = st.number_input(f"Strike {i+1}", key=f"st_{i}", min_value=0, max_value=10)
        pins = st.number_input(f"Pins {i+1}", key=f"pi_{i}", min_value=0, max_value=100)
        total = st.number_input(f"Total {i+1}", key=f"to_{i}", min_value=0, max_value=300)
        games_input.append((spare, strike, pins, total))

    submitted = st.form_submit_button("Add to Database")
    if submitted:
        update_data_to_gsheet(date_input, location_input, games_input)

df = load_data_from_gsheet()
if not df.empty and df['Date'].notna().any():
    start_date_default = df['Date'].min()
    end_date_default = df['Date'].max()
else:
    start_date_default = end_date_default = datetime.today()

# Statistics
st.subheader("📊 Statistics")
col1, col2, col3 = st.columns([4, 7, 7])

def format_avg(series):
    return pd.Series({
        "Spare": round(series.get("Spare", 0), 3),
        "Strike": round(series.get("Strike", 0), 3),
        "Pins": round(series.get("Pins", 0), 2),
        "Total": round(series.get("Total", 0), 2)
    })

def comparison_emoji(base_val, compare_val):
    if pd.notna(base_val) and pd.notna(compare_val):
        ratio = (compare_val - base_val) / base_val
        if ratio > 0.03:
            return " 🟢⬆️"
        elif ratio < -0.03:
            return " 🔴⬇️"
    return ""

last_5_dates = df['Date'].drop_duplicates().sort_values(ascending=False).head(5)
last_10_dates = df['Date'].drop_duplicates().sort_values(ascending=False).head(10)

overall = df[['Spare', 'Strike', 'Pins', 'Total']].mean()
avg_5d = df[df['Date'].isin(last_5_dates)][['Spare', 'Strike', 'Pins', 'Total']].mean()
avg_10d = df[df['Date'].isin(last_10_dates)][['Spare', 'Strike', 'Pins', 'Total']].mean()

final_overall = format_avg(overall).rename(f"{df.shape[0]} games")
# Theoretical maximums for each stat
theoretical_max = {
    "Spare": 10,
    "Strike": 12,
    "Pins": 100,
    "Total": 300
}

# Initialize structure
pb_rows = []
for stat, max_val in theoretical_max.items():
    pb_val = df[stat].max()
    pb_date = df[df[stat] == pb_val]["Date"].iloc[0].strftime("%d/%m/%Y")  # take first matching
    pb_rows.append([f"{pb_val} ({max_val})", pb_date])

# PB for highest daily average total
avg_by_date = df.groupby('Date')[['Total']].mean()
max_avg_total = avg_by_date['Total'].max()
avg_pb_date = avg_by_date['Total'].idxmax().strftime("%d/%m/%Y")

pb_rows.append([f"{round(max_avg_total, 2)} (300)", avg_pb_date])

final_max = pd.DataFrame(pb_rows, 
    columns=["PB (out of)", "Date"],
    index=["Spare", "Strike", "Pins", "Total", "Day"]
)

final_avg_5d = format_avg(avg_5d).rename("5MA")
emojis_5d = [comparison_emoji(avg_10d[x], avg_5d[x]) for x in avg_5d.index]

with col1:
    st.markdown("**Overall: Average**")
    st.dataframe(final_overall.to_frame())
with col2:
    st.markdown("**Moving Avg.**")
    st.dataframe(final_avg_5d.to_frame().assign(Trend=emojis_5d))
with col3:
    st.markdown("**Personal Best**")
    st.dataframe(final_max)

st.markdown("🟢⬆️ is printed if 5MA is more than 3\% above 10MA; 🔴⬇️ for more than 3\% less.")

# Charts
st.subheader("📈 Trends Over Time")
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
    
avg_by_date = filtered.groupby('Date')[['Spare', 'Strike', 'Pins', 'Total']].mean()

col1, col2 = st.columns(2)
with col1:
    fig1, ax1 = plt.subplots()
    avg_by_date[['Spare', 'Strike']].plot(marker='o', ax=ax1)
    ax1.set_title("Spare & Strike")
    ax1.set_ylabel("Count")
    ax1.set_xticks(avg_by_date.index[::max(1, len(avg_by_date)//5)])
    ax1.set_xticklabels([d.strftime("%d/%m") for d in avg_by_date.index[::max(1, len(avg_by_date)//5)]], rotation=45)
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots()
    avg_by_date[['Pins', 'Total']].plot(marker='o', ax=ax2)
    ax2.set_title("Pins & Total")
    ax2.set_ylabel("Score")
    ax2.set_xticks(avg_by_date.index[::max(1, len(avg_by_date)//5)])
    ax2.set_xticklabels([d.strftime("%d/%m") for d in avg_by_date.index[::max(1, len(avg_by_date)//5)]], rotation=45)
    st.pyplot(fig2)

# Analysis
# Analysis
st.subheader("📉 Analysis")
if len(filtered) >= 5:
    X = filtered[['Spare', 'Strike', 'Pins']]
    X = sm.add_constant(X)
    y = filtered['Total']
    model = sm.OLS(y, X).fit()

    tab1, tab2, tab3, tab4 = st.tabs(["📜 Reg. Summary", "📈 Reg. Coefficients", "📊 Dot Plots", "🎯 Score Distribution"])

    with tab1:
        st.text(model.summary())

    with tab2:
        st.dataframe(model.params.rename("Coefficient").to_frame())

    # Helper function for scatter plots
    def plot_scatter_with_regression(x, y, title, xlabel, color="blue"):
        fig, ax = plt.subplots()

        # Scatter
        ax.scatter(x, y, alpha=0.6, color=color, label="Data")

        # Fit linear regression
        coeffs = np.polyfit(x, y, 1)
        reg_line = np.poly1d(coeffs)
        x_vals = np.linspace(min(x), max(x), 100)
        y_vals = reg_line(x_vals)

        # Plot regression line
        ax.plot(x_vals, y_vals, color="black", linestyle="--", label="Regression Line")

        # Annotate equation
        slope = coeffs[0]
        intercept = coeffs[1]
        ax.text(0.05, 0.95,
                f"y = {slope:.2f}x + {intercept:.2f}",
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray"))

        # Labels
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Total Score")
        ax.legend()

        return fig

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.pyplot(plot_scatter_with_regression(filtered["Strike"], filtered["Total"], "Total Score vs. Strikes", "Strikes"))
            st.pyplot(plot_scatter_with_regression(filtered["Strike"] + filtered["Spare"], filtered["Total"], "Total Score vs. Bonus Frames", "Strikes + Spares", "green"))
        with col2:
            st.pyplot(plot_scatter_with_regression(filtered["Spare"], filtered["Total"], "Total Score vs. Spares", "Spares", "orange"))
            st.pyplot(plot_scatter_with_regression(filtered["Pins"], filtered["Total"], "Total Score vs. Pins", "Total Pins", "pink"))

    with tab4:
        st.markdown("### 🎯 Distribution of Total Scores")

        col1, col2 = st.columns(2)

        with col1:
            fig_hist, ax_hist = plt.subplots()
            ax_hist.hist(filtered["Total"], bins=15, color="skyblue", edgecolor="black")
            ax_hist.set_title("Histogram of Total Scores")
            ax_hist.set_xlabel("Total Score")
            ax_hist.set_ylabel("Frequency")
            st.pyplot(fig_hist)

        with col2:
            fig_kde, ax_kde = plt.subplots()
            sns.kdeplot(filtered["Total"], fill=True, ax=ax_kde, color="purple", linewidth=2)
            ax_kde.set_title("KDE of Total Scores")
            ax_kde.set_xlabel("Total Score")
            ax_kde.set_ylabel("Density")
            st.pyplot(fig_kde)

else:
    st.warning("Not enough data!")