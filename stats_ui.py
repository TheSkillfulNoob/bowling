import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from data import load_sessions, filter_sessions, format_avg, comparison_emoji
from viz import plot_hist_with_normal, plot_kde

def stats_tabs():
    df = load_sessions()
    # Sidebar filters
    loc     = st.sidebar.selectbox("Location", ["All"] + df["Location"].dropna().unique().tolist())
    dmin, dmax = df.Date.min(), df.Date.max()
    start   = st.sidebar.date_input("Start Date", dmin)
    end     = st.sidebar.date_input("End Date", dmax)
    filt    = filter_sessions(df, start, end, loc)

    # Create four sub-tabs
    tab_trends, tab_dist, tab_summary, tab_pb = st.tabs([
        "📈 Trends",
        "📊 Distributions",
        "🧾 Summary",
        "🏆 PBs"
    ])

    # --- Tab 1: Trends ---
    with tab_trends:
        st.subheader("Time Series Trends")
        avg_by_date = filt.groupby("Date")[["Spares","Strikes","Pins","Total"]].mean()
        dates = avg_by_date.index

        col1, col2 = st.columns(2)
        # Left: Spare & Strike
        with col1:
            fig1, ax1 = plt.subplots()
            avg_by_date[["Spares","Strikes"]].plot(marker="o", ax=ax1)
            ax1.set_title("Spare & Strike")
            ax1.set_ylabel("Count")
            # tidy X-ticks
            tick_idx = np.linspace(0, len(dates)-1, 5, dtype=int)
            ax1.set_xticks([dates[i] for i in tick_idx])
            ax1.set_xticklabels([dates[i].strftime("%d/%m") for i in tick_idx], rotation=45)
            st.pyplot(fig1)
        # Right: Pins & Total
        with col2:
            fig2, ax2 = plt.subplots()
            avg_by_date[["Pins","Total"]].plot(marker="o", ax=ax2)
            ax2.set_title("Pins & Total")
            ax2.set_ylabel("Score")
            ax2.set_xticks([dates[i] for i in tick_idx])
            ax2.set_xticklabels([dates[i].strftime("%d/%m") for i in tick_idx], rotation=45)
            st.pyplot(fig2)

    # --- Tab 2: Distributions ---
    with tab_dist:
        st.subheader("Distribution of Total Scores")
        col1, col2 = st.columns(2)
        # KDE
        with col1:
            fig_kde = plot_kde(filt["Total"])
            st.pyplot(fig_kde)
        # Histogram + Normal
        with col2:
            fig_hist, mu, sigma = plot_hist_with_normal(filt["Total"])
            st.pyplot(fig_hist)

    # --- Tab 3: Summary Statistics ---
    with tab_summary:
        st.subheader("📋 Key Statistics & Personal Bests")
        # 1) Basic quintiles table
        desc = filt["Total"].describe()[["min","25%","50%","75%","max"]]
        summary_df = pd.DataFrame(desc.rename({
            "min":"Min","25%":"Q1","50%":"Median","75%":"Q3","max":"Max"
        })).T
        st.table(summary_df)

        # 2) Moving averages: 5MA vs 10MA
        dates = filt["Date"].drop_duplicates().sort_values(ascending=False)
        last5  = dates.head(5)
        last10 = dates.head(10)
        overall = filt[["Spares","Strikes","Pins","Total"]].mean()
        avg5    = filt[filt["Date"].isin(last5)][["Spares","Strikes","Pins","Total"]].mean()
        avg10   = filt[filt["Date"].isin(last10)][["Spares","Strikes","Pins","Total"]].mean()

        def fmt(s): return s.round(2)
        df_ma = pd.DataFrame({
            "Overall": format_avg(overall),
            "5MA":     fmt(avg5),
            "10MA":    fmt(avg10)
        })
        # Add trend emojis comparing 5MA vs 10MA
        df_ma["Trend"] = [
            comparison_emoji(avg10[c], avg5[c]) for c in ["Spares","Strikes","Pins","Total"]
        ]
        st.table(df_ma)

    # --- Tab 4: Personal Bests ---
    with tab_pb:
        st.subheader("Personal Bests")
        pb = []
        for metric, max_possible in zip(
            ["Spares","Strikes","Pins","Total"], [10,12,100,300]
        ):
            best_val  = df[metric].max()
            best_date = df[df[metric]==best_val]["Date"].iloc[0].strftime("%d/%m/%Y")
            pb.append((metric, f"{best_val} / {max_possible}", best_date))

        pb_df = pd.DataFrame(pb, columns=["Metric","Best (out of)","Date"])
        st.table(pb_df)