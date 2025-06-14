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