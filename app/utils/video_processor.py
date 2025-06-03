# # import cv2
# # import numpy as np
# # import tempfile
# # from typing import Optional, Tuple, Dict, Any
# # import os
# # from sqlalchemy.orm import Session
# # import face_recognition
# # from .anpr import extract_plate_text
# # from .face_processing import encode_face_image, compare_face_embeddings,decode_face_embedding
# # from ..models import  User, AccessLog, UserData
# # from datetime import datetime

# # class VideoProcessor:
# #     def __init__(self, db: Session):
# #         self.db = db
# #         self.temp_dir = tempfile.mkdtemp()
    
# #     def __del__(self):
# #         # Clean up temporary directory
# #         import shutil
# #         try:
# #             shutil.rmtree(self.temp_dir)
# #         except:
# #             pass
    
# #     def save_temp_video(self, video_bytes: bytes) -> str:
# #         """Save video bytes to a temporary file and return the path"""
# #         temp_path = os.path.join(self.temp_dir, "temp_video.mp4")
# #         with open(temp_path, "wb") as f:
# #             f.write(video_bytes)
# #         return temp_path
    
# #     def process_frame(self, frame: np.ndarray) -> str:
# #         """Process a single frame to extract plate number"""
# #         return extract_plate_text(frame)
    
# #     def verify_access(self, plate_number: str) -> Tuple[bool, Dict[str, Any]]:
# #         """Verify access by checking plate number against database"""
# #         result = {
# #             "access_granted": False,
# #             "vehicle_found": False,
# #             "vehicle_info": None,
# #             "user_info": None
# #         }
        
# #         # Check if vehicle exists
# #         vehicle = self.db.query(UserData).filter(UserData.plate_number == plate_number).first()
# #         if not vehicle:
# #             return False, result
        
# #         # If vehicle is found, access is granted
# #         result["vehicle_found"] = True
# #         result["access_granted"] = True
        
# #         result["vehicle_info"] = {
# #             "id": vehicle.id,
# #             "plate_number": vehicle.plate_number,
# #             "model": vehicle.model,
# #             "color": vehicle.color
# #         }
        
# #         # Get associated user
# #         user = self.db.query(User).filter(User.id == vehicle.user_id).first()
# #         if user:
# #             result["user_info"] = {
# #                 "id": user.id,
# #                 "name": user.name,
# #                 "email": user.email
# #             }
        
# #         return result["access_granted"], result
    
# #     def process_face_image(self, image_bytes: bytes) -> Tuple[bool, float]:
# #         """Process face image and compare with database"""
# #         face_embedding = encode_face_image(image_bytes)
# #         if not face_embedding:
# #             return False, 0.0
        
# #         # Compare with all users in the database
# #         users = self.db.query(UserData).all()
# #         for user in users:
# #             if user.face_embedding and compare_face_embeddings(user.face_embedding, decode_face_embedding(face_embedding)):
# #                 return True, 0.9  # Confidence score (can be improved)
        
# #         return False, 0.0
    
# #     def process_video(self, video_bytes: bytes, image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
# #         """Process video to authenticate vehicle based on license plate and face recognition"""
# #         video_path = self.save_temp_video(video_bytes)
        
# #         cap = cv2.VideoCapture(video_path)
# #         if not cap.isOpened():
# #             return {"error": "Failed to open video file"}
        
# #         frames_processed = 0
# #         best_result = {
# #             "access_granted": False,
# #             "confidence": 0,
# #             "details": None,
# #             "all_plates": set(),  # Track all unique plates found
# #             "face_match": False,
# #             "face_confidence": 0.0
# #         }
        
# #         # Process face image if provided
# #         if image_bytes is not None:
# #             face_match, face_confidence = self.process_face_image(image_bytes)
# #             best_result["face_match"] = face_match
# #             best_result["face_confidence"] = face_confidence
        
# #         while cap.isOpened() and frames_processed < 300:  # Limit to 300 frames
# #             ret, frame = cap.read()
# #             if not ret:
# #                 break
            
# #             frames_processed += 1
# #             if frames_processed % 5 != 0:  # Process every 5th frame
# #                 continue
            
# #             try:
# #                 # Extract plate
# #                 plate_number = self.process_frame(frame)
                
# #                 if plate_number:
# #                     # Add to set of found plates
# #                     best_result["all_plates"].add(plate_number)
                    
# #                     # Verify access based on plate number
# #                     access_granted, details = self.verify_access(plate_number)
                    
# #                     # Calculate confidence based on plate recognition
# #                     confidence = 0.8 if access_granted else 0.2
                    
# #                     # Update best result if this is better
# #                     if access_granted and confidence > best_result["confidence"]:
# #                         best_result = {
# #                             "access_granted": True,
# #                             "confidence": confidence,
# #                             "details": details,
# #                             "all_plates": best_result["all_plates"],  # Maintain the set of all plates
# #                             "face_match": best_result["face_match"],
# #                             "face_confidence": best_result["face_confidence"]
# #                         }
                        
# #                         # Log access
# #                         if details["user_info"]:
# #                             self.log_access(
# #                                 details["vehicle_info"]["id"], 
# #                                 details["user_info"]["id"],
# #                                 "Granted"
# #                             )
# #                         # Do not break here to allow processing more frames for better confidence
# #             except Exception as e:
# #                 print(f"Error processing frame: {str(e)}")
# #                 continue
        
# #         cap.release()
        
# #         # Convert set to list for JSON serialization
# #         best_result["all_plates"] = list(best_result["all_plates"])
        
