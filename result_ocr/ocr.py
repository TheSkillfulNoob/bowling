# Updated `ocr.py` with EasyOCR fallback

import pytesseract
import easyocr
import numpy as np
from .preprocess import to_gray, remove_red_circles, preprocess_for_ocr
from .deskew      import detect_skew_by_hough, rotate
from .segment     import crop_row, split_frames

# Tesseract config
CONFIG = '--psm 7 -c tessedit_char_whitelist=123456789X/-F'

# Initialize EasyOCR reader once
_easy_reader = easyocr.Reader(['en'], gpu=False)

def _ocr_image(mask: np.ndarray) -> str:
    """Attempt OCR with Tesseract, fallback on EasyOCR."""
    # Try Tesseract
    try:
        txt = pytesseract.image_to_string(mask, config=CONFIG).strip().replace(' ', '')
        if txt:
            return txt
    except pytesseract.pytesseract.TesseractNotFoundError:
        pass

    # Fallback to EasyOCR
    results = _easy_reader.readtext(mask, detail=0, paragraph=False)
    # Join and clean
    return ''.join(results).replace(' ', '')

def run_pipeline(img: np.ndarray) -> list[str]:
    # 1) initial row + deskew
    row    = crop_row(img)
    gray   = to_gray(remove_red_circles(row))
    angle  = detect_skew_by_hough(gray)
    img2   = rotate(img, angle)
    row2   = crop_row(img2)

    # 2) split & OCR
    outs = []
    for fr in split_frames(row2):
        clean = remove_red_circles(fr)
        g     = to_gray(clean)
        mask  = preprocess_for_ocr(g)
        txt   = _ocr_image(mask)
        outs.append(txt)
    return outs

# End of ocr.py
