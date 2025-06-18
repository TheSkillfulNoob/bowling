import streamlit as st
import pandas as pd
from sheets import get_ground_truth_sheet
from result_ocr.ocr import compute_bowling_stats_from_string
from bonus_viz import (
    plot_spare_bonus_distribution,
    plot_strike_bonus_distributions,
)
from viz import plot_hist_with_normal  # if you want overall score dists

def professional_tab():
    st.subheader("🏅 Professional Analysis")

    # 1) Load all games
    df = pd.DataFrame(get_ground_truth_sheet().get_all_records())
    if df.empty:
        st.info("No game strings yet.")
        return

    # 2) Show global distributions
    games = df['Game String'].tolist()
    st.markdown("### Spare Bonus Distribution")
    st.pyplot(plot_spare_bonus_distribution(games))

    st.markdown("### Strike Bonus Distributions")
    st.pyplot(plot_strike_bonus_distributions(games))

    # 3) Show conditional P(conversion|first_throw)
    #st.markdown("### Spare Conversion Rate by First Throw")
    #sp_df = pd.DataFrame([
    #    {'first': int(gs[i-1]), 'bonus': compute_bowling_stats_from_string(gs)['Pins']} 
    #    for gs in games for i,ch in enumerate(gs) if ch=='/'
    #])

    # 4) Select a single session to show its raw stats
    sel = st.selectbox("Pick a session", df.apply(lambda r: f"{r.Date} – Game {r.Game}", axis=1))
    row = df[df.apply(lambda r: f"{r.Date} – Game {r.Game}", axis=1)==sel].iloc[0]
    stats = compute_bowling_stats_from_string(row['Game String'])
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total",    stats['Total'])
    c2.metric("Pins",     stats['Pins'])
    c3.metric("Strikes",  stats['Strikes'])
    c4.metric("Spares",   stats['Spares'])