# #         # Log denied access if no match found
# #         if not best_result["access_granted"] and "details" in best_result and best_result["details"]:
# #             details = best_result["details"]
# #             if details["vehicle_found"] and details["user_info"]:
# #                 self.log_access(
# #                     details["vehicle_info"]["id"],
# #                     details["user_info"]["id"],
# #                     "Denied"
# #                 )
        
# #         return best_result
    
# #     def log_access(self, vehicle_id: int, user_id: int, status: str) -> None:
# #         """Log an access attempt"""
# #         new_log = AccessLog(
# #             user_id=user_id,
# #             vehicle_id=vehicle_id,
# #             entry_time=datetime.utcnow(),
# #             status=status
# #         )
# #         self.db.add(new_log)
# #         self.db.commit()











# # below code is working correctly





# import cv2
# import numpy as np
# import tempfile
# from typing import Optional, Tuple, Dict, Any
# import os
# import base64
# from sqlalchemy.orm import Session
# import face_recognition
# from .anpr import detect_license_plates  # Import the new function instead of extract_plate_text
# from .face_processing import encode_face_image, compare_face_embeddings, decode_face_embedding
# from ..models import User, AccessLog, UserData
# from datetime import datetime

# class VideoProcessor:
#     def __init__(self, db: Session):
#         self.db = db
#         self.temp_dir = tempfile.mkdtemp()
    
#     def __del__(self):
#         # Clean up temporary directory
#         import shutil
#         try:
#             shutil.rmtree(self.temp_dir)
#         except:
#             pass
    
#     def save_temp_video(self, video_bytes: bytes) -> str:
#         """Save video bytes to a temporary file and return the path"""
#         temp_path = os.path.join(self.temp_dir, "temp_video.mp4")
#         with open(temp_path, "wb") as f:
#             f.write(video_bytes)
#         return temp_path
    
#     # def process_frame(self, frame: np.ndarray) -> str:
#     #     """Process a single frame to extract plate number"""
#     #     # This will be updated to use our new function
#     #     # For single frame, we'll need to create a temporary video file
#     #     temp_frame_path = os.path.join(self.temp_dir, "temp_frame.jpg")
#     #     cv2.imwrite(temp_frame_path, frame)
        
#     #     # We'll process just this frame using our new function
#     #     # Since our detect_license_plates function expects a video,
#     #     # we need to handle this differently
        
#     #     # For now, just create a one-frame video
#     #     temp_video_path = os.path.join(self.temp_dir, "temp_one_frame.mp4")
        
#     #     # Create a video writer
#     #     height, width = frame.shape[:2]
#     #     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#     #     writer = cv2.VideoWriter(temp_video_path, fourcc, 1, (width, height))
#     #     writer.write(frame)
#     #     writer.release()
        
#     #     # Now detect plates using our new function
#     #     plates = detect_license_plates(temp_video_path)
        
#     #     # Return the first plate (highest confidence) or None
#     #     if plates:
#     #         return plates[0]
        
#     #     return None


#     def process_face_video(self, face_video_bytes: bytes) -> Tuple[bool, float, Optional[str]]:
#         """Process face video and extract the best face embedding for comparison"""
#         if not face_video_bytes:
#             return False, 0.0, None
            
#         # Save face video to temp file
#         face_video_path = os.path.join(self.temp_dir, "temp_face_video.mp4")
#         with open(face_video_path, "wb") as f:
#             f.write(face_video_bytes)
        
#         # Open video
#         cap = cv2.VideoCapture(face_video_path)
#         if not cap.isOpened():
#             return False, 0.0, None
        
#         best_face_embedding = None
#         best_confidence = 0.0
#         face_match = False
        
#         # Process frames from the face video
#         frames_processed = 0
#         while cap.isOpened() and frames_processed < 100:  # Limit to 100 frames
#             ret, frame = cap.read()
#             if not ret:
#                 break
                
#             frames_processed += 1
#             if frames_processed % 3 != 0:  # Process every 3rd frame
#                 continue
            
#             try:
#                 # Convert BGR to RGB
#                 rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
#                 # Detect faces
#                 face_locations = face_recognition.face_locations(rgb_frame)
#                 if not face_locations:
#                     continue
                    
#                 # Get face encoding
#                 face_encoding = face_recognition.face_encodings(rgb_frame, [face_locations[0]])[0]
#                 face_bytes = face_encoding.tobytes()
#                 face_embedding = base64.b64encode(face_bytes).decode('utf-8')
                
#                 # Compare with database
#                 current_match, current_confidence = self.process_face_embedding(face_embedding)
                
#                 # Update best result if better
#                 if current_match and current_confidence > best_confidence:
#                     best_confidence = current_confidence
#                     best_face_embedding = face_embedding
#                     face_match = True
                    
#             except Exception as e:
#                 print(f"Error processing face frame: {str(e)}")
#                 continue
        
#         cap.release()
#         return face_match, best_confidence, best_face_embedding


#     def process_frame(self, frame: np.ndarray) -> Tuple[str, Optional[str]]:
#         """Process a single frame to extract plate number and face embedding"""
#         # Extract plate number
#         temp_frame_path = os.path.join(self.temp_dir, "temp_frame.jpg")
#         cv2.imwrite(temp_frame_path, frame)
        
#         # We'll process just this frame using our new function
#         # Since our detect_license_plates function expects a video,
#         # we need to handle this differently
        
#         # For now, just create a one-frame video
#         temp_video_path = os.path.join(self.temp_dir, "temp_one_frame.mp4")
        
#         # Create a video writer
#         height, width = frame.shape[:2]
#         fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#         writer = cv2.VideoWriter(temp_video_path, fourcc, 1, (width, height))
#         writer.write(frame)
#         writer.release()
        
#         # Now detect plates using our new function
#         plates = detect_license_plates(temp_video_path)
        
#         # Return the first plate (highest confidence) or None
#         plate_number = plates[0] if plates else None
        
