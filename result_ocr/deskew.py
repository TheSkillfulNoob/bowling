import cv2, numpy as np

def detect_skew_by_hough(gray: np.ndarray) -> float:
    edges = cv2.Canny(gray,50,150)
    lines = cv2.HoughLines(edges,1,np.pi/180,150)
    if lines is None:
        return 0.0
    angles = [(θ*180/np.pi - 90) for ρ,θ in lines[:,0] if abs(θ*180/np.pi-90)<10]
    if not angles:
        return 0.0
    a = float(np.median(angles))
    return float(np.clip(a, -5.0, 5.0))

def rotate(img: np.ndarray, angle: float) -> np.ndarray:
    h,w = img.shape[:2]
    M  = cv2.getRotationMatrix2D((w/2,h/2), -angle, 1)
    return cv2.warpAffine(img,M,(w,h),flags=cv2.INTER_CUBIC)