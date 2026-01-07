#!/usr/bin/env python3
"""
CG_ocr_handler.py - PaddleOCR Handler for Text Extraction

This module handles OCR (Optical Character Recognition) using PaddleOCR
to extract text from prescription and clinical report images.

MEMORY OPTIMIZATION: PaddleOCR is loaded lazily and can be unloaded
to free memory when not in use.

Target Platform: RDK X5 Kit (4GB RAM, Ubuntu 22.04 ARM64)

Run with: env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 script.py
"""

import os
import gc
from typing import Optional, List, Tuple

# Global OCR instance (lazy loaded)
_ocr_instance = None


def get_ocr_instance():
    """
    Get or create PaddleOCR instance (lazy loading).
    
    Returns:
        PaddleOCR instance
    """
    global _ocr_instance
    
    if _ocr_instance is None:
        print("[OCR] Loading PaddleOCR model (this may take a moment)...")
        
        # Set environment variable to disable model source check
        os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"
        
        from paddleocr import PaddleOCR
        from CG_config import OCR_LANG, OCR_USE_ANGLE_CLS
        
        _ocr_instance = PaddleOCR(
            use_angle_cls=OCR_USE_ANGLE_CLS,
            lang=OCR_LANG,
            show_log=False,  # Reduce verbosity
            use_gpu=False,   # CPU mode for RDK X5
        )
        
        print("[OCR] ✅ PaddleOCR loaded successfully")
    
    return _ocr_instance


def unload_ocr():
    """
    Unload PaddleOCR to free memory.
    
    Call this after OCR processing is complete to reclaim RAM.
    """
    global _ocr_instance
    
    if _ocr_instance is not None:
        print("[OCR] Unloading PaddleOCR to free memory...")
        _ocr_instance = None
        gc.collect()
        print("[OCR] ✅ Memory freed")


def extract_text(image_path: str) -> str:
    """
    Extract text from an image using PaddleOCR.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Extracted text as a single string
    """
    try:
        if not os.path.exists(image_path):
            print(f"[OCR] ❌ Image not found: {image_path}")
            return ""
        
        ocr = get_ocr_instance()
        
        print(f"[OCR] Processing: {image_path}")
        result = ocr.ocr(image_path, cls=False)
        
        # Extract text from OCR result
        extracted_lines = []
        
        if result and len(result) > 0:
            # Handle different result formats
            lines = result[0] if isinstance(result[0], list) else result
            
            for line in lines:
                if line and len(line) >= 2:
                    text_info = line[1]
                    if isinstance(text_info, tuple) and len(text_info) >= 1:
                        text = text_info[0]
                        extracted_lines.append(text)
        
        full_text = "\n".join(extracted_lines)
        
        if full_text:
            print(f"[OCR] ✅ Extracted {len(extracted_lines)} lines of text")
        else:
            print("[OCR] ⚠️ No text found in image")
        
        return full_text
        
    except Exception as e:
        print(f"[OCR] ❌ Error: {e}")
        return ""


def extract_text_with_details(image_path: str) -> List[Tuple[str, float, List]]:
    """
    Extract text with confidence scores and bounding boxes.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        List of tuples: (text, confidence, bounding_box)
    """
    try:
        if not os.path.exists(image_path):
            print(f"[OCR] ❌ Image not found: {image_path}")
            return []
        
        ocr = get_ocr_instance()
        
        print(f"[OCR] Processing with details: {image_path}")
        result = ocr.ocr(image_path, cls=False)
        
        # Extract detailed results
        detailed_results = []
        
        if result and len(result) > 0:
            lines = result[0] if isinstance(result[0], list) else result
            
            for line in lines:
                if line and len(line) >= 2:
                    box = line[0]
                    text_info = line[1]
                    
                    if isinstance(text_info, tuple) and len(text_info) >= 2:
                        text = text_info[0]
                        confidence = text_info[1]
                        detailed_results.append((text, confidence, box))
        
        return detailed_results
        
    except Exception as e:
        print(f"[OCR] ❌ Error: {e}")
        return []


def save_annotated_image(
    image_path: str,
    output_path: str,
    font_path: Optional[str] = None
) -> bool:
    """
    Save image with OCR annotations (bounding boxes and text).
    
    Args:
        image_path: Input image path
        output_path: Output annotated image path
        font_path: Path to font file for text rendering
        
    Returns:
        True if successful
    """
    try:
        from PIL import Image
        from paddleocr import draw_ocr
        import cv2
        from CG_config import OCR_FONT_PATH
        
        font_path = font_path or OCR_FONT_PATH
        
        ocr = get_ocr_instance()
        result = ocr.ocr(image_path, cls=False)
        
        if not result or len(result) == 0:
            print("[OCR] No text to annotate")
            return False
        
        lines = result[0] if isinstance(result[0], list) else result
        
        # Prepare data for drawing
        boxes = [line[0] for line in lines if line]
        txts = [line[1][0] for line in lines if line and len(line) >= 2]
        scores = [line[1][1] for line in lines if line and len(line) >= 2]
        
        # Draw annotations
        image = Image.open(image_path).convert("RGB")
        im_show = draw_ocr(image, boxes, txts, scores, font_path=font_path)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save (convert RGB->BGR for cv2.imwrite)
        cv2.imwrite(output_path, im_show[:, :, ::-1])
        print(f"[OCR] ✅ Annotated image saved: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"[OCR] ❌ Annotation error: {e}")
        return False


def preprocess_prescription_text(text: str) -> str:
    """
    Clean and preprocess OCR text from prescriptions.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Basic cleaning
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        # Remove excessive whitespace
        line = " ".join(line.split())
        
        # Skip very short lines (likely noise)
        if len(line) < 2:
            continue
        
        cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)


# ============================================================
# TEST FUNCTION
# ============================================================
def test_ocr_handler():
    """Test OCR functionality."""
    print("=" * 50)
    print("📝 OCR Handler Test")
    print("=" * 50)
    
    from CG_config import DATA_DIR, OUTPUT_DIR
    
    # Look for test image
    test_images = [
        DATA_DIR / "paddleocr_test.jpg",
        DATA_DIR / "test_prescription.jpg",
    ]
    
    test_image = None
    for img in test_images:
        if img.exists():
            test_image = str(img)
            break
    
    if not test_image:
        print("[TEST] No test image found in data directory")
        print("[TEST] Please add a test image to:", DATA_DIR)
        return
    
    print(f"\n[TEST] Testing OCR on: {test_image}")
    
    # Extract text
    text = extract_text(test_image)
    
    if text:
        print("\n[TEST] Extracted text:")
        print("-" * 40)
        print(text)
        print("-" * 40)
        
        # Save annotated image
        annotated_path = str(OUTPUT_DIR / "ocr_test_annotated.jpg")
        save_annotated_image(test_image, annotated_path)
    else:
        print("[TEST] ❌ No text extracted")
    
    # Free memory
    print("\n[TEST] Freeing OCR memory...")
    unload_ocr()
    
    print("\n[TEST] OCR test complete!")


if __name__ == "__main__":
    test_ocr_handler()
