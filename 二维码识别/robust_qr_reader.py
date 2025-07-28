#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
robust_qr_reader.py — 高鲁棒性二维码解码器（无窗口，只输出文本）

命令行用法:
    python robust_qr_reader.py /path/to/photo.jpg

作为库调用:
    from robust_qr_reader import decode_qr
    texts = decode_qr("/path/to/photo.jpg")
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from pyzbar import pyzbar


# ----------------------------------------------------------------------
# 1. OpenCV 后端：兼容各版本 detectAndDecodeMulti 返回值
# ----------------------------------------------------------------------
def _decode_opencv(img: np.ndarray):
    """OpenCV QRCodeDetector 解码（兼容不同 OpenCV 版本）"""
    det = cv2.QRCodeDetector()
    try:
        # OpenCV ≥4.5.2: retval, decoded_info, points, straight_qrcode
        retval, decoded, points, _ = det.detectAndDecodeMulti(img)
    except ValueError:
        # OpenCV <4.5.2: decoded_info, points, straight_qrcode
        decoded, points, _ = det.detectAndDecodeMulti(img)
        retval = True

    if not decoded:
        return []

    # 如果 points 是 None，用空数组占位
    if points is None:
        points = [np.empty((0, 2), dtype=np.float32)] * len(decoded)

    results = []
    for text, pts in zip(decoded, points):
        if not text:
            continue
        # 确保 pts 是二维数组
        pts_arr = np.asarray(pts, dtype=np.float32).reshape(-1, 2)
        results.append({"text": text, "points": pts_arr})
    return results


# ----------------------------------------------------------------------
# 2. ZBar 后端
# ----------------------------------------------------------------------
def _decode_pyzbar(img: np.ndarray):
    res = []
    for z in pyzbar.decode(img):
        if z.type == "QRCODE":
            pts = np.array([(p.x, p.y) for p in z.polygon], dtype=np.float32)
            res.append({"text": z.data.decode(), "points": pts})
    return res


# ----------------------------------------------------------------------
# 3. 透视矫正重试（OpenCV 仅检测角点未解码时）
# ----------------------------------------------------------------------
def _warp_and_retry(img: np.ndarray, points: np.ndarray):
    if points.shape[0] != 4:
        return []
    # 排序角点：左上(0), 右上(1), 右下(2), 左下(3)
    rect = np.zeros((4, 2), dtype="float32")
    s = points.sum(axis=1)
    diff = np.diff(points, axis=1)
    rect[0] = points[np.argmin(s)]
    rect[2] = points[np.argmax(s)]
    rect[1] = points[np.argmin(diff)]
    rect[3] = points[np.argmax(diff)]
    # 目标正方形边长
    side = int(max(
        np.linalg.norm(rect[0] - rect[1]),
        np.linalg.norm(rect[1] - rect[2]),
        np.linalg.norm(rect[2] - rect[3]),
        np.linalg.norm(rect[3] - rect[0]),
    ))
    dst = np.array([[0, 0], [side-1, 0], [side-1, side-1], [0, side-1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (side, side))
    return _decode_opencv(warped) + _decode_pyzbar(warped)


# ----------------------------------------------------------------------
# 4. 自适应直方图增强
# ----------------------------------------------------------------------
def _preprocess(gray: np.ndarray):
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


# ----------------------------------------------------------------------
# 5. 综合解码流程
# ----------------------------------------------------------------------
def _try_decode(img: np.ndarray):
    # 1) 原图直接解码
    results = _decode_opencv(img) + _decode_pyzbar(img)

    # 2) OpenCV 仅检测角点时做透视矫正重试
    det = cv2.QRCodeDetector()
    _, corners = det.detect(img)
    if corners is not None:
        for c in corners:
            results += _warp_and_retry(img, c.squeeze())

    # 3) 预处理后再试
    if not results:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        enhanced = _preprocess(gray)
        results = _decode_opencv(enhanced) + _decode_pyzbar(enhanced)

    # 4) 旋转尝试
    if not results:
        for flag in (
            cv2.ROTATE_90_CLOCKWISE,
            cv2.ROTATE_180,
            cv2.ROTATE_90_COUNTERCLOCKWISE,
        ):
            rot = cv2.rotate(img, flag)
            results = _decode_opencv(rot) + _decode_pyzbar(rot)
            if results:
                break

    # 去重并保持顺序
    seen, uniq = set(), []
    for r in results:
        t = r["text"]
        if t not in seen:
            seen.add(t)
            uniq.append(r)
    return uniq


def decode_qr(image_path: str | Path, max_side: int = 1600) -> list[str]:
    """
    返回图片中所有二维码文本，按出现顺序去重。
    会在必要时自动缩放（最长边 ≤ max_side）。
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"无法读取图片：{image_path}")
    h, w = img.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        img = cv2.resize(img, (int(w*scale), int(h*scale)))
    return [r["text"] for r in _try_decode(img)]


# ----------------------------------------------------------------------
# 6. 命令行接口
# ----------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python robust_qr_reader.py /path/to/photo.jpg", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    try:
        texts = decode_qr(path)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    if not texts:
        print("未检测到二维码。")
        sys.exit(0)

    for txt in texts:
        print(txt)
