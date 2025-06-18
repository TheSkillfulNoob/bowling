import pytesseract
import easyocr
import numpy as np
from .preprocess import to_gray, remove_red_circles, preprocess_for_ocr
from .deskew      import detect_skew_by_hough, rotate
from .segment     import crop_row, split_frames

CONFIG = '--psm 7 -c tessedit_char_whitelist=123456789X/-F'
_reader = easyocr.Reader(['en'], gpu=False)

def _ocr_image(mask: np.ndarray) -> str:
    try:
        txt = pytesseract.image_to_string(mask, config=CONFIG).strip().replace(' ','')
        if txt:
            return txt
    except pytesseract.pytesseract.TesseractNotFoundError:
        pass
    res = _reader.readtext(mask, detail=0, paragraph=False,
                           mag_ratio=2.0, text_threshold=0.4,
                           low_text=0.3, link_threshold=0.3)
    return ''.join(res).replace(' ','')

def run_pipeline(img: np.ndarray) -> list[str]:
    row  = crop_row(img)
    gray = to_gray(remove_red_circles(row))
    angle= detect_skew_by_hough(gray)
    img2 = rotate(img, angle)
    row2 = crop_row(img2)
    outs = []
    for fr in split_frames(row2):
        clean = remove_red_circles(fr)
        g     = to_gray(clean)
        m     = preprocess_for_ocr(g)
        outs.append(_ocr_image(m))
    return outs

def compute_bowling_stats_from_string(game_str: str) -> dict:
    """
    Safely score a 10‐frame bowling string via the numeric rolls list,
    avoiding any indexing of the raw string.
    """
     # 1) Build full roll list
    rolls = []
    for ch in game_str:
        if ch == "X":
            rolls.append(10)
        elif ch == "/":
            # spare: make up to 10
            rolls.append(10 - rolls[-1])
        elif ch in "-F":  # miss or foul
            rolls.append(0)
        else:
            rolls.append(int(ch))

    total, strikes, spares = 0, 0, 0
    pins_in_frame = 0
    roll_idx = 0

    # 2) Walk frame by frame
    for frame in range(1, 11):
        if game_str[roll_idx] == "X":
            # Strike frame
            strikes += 1
            total += 10
            # bonus: next two rolls
            total += rolls[roll_idx + 1] if roll_idx + 1 < len(rolls) else 0
            total += rolls[roll_idx + 2] if roll_idx + 2 < len(rolls) else 0
            pins_in_frame += 10
            roll_idx += 1

        else:
            # Two‐ball frame (might be spare)
            first = rolls[roll_idx]
            second = rolls[roll_idx + 1] if roll_idx + 1 < len(rolls) else 0

            if first + second == 10:
                # Spare
                spares += 1
                total += 10
                # bonus: next one roll
                total += rolls[roll_idx + 2] if roll_idx + 2 < len(rolls) else 0
            else:
                # Open frame
                total += first + second

            pins_in_frame += first + second
            roll_idx += 2
    return {
        "Total":    total,
        "Pins":     pins_in_frame,
        "Strikes":  strikes,
        "Spares":   spares
    }