#         # Extract face embedding
#         face_embedding = encode_face_image(frame.tobytes())
        
#         return plate_number, face_embedding
    
#     def verify_access(self, plate_number: str) -> Tuple[bool, Dict[str, Any]]:
#         """Verify access by checking plate number against database"""
#         result = {
#             "access_granted": False,
#             "vehicle_found": False,
#             "vehicle_info": None,
#             "user_info": None
#         }
        
#         # Check if vehicle exists
#         vehicle = self.db.query(UserData).filter(UserData.plate_number == plate_number).first()
#         if not vehicle:
#             return False, result
        
#         # If vehicle is found, access is granted
#         result["vehicle_found"] = True
#         result["access_granted"] = True
        
#         result["vehicle_info"] = {
#             "id": vehicle.id,
#             "plate_number": vehicle.plate_number,
#             "model": vehicle.model,
#             "color": vehicle.color
#         }
        
#         # Get associated user
#         user = self.db.query(User).filter(User.id == vehicle.user_id).first()
#         if user:
#             result["user_info"] = {
#                 "id": user.id,
#                 "name": user.name,
#                 "email": user.email
#             }
        
#         return result["access_granted"], result
    
#     # def process_face_image(self, image_bytes: bytes) -> Tuple[bool, float]:
#     #     """Process face image and compare with database"""
#     #     face_embedding = encode_face_image(image_bytes)
#     #     if not face_embedding:
#     #         return False, 0.0
        
#     #     # Compare with all users in the database
#     #     users = self.db.query(UserData).all()
#     #     for user in users:
#     #         if user.face_embedding and compare_face_embeddings(user.face_embedding, decode_face_embedding(face_embedding)):
#     #             return True, 0.9  # Confidence score (can be improved)
        
#     #     return False, 0.0

#     def process_face_embedding(self, face_embedding: Optional[str]) -> Tuple[bool, float]:
#         """Process face embedding and compare with database"""
#         if not face_embedding:
#             return False, 0.0
        
#         # Compare with all users in the database
#         users = self.db.query(UserData).all()
#         best_confidence = 0.0
#         face_match = False
        
#         for user in users:
#             if user.face_embedding:
#                 # Get comparison result and similarity score
#                 is_match = compare_face_embeddings(user.face_embedding, decode_face_embedding(face_embedding))
#                 if is_match:
#                     face_match = True
#                     # Calculate a confidence score (this is simplified, you might want to use actual distance metrics)
#                     confidence = 0.9  # Using a fixed value for now, but could be improved
#                     if confidence > best_confidence:
#                         best_confidence = confidence
        
#         return face_match, best_confidence
    

    
#     # def process_video(self, video_bytes: bytes, image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
#     #     """Process video to authenticate vehicle based on license plate and face recognition"""
#     #     video_path = self.save_temp_video(video_bytes)
        
#     #     # Directly use the detect_license_plates function for the whole video
#     #     plates = detect_license_plates(video_path)
        
#     #     best_result = {
#     #         "access_granted": False,
#     #         "confidence": 0,
#     #         "details": None,
#     #         "all_plates": set(plates),  # Use all unique plates found
#     #         "face_match": False,
#     #         "face_confidence": 0.0
#     #     }
        
#     #     # Process face image if provided
#     #     if image_bytes is not None:
#     #         face_match, face_confidence = self.process_face_image(image_bytes)
#     #         best_result["face_match"] = face_match
#     #         best_result["face_confidence"] = face_confidence
        
#     #     # Process each detected plate to find the best match
#     #     for plate_number in plates:
#     #         try:
#     #             # Verify access based on plate number
#     #             access_granted, details = self.verify_access(plate_number)
                
#     #             # Calculate confidence (simplified for now)
#     #             confidence = 0.8 if access_granted else 0.2
                
#     #             # Update best result if this is better
#     #             if access_granted and confidence > best_result["confidence"]:
#     #                 best_result = {
#     #                     "access_granted": True,
#     #                     "confidence": confidence,
#     #                     "details": details,
#     #                     "all_plates": best_result["all_plates"],  # Maintain the set of all plates
#     #                     "face_match": best_result["face_match"],
#     #                     "face_confidence": best_result["face_confidence"]
#     #                 }
                    
#     #                 # Log access
#     #                 if details["user_info"]:
#     #                     self.log_access(
#     #                         details["vehicle_info"]["id"], 
#     #                         details["user_info"]["id"],
#     #                         "Granted"
#     #                     )
#     #         except Exception as e:
#     #             print(f"Error processing plate {plate_number}: {str(e)}")
#     #             continue
        
#     #     # Convert set to list for JSON serialization
#     #     best_result["all_plates"] = list(best_result["all_plates"])
        
#     #     # Log denied access if no match found
#     #     if not best_result["access_granted"] and "details" in best_result and best_result["details"]:
#     #         details = best_result["details"]
#     #         if details["vehicle_found"] and details["user_info"]:
#     #             self.log_access(
#     #                 details["vehicle_info"]["id"],
#     #                 details["user_info"]["id"],
#     #                 "Denied"
#     #             )
        
#     #     return best_result



#     def process_video(self, gate_video_bytes: bytes, face_video_bytes: Optional[bytes] = None) -> Dict[str, Any]:
#         """Process video to authenticate vehicle based on license plate and face recognition"""
#         video_path = self.save_temp_video(gate_video_bytes)
        
#         # Directly use the detect_license_plates function for the whole video
#         plates = detect_license_plates(video_path)
        
#         best_result = {
#             "access_granted": False,
#             "confidence": 0,
#             "details": None,
#             "all_plates": set(plates),  # Use all unique plates found
#             "face_match": False,
#             "face_confidence": 0.0
#         }
        
