import streamlit as st
import pandas as pd
import cv2, numpy as np
from PIL import Image
from sheets import push_session_data, push_ground_truth
from result_ocr.ocr import run_pipeline
from result_ocr.preprocess import to_gray, remove_red_circles
from result_ocr.segment   import crop_row, split_frames

def compute_bowling_stats(frames):
    # Build flat list of roll scores + frame start indices
    rolls = []
    frame_starts = []
    bonus_pins = 0
    for fr in frames:
        frame_starts.append(len(rolls))
        if fr == "X":
            rolls.append(10)
        else:
            # first roll
            a = fr[0]
            rolls.append(int(a) if a.isdigit() else 0)
            # second roll
            b = fr[1]
            if b == "/":
                rolls.append(10 - rolls[-1])
            else:
                rolls.append(int(b) if b.isdigit() else 0)
        # tenth frame can have a third roll
        if len(fr) == 3:
            c = fr[2]
            if c == "X":
                bonus_pins = 10
            elif c == "/":
                bonus_pins = 10 - rolls[-1]
            else:
                bonus_pins = (int(c) if c.isdigit() else 0)
            rolls.append(bonus_pins)

    total_score, strikes, spares = 0, 0, 0
    for i, fr in enumerate(frames):
        idx = frame_starts[i]
        # Strike
        if fr == "X":
            strikes += 1
            total_score += 10
            # bonus next two rolls
            if idx+1 < len(rolls): total_score += rolls[idx+1]
            if idx+2 < len(rolls): total_score += rolls[idx+2]
        # Spare (but not strike)
        elif "/" in fr:
            spares += 1
            total_score += 10
            # bonus next one roll
            if idx+2 < len(rolls): total_score += rolls[idx+2]
        else:
            # Open frame or 10th frame leftover
            # count how many rolls this frame contributed
            count = 1 if fr=="X" else (2 if len(fr)==2 else 3)
            total_score += sum(rolls[idx: idx+count])

    return {
        "Total":    total_score,
        "Strikes":  strikes,
        "Spares":   spares,
        "Pins":     sum(rolls) - bonus_pins
    }

def get_data_editor():
    """Picks the available Streamlit editor API."""
    if hasattr(st, "data_editor"):
        return st.data_editor
    if hasattr(st, "experimental_data_editor"):
        return st.experimental_data_editor
    return None

def session_input_tab():
    st.subheader("➕ Input with OCR Review")

    # 1) Metadata
    cols_metadata = st.columns(3)
    with cols_metadata[0]:
        date   = st.date_input("Date")
    with cols_metadata[1]:
        loc    = st.text_input("Location")
    with cols_metadata[2]:
        game_n = st.number_input("Game number", min_value=1, step=1)

    # 2) Upload & preview frames
    uploaded = st.file_uploader("Upload a cropped row image", type=["png","jpg","jpeg"])
    if not uploaded:
        st.info("Please upload a row‐crop.")
        return

    pil = Image.open(uploaded)
    bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    row = crop_row(bgr)
    clean = remove_red_circles(row)
    frames = split_frames(clean)
    cols = st.columns(10)
    for i,f in enumerate(frames):
        with cols[i]:
            st.image(to_gray(f), clamp=True)
            st.caption(f"F{i+1}")

    # OCR
    preds = run_pipeline(bgr)
    df = pd.DataFrame({"Frame":range(1,11),"Predicted":preds,"Corrected":preds[:]})
    if hasattr(st, "data_editor"):
        edited = st.data_editor(
            df,
            num_rows="fixed",
            use_container_width=True,
            hide_index=False
        )
    else:
        edited = st.experimental_data_editor(
            df,
            num_rows="fixed",
            use_container_width=True
        )
    
    # 4) Compute Totals in one row of metrics
    if st.button("Compute Totals"):
        final = edited["Corrected"].tolist()
        stats = compute_bowling_stats(final)
        stats["Date"], stats["Location"], stats["Game"] = (
            date.strftime("%Y-%m-%d"), loc, int(game_n)
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🏆 Total Score", f"{stats['Total']}")
        c2.metric("💥 Strikes",     f"{stats['Strikes']}")
        c3.metric("🔄 Spares",      f"{stats['Spares']}")
        c4.metric("🎳 Pins",        f"{stats['Pins']}")
        st.session_state["ocr_stats"]  = stats
        st.session_state["ocr_frames"] = final

    # 5) Submit both session and detailed frames
    if st.session_state.get("ocr_stats") and st.button("Submit Session"):
        s = st.session_state["ocr_stats"]
        # aggregate to Bowling
        push_session_data(pd.DataFrame([{
            "Date":     s["Date"],
            "Location": s["Location"],
            "Game":     s["Game"],
            "Total":    s["Total"],
            "Pins":     s["Pins"],
            "Strikes":  s["Strikes"],
            "Spares":   s["Spares"]
        }]))
        # detailed to Bowling-full
        frames = st.session_state["ocr_frames"]
        rolls = []
        # frames 1–9: exactly 2 rolls each
        for fr in frames[:9]:
            if fr == "X":
                # strike → 10 pins on first roll, blank second roll
                rolls += ["X", ""]
            elif "/" in fr:
                rolls += [fr[0], "/"]
            else:
                a = fr[0] if len(fr) > 0 else ""
                b = fr[1] if len(fr) > 1 else ""
                rolls += [a, b]
        # frame 10: up to 3 rolls
        fr10 = frames[9]
        for ch in fr10:
            rolls.append(ch)
        # pad to 21 throws if only 2 in 10th frame
        while len(rolls) < 21:
            rolls.append("")

        # build detail dict
        detail = {
            "Date":     s["Date"],
            "Location": s["Location"],
            "Game":     s["Game"],
        }
        # assign T1…T21
        for idx, r in enumerate(rolls, start=1):
            frame = min((idx + 1) // 2, 10)
            attempt = idx - frame * 2 + 2
            detail[f"Frame{frame}-{attempt}"] = r

        push_ground_truth(pd.DataFrame([detail]))        
        st.success("✅ Session saved!")