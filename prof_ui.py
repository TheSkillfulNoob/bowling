import streamlit as st
import pandas as pd
from sheets import get_ground_truth_sheet
from result_ocr.ocr import parse_splits_from_frames

def professional_tab():
    st.subheader("🏅 Professional Analysis")

    # Let user pick a session (by date & game)
    data = pd.DataFrame(get_ground_truth_sheet().get_all_records())
    key = st.selectbox("Choose session", data.apply(lambda r: f"{r.Date} – Game {r.Game}", axis=1))
    row = data[data.apply(lambda r: f"{r.Date} – Game {r.Game}", axis=1) == key].iloc[0]

    frames = [row[f"F{i}"] for i in range(1,11)]
    # Parse rolls and split info
    rolls, split_info = parse_splits_from_frames(frames)

    # 1) Spare conversion rate
    spares = [i for i,fr in enumerate(frames,1) if "/" in fr]
    spare_success = len(spares)
    spare_rate = spare_success / len(spares) if spares else 0.0

    # 2) Strike rate
    strikes = sum(1 for fr in frames if fr=="X")
    strike_rate = strikes / 10

    # 3) Spare bonus avg: pins scored on roll immediately after a spare
    bonuses = []
    idx = 0
    for fr in frames:
        if "/" in fr:
            idx += 2
            bonuses.append(rolls[idx])
        else:
            idx += (1 if fr=="X" else 2)
    spare_bonus = sum(bonuses)/len(bonuses) if bonuses else 0.0

    # 4) Split & conversion: let user enter or parsed
    splits     = st.number_input("Number of splits faced", min_value=0)
    conversions= st.number_input("Number converted", min_value=0, max_value=splits)
    split_rate = conversions / splits if splits else 0.0

    st.metric("Spare Conversion Rate", f"{spare_rate:.0%}")
    st.metric("Strike Rate (per frame)", f"{strike_rate:.0%}")
    st.metric("Avg Spare Bonus", f"{spare_bonus:.1f} pins")
    st.metric("Split Conversion Rate", f"{split_rate:.0%}")