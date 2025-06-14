import cv2, numpy as np

W = np.array([0.503, 0.423, 0.074], dtype=float)

def to_gray(img):
    b, g, r = cv2.split(img)
    return (W[0]*r + W[1]*g + W[2]*b).astype(np.uint8)

def remove_red_circles(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m1 = cv2.inRange(hsv, (0,100,100), (10,255,255))
    m2 = cv2.inRange(hsv, (170,100,100), (180,255,255))
    red = cv2.bitwise_or(m1, m2)
    red = cv2.morphologyEx(red, cv2.MORPH_CLOSE, np.ones((5,5),np.uint8))
    return cv2.inpaint(bgr, red, 3, cv2.INPAINT_TELEA)

def preprocess_for_ocr(gray):
    _, g1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    g2 = cv2.adaptiveThreshold(gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 15, 2)
    g2 = cv2.morphologyEx(g2, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
    return g1 if g1.sum()>g2.sum() else g2