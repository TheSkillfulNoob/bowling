
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import statsmodels.api as sm
from datetime import datetime

CSV_FILE = "past_games.csv"

# Load data from CSV
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_FILE)

    # Parse mixed date formats safely and convert to datetime.date
    df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Date'])  # Remove any unparseable dates
    df['Date'] = df['Date'].dt.date  # Standardize to date only (drop time)
    
    df = df.sort_values(by=['Date', 'Game']).reset_index(drop=True)
    return df

# Update the CSV with new game entries
def update_data(date_str, location_str, games):
    try:
        date_parsed = pd.to_datetime(date_str, dayfirst=True).date()
    except Exception as e:
        st.error(f"Invalid date format. Use DD/MM/YYYY. Details: {e}")
        return

    # Create new game entries
    new_rows = []
    for i, g in enumerate(games, 1):
        spare, strike, pins, total = g
        new_rows.append({
            'Date': date_parsed,
            'Location': location_str,
            'Game': i,
            'Spare': spare,
            'Strike': strike,
            'Pins': pins,
            'Total': total
        })

    # Load existing data
    existing = pd.read_csv(CSV_FILE)
    existing['Date'] = pd.to_datetime(existing['Date'], format='mixed', dayfirst=True, errors='coerce').dt.date

    # Remove any prior session on the same date and location (case-insensitive)
    existing = existing[~((existing['Date'] == date_parsed) & 
                          (existing['Location'].str.lower() == location_str.lower()))]

    # Append new session
    combined = pd.concat([existing, pd.DataFrame(new_rows)], ignore_index=True)
    combined.to_csv(CSV_FILE, index=False)

    st.success(f"✅ Added new session for {date_parsed} at {location_str} (replacing previous if existed).")

# ---- Streamlit UI ----
st.title("🎳 Bowling Stats Dashboard")

# Data Entry Section
st.sidebar.header("➕ Add New Game Session")
with st.sidebar.form("entry_form", clear_on_submit=False):
    date_input = st.text_input("Date (DD/MM/YYYY)")
    location_input = st.text_input("Location")
    num_games = st.number_input("Number of Games", min_value=1, step=1)
    
    games_input = []
    for i in range(int(num_games)):
        st.markdown(f"**Game {i+1}**")
        spare = st.number_input(f"Spare {i+1}", key=f"sp_{i}", min_value=0, max_value = 10, step=1)
        strike = st.number_input(f"Strike {i+1}", key=f"st_{i}", min_value=0, max_value = 10, step=1)
        pins = st.number_input(f"Pins {i+1}", key=f"pi_{i}", min_value=0, max_value = 100, step=1)
        total = st.number_input(f"Total {i+1}", key=f"to_{i}", min_value=0, max_value = 300, step=1)
        games_input.append((spare, strike, pins, total))

    submitted = st.form_submit_button("Add to Database")
    if submitted:
        update_data(date_input, location_input, games_input)
        # How to check duplicate data (where date and location are the same, and overwrite with newer data?)

# Load and filter data
df = load_data()

# Filters
locations = df['Location'].dropna().unique()

col1, col2, col3 = st.columns(3)
with col1:
    location = st.selectbox("Select location (optional)", ["All"] + list(locations))
with col2:
    start_date = st.date_input("Start Date", value=df['Date'].min())
with col3:
    end_date = st.date_input("End Date", value=df['Date'].max())

filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
if location != "All":
    filtered = filtered[filtered['Location'] == location]

# Averages
st.subheader("📊 Averages")

col1, col2, col3 = st.columns(3)
overall = df[['Spare', 'Strike', 'Pins', 'Total']].mean().rename("Overall")
last_50 = df.tail(50)[['Spare', 'Strike', 'Pins', 'Total']].mean().rename("Last 50 Games")
last_5_dates = df['Date'].drop_duplicates().sort_values(ascending=False).head(5) #nlargest(5) returns error
last_5 = df[df['Date'].isin(last_5_dates)][['Spare', 'Strike', 'Pins', 'Total']].mean().rename("Last 5 Dates")

with col1:
    st.markdown("**Overall**")
    st.dataframe(overall.to_frame())
with col2:
    st.markdown("**Last 50 Games**")
    st.dataframe(last_50.to_frame())
with col3:
    st.markdown("**Last 5 Dates**")
    st.dataframe(last_5.to_frame())

# Charts
st.subheader("📈 Trends Over Time")
avg_by_date = df.groupby('Date')[['Spare', 'Strike', 'Pins', 'Total']].mean()

col1, col2 = st.columns(2)

with col1:
    fig1, ax1 = plt.subplots()
    avg_by_date[['Spare', 'Strike']].plot(marker='o', ax=ax1)
    ax1.set_title("Spare & Strike")
    ax1.set_ylabel("Count")
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots()
    avg_by_date[['Pins', 'Total']].plot(marker='o', ax=ax2)
    ax2.set_title("Pins & Total")
    ax2.set_ylabel("Score")
    st.pyplot(fig2)

# Regression
st.subheader("📉 Regression Model")

if len(filtered) >= 5:
    # filtered['Strike_squared'] = filtered['Strike'] ** 2
    X = filtered[['Spare', 'Strike', 'Pins']]
    X = sm.add_constant(X)
    y = filtered['Total']
    model = sm.OLS(y, X).fit()
    
    tab1, tab2 = st.tabs(["📜 Summary", "📈 Coefficients"])
    
    with tab1:
        st.text(model.summary())
    with tab2:
        st.dataframe(model.params.rename("Coefficient").to_frame())
else:
    st.warning("Not enough data after filtering to fit a regression model.")
