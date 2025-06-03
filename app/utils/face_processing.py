import face_recognition
import numpy as np
import base64
from typing import Optional, Tuple
import cv2
import io

def encode_face_image(image_data: bytes) -> Optional[str]:
    """
    Process an image and extract face embedding.
    Returns base64 encoded face embedding or None if no face detected.
    """
    try:
        # Convert bytes to numpy array
        image_array = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        # Convert BGR to RGB (face_recognition uses RGB)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Find face locations and encodings
        face_locations = face_recognition.face_locations(rgb_image)
        if not face_locations:
            return None
        
        # Get face encodings (using the first face found)
        face_encoding = face_recognition.face_encodings(rgb_image, [face_locations[0]])[0]
        
        # Convert numpy array to base64 string for storage
        face_bytes = face_encoding.tobytes()
        face_base64 = base64.b64encode(face_bytes).decode('utf-8')
        
        return face_base64
    except Exception as e:
        print(f"Error processing face image: {str(e)}")
        return None

def decode_face_embedding(encoded_embedding: str) -> np.ndarray:
    """
    Convert a base64 encoded face embedding back to numpy array
    """
    embedding_bytes = base64.b64decode(encoded_embedding)
    return np.frombuffer(embedding_bytes, dtype=np.float64)

def compare_face_embeddings(known_embedding_str: str, query_embedding: np.ndarray, tolerance=0.6) -> bool:
    """
    Compare a stored face embedding with a query embedding
    """
    if not known_embedding_str:
        return False
        
    known_embedding = decode_face_embedding(known_embedding_str)
    # Reshape if necessary to match expected dimensions
    known_embedding = known_embedding.reshape(1, -1)
    query_embedding = query_embedding.reshape(1, -1)
    
    # Compare faces using face_recognition library
    return face_recognition.compare_faces(known_embedding, query_embedding[0], tolerance=tolerance)[0]
