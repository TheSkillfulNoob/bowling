import numpy as np

def crop_row(img: np.ndarray) -> np.ndarray:
    h = img.shape[0]
    return img[int(0.3*h):int(0.59*h), :]

def split_frames(img: np.ndarray) -> list[np.ndarray]:
    h,w = img.shape[:2]
    out = []
    for i in range(10):
        x1 = int(i*w/10); x2 = int((i+1)*w/10)
        out.append(img[:, x1:x2])
    return out