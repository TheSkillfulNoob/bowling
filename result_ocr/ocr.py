import pytesseract
from .preprocess import to_gray, remove_red_circles, preprocess_for_ocr
from .deskew      import detect_skew_by_hough, rotate
from .segment     import crop_row, split_frames

CONFIG = '--psm 7 -c tessedit_char_whitelist=123456789X/-F'

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
        txt   = pytesseract.image_to_string(mask, config=CONFIG).strip().replace(' ','')
        outs.append(txt)
    return outs