#         # Process face video if provided
#         if face_video_bytes is not None:
#             face_match, face_confidence, _ = self.process_face_video(face_video_bytes)
#             best_result["face_match"] = face_match
#             best_result["face_confidence"] = face_confidence
        
#         # Process each detected plate to find the best match
#         for plate_number in plates:
#             try:
#                 # Verify access based on plate number
#                 access_granted, details = self.verify_access(plate_number)
                
#                 # Calculate confidence based on plate recognition and face recognition
#                 plate_confidence = 0.8 if access_granted else 0.2
                
#                 # Add extra confidence if face is also recognized
#                 final_confidence = plate_confidence
#                 if best_result["face_match"]:
#                     final_confidence = (plate_confidence + best_result["face_confidence"]) / 2
                
#                 # Update best result if this is better
#                 if access_granted and final_confidence > best_result["confidence"]:
#                     best_result = {
#                         "access_granted": True,
#                         "confidence": final_confidence,
#                         "details": details,
#                         "all_plates": best_result["all_plates"],  # Maintain the set of all plates
#                         "face_match": best_result["face_match"],
#                         "face_confidence": best_result["face_confidence"]
#                     }
                    
#                     # Log access
#                     if details["user_info"]:
#                         self.log_access(
#                             details["vehicle_info"]["id"], 
#                             details["user_info"]["id"],
#                             "Granted"
#                         )
#             except Exception as e:
#                 print(f"Error processing plate {plate_number}: {str(e)}")
#                 continue
        
#         # Convert set to list for JSON serialization
#         best_result["all_plates"] = list(best_result["all_plates"])
        
#         # Log denied access if no match found
#         if not best_result["access_granted"] and "details" in best_result and best_result["details"]:
#             details = best_result["details"]
#             if details["vehicle_found"] and details["user_info"]:
#                 self.log_access(
#                     details["vehicle_info"]["id"],
#                     details["user_info"]["id"],
#                     "Denied"
#                 )
        
#         return best_result


#     def log_access(self, vehicle_id: int, user_id: int, status: str) -> None:
#         """Log an access attempt"""
#         new_log = AccessLog(
#             user_id=user_id,
#             vehicle_id=vehicle_id,  # This now correctly maps to the renamed field
#             entry_time=datetime.utcnow(),
#             status=status
#         )
#         self.db.add(new_log)
#         self.db.commit()

    


# import cv2
# import numpy as np
# import tempfile
# from typing import Optional, Tuple, Dict, Any
# import os
# import base64
# from sqlalchemy.orm import Session
# import face_recognition
# from .anpr import detect_license_plates
# from .face_processing import encode_face_image, compare_face_embeddings, decode_face_embedding
# from ..models import User, AccessLog, UserData
# from datetime import datetime

# class VideoProcessor:
#     def __init__(self, db: Session):
#         self.db = db
#         self.temp_dir = tempfile.mkdtemp()
    
#     def __del__(self):
#         # Clean up temporary directory
#         import shutil
#         try:
#             shutil.rmtree(self.temp_dir)
#         except:
#             pass
    
#     def save_temp_video(self, video_bytes: bytes) -> str:
#         """Save video bytes to a temporary file and return the path"""
#         temp_path = os.path.join(self.temp_dir, "temp_video.mp4")
#         with open(temp_path, "wb") as f:
#             f.write(video_bytes)
#         return temp_path
    
#     def process_frame(self, frame: np.ndarray) -> Tuple[str, Optional[str]]:
#         """Process a single frame to extract plate number and face embedding"""
#         # Extract plate number
#         temp_frame_path = os.path.join(self.temp_dir, "temp_frame.jpg")
#         cv2.imwrite(temp_frame_path, frame)
        
#         # Create a one-frame video
#         temp_video_path = os.path.join(self.temp_dir, "temp_one_frame.mp4")
        
#         # Create a video writer
#         height, width = frame.shape[:2]
#         fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#         writer = cv2.VideoWriter(temp_video_path, fourcc, 1, (width, height))
#         writer.write(frame)
#         writer.release()
        
#         # Now detect plates using our function
#         plates = detect_license_plates(temp_video_path)
        
#         # Return the first plate (highest confidence) or None
#         plate_number = plates[0] if plates else None
        
#         # Extract face embedding
#         face_embedding = encode_face_image(frame.tobytes())
        
#         return plate_number, face_embedding

#     def process_face_video(self, face_video_bytes: bytes) -> Tuple[bool, float, Optional[str], Optional[int]]:
#         """Process face video and extract the best face embedding for comparison"""
#         if not face_video_bytes:
#             return False, 0.0, None, None
            
#         # Save face video to temp file
#         face_video_path = os.path.join(self.temp_dir, "temp_face_video.mp4")
#         with open(face_video_path, "wb") as f:
#             f.write(face_video_bytes)
        
#         # Open video
#         cap = cv2.VideoCapture(face_video_path)
#         if not cap.isOpened():
#             return False, 0.0, None, None
        
#         best_face_embedding = None
#         best_confidence = 0.0
#         face_match = False
#         matched_user_id = None
        
#         # Process frames from the face video
#         frames_processed = 0
#         while cap.isOpened() and frames_processed < 100:  # Limit to 100 frames
#             ret, frame = cap.read()
#             if not ret:
#                 break
                
#             frames_processed += 1
#             if frames_processed % 3 != 0:  # Process every 3rd frame
#                 continue
            
#             try:
#                 # Convert BGR to RGB
#                 rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
#                 # Detect faces
#                 face_locations = face_recognition.face_locations(rgb_frame)
#                 if not face_locations:
#                     continue
                    
