import streamlit as st
import statsmodels.api as sm
from data import load_sessions, filter_sessions
from viz import plot_residuals

def regression_tabs():
    df = load_sessions()
    # apply same filters as stats_ui or reuse passed df
    #loc = st.sidebar.selectbox("Location (reg)", ["All"]+ df['Location'].unique().tolist())
    #dmin, dmax = df.Date.min(), df.Date.max()
    #start = st.sidebar.date_input("Start (reg)", dmin)
    #end   = st.sidebar.date_input("End (reg)", dmax)
    #filt  = filter_sessions(df, start, end, loc)
    filt = df
    tab1, tab2 = st.tabs(["📊 Dot Plot","📜 Regression"])
    with tab1:
        st.pyplot(plot_residuals(filt['Pins'], filt['Total'], 'Pins','blue'))
    with tab2:
        X = sm.add_constant(filt[['Spares','Strikes','Pins']])
        y = filt['Total']
        model = sm.OLS(y, X).fit()
        st.text(model.summary())
        st.dataframe(model.params.to_frame('Coef'))