import streamlit as st
from sheets import get_ground_truth_sheet
from result_ocr.ocr import compute_bowling_stats_from_string
from bonus_viz import (
    plot_spare_bonus_distribution,
    plot_strike_bonus_distributions,
)
import pandas as pd
from itertools import accumulate
from typing import Tuple, List

def framewise_and_cumulative(gs: str) -> Tuple[List[str], List[int], List[int]]:
    """
    Returns (frame_strs, frame_scores, cumulative_scores) for a 10‐frame game string.
    Frame 10 is the rest of the string.
    """
    # build numeric rolls[]
    rolls = []
    for ch in gs:
        if ch == "X":
            rolls.append(10)
        elif ch == "/":
            rolls.append(10 - rolls[-1])
        elif ch in "-F":
            rolls.append(0)
        else:
            rolls.append(int(ch))

    frame_strs   = []
    frame_scores = []
    i = 0  # pointer into the string gs
    r = 0  # pointer into rolls[]

    for frame in range(1, 11):
        if frame < 10:
            # frames 1–9
            if rolls[r] == 10:
                # strike
                seg = "X"
                score = 10
                # bonus
                score += rolls[r+1] if r+1 < len(rolls) else 0
                score += rolls[r+2] if r+2 < len(rolls) else 0
                frame_strs.append(seg)
                frame_scores.append(score)
                i += 1
                r += 1
            else:
                # two-ball (or spare)
                seg = gs[i:i+2]
                first  = rolls[r]
                second = rolls[r+1] if r+1 < len(rolls) else 0
                if first + second == 10:
                    # spare
                    score = 10 + (rolls[r+2] if r+2 < len(rolls) else 0)
                else:
                    score = first + second
                frame_strs.append(seg)
                frame_scores.append(score)
                i += 2
                r += 2
        else:
            # frame 10: everything left
            seg = gs[i:]
            # turn seg into numeric list
            vals = []
            for ch in seg:
                if ch == "X":
                    vals.append(10)
                elif ch == "/":
                    vals.append(10 - vals[-1])
                elif ch in "-F":
                    vals.append(0)
                else:
                    vals.append(int(ch))
            score = sum(vals)
            frame_strs.append(seg)
            frame_scores.append(score)
            break

    cum_scores = list(accumulate(frame_scores))
    return frame_strs, frame_scores, cum_scores

def professional_tab():
    df = pd.DataFrame(get_ground_truth_sheet().get_all_records())
    if df.empty:
        st.info("No games yet.")
        return

    games = df["Game String"].tolist()
    meta  = df[["Date","Location","Game"]].apply(
        lambda r: f"{r.Date} – {r.Location} G{r.Game}", axis=1
    )

    tab_sp, tab_st, tab_gw = st.tabs(["📍 Spares","❌ Strikes","📊 Game Stats"])

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
        strs, fs, cs = framewise_and_cumulative(gs)

        df_fw = pd.DataFrame(
            [strs, fs, cs],
            index=["Rolls", "Frame Score", "Cumulative"]
        )
        df_fw.columns = [f"F{i}" for i in range(1,11)]
        st.table(df_fw)
        stats = compute_bowling_stats_from_string(gs)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total",    stats['Total'])
        c2.metric("Pins",     stats['Pins'])
        c3.metric("Strikes",  stats['Strikes'])
        c4.metric("Spares",   stats['Spares'])