#                 # Get face encoding
#                 face_encoding = face_recognition.face_encodings(rgb_frame, [face_locations[0]])[0]
#                 face_bytes = face_encoding.tobytes()
#                 face_embedding = base64.b64encode(face_bytes).decode('utf-8')
                
#                 # Compare with database
#                 current_match, current_confidence, current_user_id = self.process_face_embedding(face_embedding)
                
#                 # Update best result if better
#                 if current_match and current_confidence > best_confidence:
#                     best_confidence = current_confidence
#                     best_face_embedding = face_embedding
#                     face_match = True
#                     matched_user_id = current_user_id
                    
#             except Exception as e:
#                 print(f"Error processing face frame: {str(e)}")
#                 continue
        
#         cap.release()
#         return face_match, best_confidence, best_face_embedding, matched_user_id
    
#     def verify_access(self, plate_number: str) -> Tuple[bool, Dict[str, Any]]:
#         """Verify access by checking plate number against database"""
#         result = {
#             "access_granted": False,
#             "vehicle_found": False,
#             "vehicle_info": None,
#             "user_info": None,
#             "user_id": None,
#             "vehicle_id": None
#         }
        
#         # Check if vehicle exists in UserData table
#         vehicle = self.db.query(UserData).filter(UserData.plate_number == plate_number).first()
#         if not vehicle:
#             return False, result
        
#         # If vehicle is found, access could be granted (depends on face match too)
#         result["vehicle_found"] = True
#         result["access_granted"] = True  # This will be combined with face match later
#         result["vehicle_id"] = vehicle.id  # Important for logging
#         result["user_id"] = vehicle.user_id  # Important for logging
        
#         result["vehicle_info"] = {
#             "id": vehicle.id,
#             "plate_number": vehicle.plate_number,
#             "model": vehicle.model,
#             "color": vehicle.color
#         }
        
#         # Get associated user
#         user = self.db.query(User).filter(User.id == vehicle.user_id).first()
#         if user:
#             result["user_info"] = {
#                 "id": user.id,
#                 "name": user.name,
#                 "email": user.email
#             }
        
#         return result["access_granted"], result

#     def process_face_embedding(self, face_embedding: Optional[str]) -> Tuple[bool, float, Optional[int]]:
#         """Process face embedding and compare with database - returns match status, confidence, and user_id"""
#         if not face_embedding:
#             return False, 0.0, None
        
#         # Compare with all users in the database
#         users = self.db.query(UserData).all()
#         best_confidence = 0.0
#         face_match = False
#         matched_user_id = None
        
#         for user in users:
#             if user.face_embedding:
#                 # Get comparison result and similarity score
#                 is_match = compare_face_embeddings(user.face_embedding, decode_face_embedding(face_embedding))
#                 if is_match:
#                     face_match = True
#                     # Calculate a confidence score
#                     confidence = 0.9  # Using a fixed value for now
#                     if confidence > best_confidence:
#                         best_confidence = confidence
#                         matched_user_id = user.user_id  # Store the user_id of the matched face
        
#         return face_match, best_confidence, matched_user_id
    
#     def process_video(self, gate_video_bytes: bytes, face_video_bytes: Optional[bytes] = None) -> Dict[str, Any]:
#         """Process video to authenticate vehicle based on license plate and face recognition"""
#         video_path = self.save_temp_video(gate_video_bytes)
        
#         # Detect license plates from the video
#         plates = detect_license_plates(video_path)
        
#         # Initialize result structure
#         result = {
#             "access_granted": False,
#             "plate_match": False,  # Specific flag for plate matching
#             "confidence": 0,
#             "details": None,
#             "all_plates": list(set(plates)),
#             "face_match": False,
#             "face_confidence": 0.0,
#             "user_id": None,
#             "vehicle_id": None
#         }
        
#         # Process face video if provided
#         matched_face_user_id = None
#         if face_video_bytes is not None:
#             face_match, face_confidence, _, matched_face_user_id = self.process_face_video(face_video_bytes)
#             result["face_match"] = face_match
#             result["face_confidence"] = face_confidence
        
#         # Process each detected plate to find the best match
#         best_plate_match = None
#         best_confidence = 0
        
#         for plate_number in plates:
#             try:
#                 # Verify access based on plate number
#                 access_granted, details = self.verify_access(plate_number)
                
#                 if access_granted:
#                     # Calculate confidence based on plate recognition
#                     plate_confidence = 0.85  # Fixed confidence for now
                    
#                     # Update best result if this is better
#                     if plate_confidence > best_confidence:
#                         best_confidence = plate_confidence
#                         best_plate_match = details
#                         result["plate_match"] = True
#                         result["vehicle_id"] = details["vehicle_id"]
#                         result["user_id"] = details["user_id"]
                        
#                         # Update details in result
#                         result["details"] = details
#                         result["confidence"] = plate_confidence
                        
#                         # Store plate info for access log
#                         plate_user_id = details["user_id"]
#                         plate_vehicle_id = details["vehicle_id"]
#             except Exception as e:
#                 print(f"Error processing plate {plate_number}: {str(e)}")
#                 continue
        
#         # Final access decision - requires BOTH plate and face match
#         result["access_granted"] = result["plate_match"] and result["face_match"]
        
#         # Ensure the face match is for the same user as the plate match
#         if result["plate_match"] and result["face_match"]:
#             plate_user_id = result["user_id"]
#             # Check if the matched face belongs to the same user as the plate
#             if matched_face_user_id and matched_face_user_id != plate_user_id:
#                 # Face doesn't match the owner of the vehicle
#                 result["access_granted"] = False
#                 result["face_mismatch"] = True
        
