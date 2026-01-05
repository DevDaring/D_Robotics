#!/usr/bin/env python3
import os
import argparse

import cv2
import numpy as np
from PIL import Image

# IMPORTANT:
# - This script targets PaddleOCR 2.x (e.g., 2.7.0.3)
# - PaddleOCR 2.x uses ocr.ocr(...), NOT ocr.predict(...) [web:389]
from paddleocr import PaddleOCR, draw_ocr


def init_args():
    p = argparse.ArgumentParser(description="PaddleOCR runner (PaddleOCR 2.x API)")
    p.add_argument("--image_path", default="data/paddleocr_test.jpg", type=str, help="Input image path")
    p.add_argument("--output_folder", default="output/predict.jpg", type=str, help="Output image path")
    p.add_argument("--lang", default="en", type=str, help="OCR language, e.g. en/ch")
    p.add_argument("--use_angle_cls", action="store_true", help="Enable angle classifier (cls)")
    p.add_argument("--disable_model_source_check", action="store_true", help="Disable model source connectivity check")
    p.add_argument("--font_path", default="./doc/fonts/simfang.ttf", type=str, help="Font for draw_ocr()")
    return p.parse_args()


def ensure_dir_for_file(path: str):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def main():
    args = init_args()

    # Must be set BEFORE importing/initializing PaddleOCR to suppress the hoster check message
    if args.disable_model_source_check:
        os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

    # Init OCR engine (2.x API) [web:389]
    ocr = PaddleOCR(use_angle_cls=args.use_angle_cls, lang=args.lang)

    # Run OCR (2.x API) [web:389]
    result = ocr.ocr(args.image_path, cls=args.use_angle_cls)

    # PaddleOCR may return either:
    # - result = [ [box,(text,score)], ... ]  (common for single image)
    # - result = [ res_for_img0, res_for_img1, ... ] (batch/multi-page style)
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list) and len(result[0]) > 0:
        # Heuristic: if first element looks like [box,(text,score)] then it's already single-image
        if isinstance(result[0][0], (list, tuple)) and len(result[0]) == 2:
            lines = result
        else:
            lines = result[0]
    else:
        lines = []

    # Print text results
    for line in lines:
        box, (txt, score) = line[0], line[1]
        print(f"{txt}\t{score:.3f}")

    # Draw + save annotated image (official pattern) [web:389]
    image = Image.open(args.image_path).convert("RGB")
    boxes = [line[0] for line in lines]
    txts = [line[1][0] for line in lines]
    scores = [line[1][1] for line in lines]

    im_show = draw_ocr(image, boxes, txts, scores, font_path=args.font_path)  # returns numpy RGB array [web:389]
    ensure_dir_for_file(args.output_folder)

    # Save (convert RGB->BGR for cv2.imwrite)
    cv2.imwrite(args.output_folder, im_show[:, :, ::-1])
    print(f"Saved: {args.output_folder}")


if __name__ == "__main__":
    main()
