import cv2
from ultralytics import YOLO
import numpy as np
import re
import os
from paddleocr import PaddleOCR

def detect_license_plates(
    video_path,
    model_path="./license_plate_detector.pt",
    confidence_threshold=0.45
):
    """
    Process a video to detect license plates and return unique plate numbers with highest confidence.
    
    Args:
        video_path (str): Path to the input video file
        model_path (str): Path to the YOLO model file for license plate detection
        confidence_threshold (float): Confidence threshold for license plate detection
        
    Returns:
        list: List of unique license plate texts with highest confidence scores
    """
    # Configure environment
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    
    # Initialize video capture
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    # Initialize YOLO Model
    model = YOLO(model_path)
    
    # Initialize Paddle OCR
    ocr = PaddleOCR(use_angle_cls=True, use_gpu=False)
    
    # Dictionary to store license plates with their highest confidence
    plate_confidence = {}
    
    # Process video frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect license plates using YOLO
        results = model.predict(frame, conf=confidence_threshold)
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detection_confidence = float(box.conf[0])
                
                # Extract license plate region
                plate_region = frame[y1:y2, x1:x2]
                
                # Recognize text using PaddleOCR
                ocr_result = ocr.ocr(plate_region, det=False, rec=True, cls=False)
                
                for r in ocr_result:
                    ocr_confidence = r[0][1]
                    if np.isnan(ocr_confidence):
                        ocr_confidence = 0
                    else:
                        ocr_confidence = float(ocr_confidence)
                    
                    # Get plate text and clean it
                    if ocr_confidence > 0.6:  # Confidence threshold for OCR
                        plate_text = r[0][0]
                        # Clean the text
                        pattern = re.compile('r[\W]')
                        plate_text = pattern.sub('', plate_text)
                        plate_text = plate_text.replace("???", "").replace("O", "0").replace("粤", "")
                        
                        # Skip empty or very short plate text
                        if len(plate_text) < 4:
                            continue
                        
                        # Calculate combined confidence (detection * OCR)
                        combined_confidence = detection_confidence * ocr_confidence
                        
                        # Update if this is a higher confidence detection of this plate
                        if plate_text not in plate_confidence or combined_confidence > plate_confidence[plate_text]:
                            plate_confidence[plate_text] = combined_confidence
    
    # Release resources
    cap.release()
    
    # Get unique license plates sorted by confidence (highest first)
    unique_plates = sorted(plate_confidence.keys(), key=lambda x: plate_confidence[x], reverse=True)
    
    return unique_plates




# license_plates = detect_license_plates("demo.mp4")
# print("Detected license plates:")
# for plate in license_plates:
#     print(plate)
























































































































# import cv2
# import numpy as np
# import pytesseract
# # import pytesseract

# # Set the path to the tesseract executable
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust path as needed
# from typing import Optional, List, Tuple

# def preprocess_for_anpr(image: np.ndarray) -> np.ndarray:
#     """
#     Preprocess image for better license plate recognition
#     """
#     # Convert to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
#     # Apply bilateral filter to reduce noise while keeping edges sharp
#     blur = cv2.bilateralFilter(gray, 11, 17, 17)
    
#     # Apply thresholding to get binary image
#     _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
#     return binary

# def detect_plate_regions(image: np.ndarray) -> List[np.ndarray]:
#     """
#     Detect regions in the image that may contain license plates
#     """
#     # Preprocess the image
#     preprocessed = preprocess_for_anpr(image)
    
#     # Find contours
#     contours, _ = cv2.findContours(preprocessed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
#     # Filter contours based on area and aspect ratio
#     potential_plates = []
#     for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
#         x, y, w, h = cv2.boundingRect(contour)
#         aspect_ratio = w / float(h)
        
#         # License plates typically have an aspect ratio between 2 and 5
#         if 1.5 <= aspect_ratio <= 6.0 and w > 60 and h > 10:
#             # Extract the potential plate region with a small margin
#             margin = 10
#             x_margin = max(0, x - margin)
#             y_margin = max(0, y - margin)
#             plate_region = image[y_margin:y+h+margin, x_margin:x+w+margin]
#             potential_plates.append(plate_region)
    
#     return potential_plates

# def extract_plate_text(image: np.ndarray) -> Optional[str]:
#     """
#     Extract license plate text from an image using OCR
#     """
#     # Get potential plate regions
#     plate_regions = detect_plate_regions(image)
    
#     # Configure pytesseract for license plate recognition
#     custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    
#     # Try to recognize text from each potential plate region
#     for plate_region in plate_regions:
#         # Preprocess the plate region for better OCR
#         gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
#         _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
#         # Apply OCR
#         plate_text = pytesseract.image_to_string(binary, config=custom_config)
        
#         # Clean up the text
#         plate_text = ''.join(c for c in plate_text if c.isalnum())
        
#         # If we found text with a reasonable length, return it
#         if len(plate_text) >= 4 and len(plate_text) <= 10:
#             return plate_text
    
#     return None











# import cv2
# import numpy as np
# import easyocr
# from typing import Optional, List

# # Initialize the EasyOCR reader
# reader = easyocr.Reader(['en'])  # Specify the language(s) you want to recognize

# def preprocess_for_anpr(image: np.ndarray) -> np.ndarray:
#     """
#     Preprocess image for better license plate recognition
#     """
#     # Convert to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
#     # Apply bilateral filter to reduce noise while keeping edges sharp
#     blur = cv2.bilateralFilter(gray, 11, 17, 17)
    
#     # Apply thresholding to get binary image
#     _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
#     return binary

# def detect_plate_regions(image: np.ndarray) -> List[np.ndarray]:
#     """
#     Detect regions in the image that may contain license plates
#     """
#     # Preprocess the image
#     preprocessed = preprocess_for_anpr(image)
    
#     # Find contours
#     contours, _ = cv2.findContours(preprocessed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
#     # Filter contours based on area and aspect ratio
#     potential_plates = []
#     for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
#         x, y, w, h = cv2.boundingRect(contour)
#         aspect_ratio = w / float(h)
        
#         # License plates typically have an aspect ratio between 2 and 5
#         if 1.5 <= aspect_ratio <= 6.0 and w > 60 and h > 10:
#             # Extract the potential plate region with a small margin
#             margin = 10
#             x_margin = max(0, x - margin)
#             y_margin = max(0, y - margin)
#             plate_region = image[y_margin:y+h+margin, x_margin:x+w+margin]
#             potential_plates.append(plate_region)
    
#     return potential_plates

# def extract_plate_text(image: np.ndarray) -> Optional[str]:
#     """
#     Extract license plate text from an image using OCR
#     """
#     # Get potential plate regions
#     plate_regions = detect_plate_regions(image)
    
#     # Try to recognize text from each potential plate region
#     for plate_region in plate_regions:
#         # Preprocess the plate region for better OCR
#         gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
#         _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
#         # Apply OCR using EasyOCR
#         results = reader.readtext(binary)
        
#         # Extract and clean up the text
#         plate_text = ''.join([result[1] for result in results])
#         plate_text = ''.join(c for c in plate_text if c.isalnum())
        
#         # If we found text with a reasonable length, return it
#         if len(plate_text) >= 4 and len(plate_text) <= 10:
#             return plate_text
    
#     return None