import streamlit as st
from sheets import get_ground_truth_sheet
from result_ocr.ocr import compute_bowling_stats_from_string
from bonus_viz import (
    plot_spare_bonus_distribution,
    plot_strike_bonus_distributions,
)
from typing import Tuple
import pandas as pd
import numpy as np
from itertools import accumulate

def framewise_and_cumulative(gs: str) -> Tuple[list[int], list[int]]:
    # Build roll list
    rolls = []
    for ch in gs:
        if ch == "X": rolls.append(10)
        elif ch == "/": rolls.append(10 - rolls[-1])
        elif ch in "-F": rolls.append(0)
        else: rolls.append(int(ch))

    frame_scores = []
    idx = 0
    # 10 frames
    for _ in range(10):
        if rolls[idx] == 10:
            # strike
            score = 10
            bonus1 = rolls[idx+1] if idx+1 < len(rolls) else 0
            bonus2 = rolls[idx+2] if idx+2 < len(rolls) else 0
            frame_scores.append(score + bonus1 + bonus2)
            idx += 1
        else:
            first, second = rolls[idx], (rolls[idx+1] if idx+1 < len(rolls) else 0)
            if first + second == 10:
                # spare
                bonus = rolls[idx+2] if idx+2 < len(rolls) else 0
                frame_scores.append(10 + bonus)
            else:
                frame_scores.append(first + second)
            idx += 2

    cum_scores = list(accumulate(frame_scores))
    return frame_scores, cum_scores


def professional_tab():
    st.subheader("🏅 Professional Analysis")
    df = pd.DataFrame(get_ground_truth_sheet().get_all_records())
    if df.empty:
        st.info("No games yet.")
        return

    games = df["Game String"].tolist()
    meta  = df[["Date","Location","Game"]].apply(
        lambda r: f"{r.Date} – {r.Location} G{r.Game}", axis=1
    )

    tab_sp, tab_st, tab_gw = st.tabs(["Spares","Strikes","Game Stats"])

    # — Tab 1: Spare analytics —
    with tab_sp:
        st.markdown("#### Spare Bonus Distribution")
        st.pyplot(plot_spare_bonus_distribution(games))

        st.markdown("#### Spare Conversion by First Ball")
        # you can build a DataFrame from bonus_viz.extract_spare_bonuses if you wrote it,
        # or inline:
        records = []
        for gs in games:
            for i,ch in enumerate(gs):
                if ch == "/":
                    first = int(gs[i-1]) if gs[i-1].isdigit() else 0
                    # next char bonus
                    raw_bonus = gs[i+1] if i+1 < len(gs) else "0"
                    bonus = 10 if raw_bonus=="X" else (0 if raw_bonus in "-F" else int(raw_bonus))
                    records.append({"first_throw": first, "bonus": bonus})
        sp_df = pd.DataFrame(records)
        rates = sp_df.assign(conv=lambda d: d.bonus>0) \
                     .groupby("first_throw").conv.mean()
        st.bar_chart(rates)

    # — Tab 2: Strike analytics —
    with tab_st:
        st.markdown("#### Strike Bonus Distributions")
        st.pyplot(plot_strike_bonus_distributions(games))

    # — Tab 3: Game‐wise frame & cumulative scores —
    with tab_gw:
        sel = st.selectbox("Pick session", meta)
        idx = meta.tolist().index(sel)
        gs  = games[idx]
        fs, cs = framewise_and_cumulative(gs)
        df_fw = pd.DataFrame([fs, cs], index=["Frame Score","Cumulative"])
        # label columns F1…F10
        df_fw.columns = [f"F{i}" for i in range(1,11)]
        st.table(df_fw)