#         # # Log the access attempt if we have both user_id and vehicle_id
#         # if result["user_id"] and result["vehicle_id"]:
#         #     status = "Granted" if result["access_granted"] else "Denied"
#         #     self.log_access(
#         #         result["vehicle_id"],
#         #         result["user_id"],
#         #         status
#         #     )
        
#         return result

#     def log_access(self, vehicle_id: int, user_id: int, status: str) -> None:
#         """Log an access attempt"""
#         new_log = AccessLog(
#             user_id=user_id,
#             vehicle_id=vehicle_id,
#             entry_time=datetime.utcnow(),
#             status=status
#         )
#         self.db.add(new_log)
#         self.db.commit()



# ////////////////////////////////////////////////

import cv2
import numpy as np
import tempfile
from typing import Optional, Tuple, Dict, Any
import os
import base64
from sqlalchemy.orm import Session
import face_recognition
from .anpr import detect_license_plates
from .face_processing import encode_face_image, compare_face_embeddings, decode_face_embedding
from ..models import User, AccessLog, UserData
from datetime import datetime
from sqlalchemy import or_, and_

class VideoProcessor:
    def __init__(self, db: Session):
        self.db = db
        self.temp_dir = tempfile.mkdtemp()
    
    def __del__(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def save_temp_video(self, video_bytes: bytes) -> str:
        temp_path = os.path.join(self.temp_dir, "temp_video.mp4")
        with open(temp_path, "wb") as f:
            f.write(video_bytes)
        return temp_path
    
    def process_frame(self, frame: np.ndarray) -> Tuple[str, Optional[str]]:
        temp_frame_path = os.path.join(self.temp_dir, "temp_frame.jpg")
        cv2.imwrite(temp_frame_path, frame)
        
        temp_video_path = os.path.join(self.temp_dir, "temp_one_frame.mp4")
        height, width = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(temp_video_path, fourcc, 1, (width, height))
        writer.write(frame)
        writer.release()
        
        plates = detect_license_plates(temp_video_path)
        plate_number = plates[0] if plates else None
        
        face_embedding = encode_face_image(frame.tobytes())
        
        return plate_number, face_embedding

    def process_face_video(self, face_video_bytes: bytes) -> Tuple[bool, float, Optional[str], Optional[int]]:
        if not face_video_bytes:
            return False, 0.0, None, None
            
        face_video_path = os.path.join(self.temp_dir, "temp_face_video.mp4")
        with open(face_video_path, "wb") as f:
            f.write(face_video_bytes)
        
        cap = cv2.VideoCapture(face_video_path)
        if not cap.isOpened():
            return False, 0.0, None, None
        
        best_face_embedding = None
        best_confidence = 0.0
        face_match = False
        matched_user_id = None
        frames_processed = 0
        
        while cap.isOpened() and frames_processed < 100:
            ret, frame = cap.read()
            if not ret:
                break
            frames_processed += 1
            if frames_processed % 3 != 0:
                continue
            
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                if not face_locations:
                    continue
                face_encoding = face_recognition.face_encodings(rgb_frame, [face_locations[0]])[0]
                face_bytes = face_encoding.tobytes()
                face_embedding = base64.b64encode(face_bytes).decode('utf-8')
                
                current_match, current_confidence, current_user_id = self.process_face_embedding(face_embedding)
                
                if current_match and current_confidence > best_confidence:
                    best_confidence = current_confidence
                    best_face_embedding = face_embedding
                    face_match = True
                    matched_user_id = current_user_id
            except Exception as e:
                print(f"Error processing face frame: {str(e)}")
                continue
        
        cap.release()
        return face_match, best_confidence, best_face_embedding, matched_user_id
    
    def verify_access(self, plate_number: str) -> Tuple[bool, Dict[str, Any]]:
        result = {
            "access_granted": False,
            "vehicle_found": False,
            "vehicle_info": None,
            "user_info": None,
            "user_id": None,
            "plate_number": None
        }
        
        vehicle = self.db.query(UserData).filter(UserData.plate_number == plate_number).first()
        if not vehicle:
            return False, result
        
        result["vehicle_found"] = True
        result["access_granted"] = True
        result["plate_number"] = vehicle.plate_number
        result["user_id"] = vehicle.user_id
        
        result["vehicle_info"] = {
            "plate_number": vehicle.plate_number,
            "model": vehicle.model,
            "color": vehicle.color
        }        
        user = self.db.query(User).filter(User.id == vehicle.user_id).first()
        if user:
            result["user_info"] = {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        
        return result["access_granted"], result

    def process_face_embedding(self, face_embedding: Optional[str]) -> Tuple[bool, float, Optional[int]]:
        if not face_embedding:
            return False, 0.0, None
        
        users = self.db.query(UserData).all()
        best_confidence = 0.0
        face_match = False
        matched_user_id = None
        
        for user in users:
            if user.face_embedding:
                is_match = compare_face_embeddings(user.face_embedding, decode_face_embedding(face_embedding))
                if is_match:
                    face_match = True
                    confidence = 0.9
                    if confidence > best_confidence:
                        best_confidence = confidence
                        matched_user_id = user.user_id
        
        return face_match, best_confidence, matched_user_id
    
    # def process_video(self, gate_video_bytes: bytes, face_video_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    #     video_path = self.save_temp_video(gate_video_bytes)
    #     plates = detect_license_plates(video_path)
        
    #     result = {
    #         "access_granted": False,
    #         "plate_match": False,
    #         "confidence": 0,
    #         "details": None,
    #         "all_plates": list(set(plates)),
    #         "face_match": False,
    #         "face_confidence": 0.0,
    #         "user_id": None,
    #         "plate_number": None
    #     }
        
    #     matched_face_user_id = None
    #     if face_video_bytes is not None:
    #         face_match, face_confidence, _, matched_face_user_id = self.process_face_video(face_video_bytes)
    #         result["face_match"] = face_match
    #         result["face_confidence"] = face_confidence
        
    #     best_plate_match = None
    #     best_confidence = 0
        
    #     for plate_number in plates:
    #         try:
    #             access_granted, details = self.verify_access(plate_number)
    #             if access_granted:
    #                 plate_confidence = 0.85
                    
    #                 if plate_confidence > best_confidence:
    #                     best_confidence = plate_confidence
    #                     best_plate_match = details
    #                     result["plate_match"] = True
    #                     result["plate_number"] = details["plate_number"]
    #                     result["user_id"] = details["user_id"]
    #                     result["details"] = details
    #                     result["confidence"] = plate_confidence
    #         except Exception as e:
    #             print(f"Error processing plate {plate_number}: {str(e)}")
    #             continue
        
    #     result["access_granted"] = result["plate_match"] and result["face_match"]
        
    #     if result["plate_match"] and result["face_match"]:
    #         plate_user_id = result["user_id"]
    #         if matched_face_user_id and matched_face_user_id != plate_user_id:
    #             result["access_granted"] = False
    #             result["face_mismatch"] = True
        
    #     # Uncomment to log access attempts:
    #     # if result["user_id"] and result["plate_number"]:
    #     #     status = "Granted" if result["access_granted"] else "Denied"
    #     #     self.log_access(
    #     #         plate_number=result["plate_number"],
    #     #         user_id=result["user_id"],
    #     #         status=status
    #     #     )
        
    #     return result

    # def process_video(self, gate_video_bytes: bytes, face_video_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    #         video_path = self.save_temp_video(gate_video_bytes)
    #         plates = detect_license_plates(video_path)
            
    #         result = {
    #             "access_granted": False,
    #             "plate_match": False,
    #             "confidence": 0,
    #             "details": None,
    #             "all_plates": list(set(plates)),
    #             "face_match": False,
    #             "face_confidence": 0.0,
    #             "user_id": None,
    #             "plate_number": None
    #         }
            
    #         matched_face_user_id = None
    #         if face_video_bytes is not None:
    #             face_match, face_confidence, _, matched_face_user_id = self.process_face_video(face_video_bytes)
    #             result["face_match"] = face_match
    #             result["face_confidence"] = face_confidence
            
    #         best_plate_match = None
    #         best_confidence = 0
    #         detected_plate = None  # Track the best detected plate regardless of access
            
    #         for plate_number in plates:
    #             try:
    #                 access_granted, details = self.verify_access(plate_number)
                    
    #                 # Always store the first detected plate as fallback
    #                 if detected_plate is None:
    #                     detected_plate = plate_number
                    
    #                 if access_granted:
    #                     plate_confidence = 0.85
                        
    #                     if plate_confidence > best_confidence:
    #                         best_confidence = plate_confidence
    #                         best_plate_match = details
    #                         result["plate_match"] = True
    #                         result["plate_number"] = details["plate_number"]
    #                         result["user_id"] = details["user_id"]
    #                         result["details"] = details
    #                         result["confidence"] = plate_confidence
    #                         detected_plate = plate_number  # Update with matched plate
    #             except Exception as e:
    #                 print(f"Error processing plate {plate_number}: {str(e)}")
    #                 continue
            
    #         # If no plate matched but we detected plates, use the first detected one
    #         if not result["plate_match"] and detected_plate:
    #             result["plate_number"] = detected_plate
    #             # Create minimal details for unrecognized plate
    #             result["details"] = {
    #                 "plate_number": detected_plate,
    #                 "vehicle_info": {
    #                     "plate_number": detected_plate,
    #                     "model": "Unknown",
    #                     "color": "Unknown"
    #                 },
    #                 "user_info": {
    #                     "name": "Unknown",
    #                     "email": "Unknown"
    #                 }
    #             }
            
    #         result["access_granted"] = result["plate_match"] and result["face_match"]
            
    #         if result["plate_match"] and result["face_match"]:
    #             plate_user_id = result["user_id"]
    #             if matched_face_user_id and matched_face_user_id != plate_user_id:
    #                 result["access_granted"] = False
    #                 result["face_mismatch"] = True
            
    #         # Log access attempts for any detected plate
    #         if result["plate_number"]:
    #             status = "Granted" if result["access_granted"] else "Denied"
    #             self.log_access(
    #                 plate_number=result["plate_number"],
    #                 user_id=result["user_id"],  # This can be None for unrecognized plates
    #                 status=status
    #             )
            
    #         return result


    def process_video(self, gate_video_bytes: bytes, face_video_bytes: Optional[bytes] = None) -> Dict[str, Any]:
                video_path = self.save_temp_video(gate_video_bytes)
                plates = detect_license_plates(video_path)
                
                result = {
                    "access_granted": False,
                    "plate_match": False,
                    "confidence": 0,
                    "details": None,
                    "all_plates": list(set(plates)),
                    "face_match": False,
                    "face_confidence": 0.0,
                    "user_id": None,
                    "plate_number": None
                }
                
                matched_face_user_id = None
                if face_video_bytes is not None:
                    face_match, face_confidence, _, matched_face_user_id = self.process_face_video(face_video_bytes)
                    result["face_match"] = face_match
                    result["face_confidence"] = face_confidence
                
                best_plate_match = None
                best_confidence = 0
                detected_plate = None  # Track the best detected plate regardless of access
                
                for plate_number in plates:
                    try:
                        access_granted, details = self.verify_access(plate_number)
                        
                        # Always store the first detected plate as fallback
                        if detected_plate is None:
                            detected_plate = plate_number
                        
                        if access_granted:
                            plate_confidence = 0.85
                            
                            if plate_confidence > best_confidence:
                                best_confidence = plate_confidence
                                best_plate_match = details
                                result["plate_match"] = True
                                result["plate_number"] = details["plate_number"]
                                result["user_id"] = details["user_id"]
                                result["details"] = details
                                result["confidence"] = plate_confidence
                                detected_plate = plate_number  # Update with matched plate
                    except Exception as e:
                        print(f"Error processing plate {plate_number}: {str(e)}")
                        continue
                
                # If no plate matched but we detected plates, use the first detected one
                if not result["plate_match"] and detected_plate:
                    result["plate_number"] = detected_plate
                    # Create minimal details for unrecognized plate
                    result["details"] = {
                        "plate_number": detected_plate,
                        "vehicle_info": {
                            "plate_number": detected_plate,
                            "model": "Unknown",
                            "color": "Unknown"
                        },
                        "user_info": {
                            "name": "Unknown",
                            "email": "Unknown"
                        }
                    }
                
                result["access_granted"] = result["plate_match"] and result["face_match"]
                
                if result["plate_match"] and result["face_match"]:
                    plate_user_id = result["user_id"]
                    if matched_face_user_id and matched_face_user_id != plate_user_id:
                        result["access_granted"] = False
                        result["face_mismatch"] = True
                
                # IMPORTANT: Log access attempts for any detected plate
                # Only log if we actually detected a plate
                if result["plate_number"]:
                    status = "Granted" if result["access_granted"] else "Denied"
                    
                    # Add debug logging to track calls
                    print(f"LOGGING ACCESS: plate={result['plate_number']}, user_id={result['user_id']}, status={status}")
                    
                    try:
                        self.log_access(
                            plate_number=result["plate_number"],
                            user_id=result["user_id"],  # This can be None for unrecognized plates
                            status=status
                        )
                    except Exception as e:
                        print(f"Error logging access: {str(e)}")
                else:
                    print("No plate detected - skipping access log")
                
                return result
    # def log_access(self, plate_number: str, user_id: int, status: str) -> None:
    #     new_log = AccessLog(
    #         user_id=user_id,
    #         plate_number=plate_number,
    #         entry_time=datetime.utcnow(),
    #         status=status
    #     )
    #     self.db.add(new_log)
    #     self.db.commit()
    # def log_access(self, plate_number: str, user_id: Optional[int], status: str) -> None:
    #         """Log access attempt, even for unrecognized plates/users"""
    #         new_log = AccessLog(
    #             user_id=user_id,  # Can be None for unrecognized users
    #             plate_number=plate_number,
    #             entry_time=datetime.utcnow(),
    #             status=status
    #         )
    #         self.db.add(new_log)
    #         self.db.commit()

    # def log_access(self, plate_number: str, user_id: Optional[int], status: str) -> None:
    #         """Log access attempt - handles both recognized and unrecognized plates"""
            
    #         # Check if plate exists in userdata table
    #         existing_plate = self.db.query(UserData).filter(UserData.plate_number == plate_number).first()
            
    #         if existing_plate:
    #             # Log recognized plates using the FK-constrained field
    #             new_log = AccessLog(
    #                 user_id=user_id,
    #                 plate_number=plate_number,  # This will satisfy FK constraint
    #                 unrecognized_plate=None,
    #                 entry_time=datetime.utcnow(),
    #                 status=status
    #             )
    #         else:
    #             # Log unrecognized plates in the separate field
    #             new_log = AccessLog(
    #                 user_id=None,  # No user for unrecognized plates
    #                 plate_number=None,  # Leave FK field empty
    #                 unrecognized_plate=plate_number,  # Store in non-FK field
    #                 entry_time=datetime.utcnow(),
    #                 status=status
    #             )
            
    #         self.db.add(new_log)
    #         self.db.commit()
    def log_access(self, plate_number: str, user_id: Optional[int], status: str) -> None:
            """Log access attempt - handles both recognized and unrecognized plates"""
            
            print(f"log_access called with: plate_number={plate_number}, user_id={user_id}, status={status}")
            
            # Add duplicate prevention - check for recent identical entry
            from datetime import timedelta
            one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
            
            # Check for recent duplicate entry for the same plate and status
            existing_recent_log = self.db.query(AccessLog).filter(
                or_(
                    and_(AccessLog.plate_number == plate_number),
                    and_(AccessLog.unrecognized_plate == plate_number)
                ),
                AccessLog.status == status,
                AccessLog.entry_time >= one_minute_ago
            ).first()
            
            if existing_recent_log:
                print(f"Duplicate log prevented for plate {plate_number} with status {status}")
                return
            
            # Check if plate exists in userdata table
            existing_plate = self.db.query(UserData).filter(UserData.plate_number == plate_number).first()
            
            if existing_plate:
                # Log recognized plates using the FK-constrained field
                new_log = AccessLog(
                    user_id=user_id,
                    plate_number=plate_number,  # This will satisfy FK constraint
                    unrecognized_plate=None,
                    entry_time=datetime.utcnow(),
                    status=status
                )
                print(f"Logging recognized plate: {plate_number}")
            else:
                # Log unrecognized plates in the separate field
                new_log = AccessLog(
                    user_id=None,  # No user for unrecognized plates
                    plate_number=None,  # Leave FK field empty
                    unrecognized_plate=plate_number,  # Store in non-FK field
                    entry_time=datetime.utcnow(),
                    status=status
                )
                print(f"Logging unrecognized plate: {plate_number}")
            
            try:
                self.db.add(new_log)
                self.db.commit()
                print(f"Successfully logged access for plate: {plate_number}")
            except Exception as e:
                self.db.rollback()
                print(f"Failed to log access: {str(e)}")
                raise



