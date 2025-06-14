import streamlit as st
from data import load_sessions, filter_sessions
from viz import plot_time_series, plot_hist_with_normal, plot_kde

def stats_tabs():
    df = load_sessions()
    loc = st.sidebar.selectbox("Location", ["All"]+ df['Location'].unique().tolist())
    dmin, dmax = df.Date.min(), df.Date.max()
    start = st.sidebar.date_input("Start", dmin)
    end   = st.sidebar.date_input("End", dmax)
    filt  = filter_sessions(df, start, end, loc)

    tab1, tab2 = st.tabs(["📈 Time Series","🎯 Stats Summary"])
    with tab1:
        st.pyplot(plot_time_series(
            filt.groupby('Date')[['Spare','Strike','Pins','Total']].mean()
        ))
        fig, mu, sigma = plot_hist_with_normal(filt['Total'])
        st.pyplot(fig)
        st.pyplot(plot_kde(filt['Total']))
    with tab2:
        st.dataframe(filt.describe())