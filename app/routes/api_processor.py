from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..utils.video_processor import VideoProcessor
import logging

router = APIRouter()

@router.post("/process-gate-video")
async def process_gate_video(
    gate_video: UploadFile = File(...),
    face_video: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    allowed_video_types = {'video/mp4', 'video/avi', 'video/quicktime'}
    if gate_video.content_type not in allowed_video_types:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Invalid video file type. Allowed types: {', '.join(allowed_video_types)}"}
        )
    
    if face_video is not None:
        if face_video.content_type not in allowed_video_types:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid face video file type. Allowed types: {', '.join(allowed_video_types)}"}
            )
    
    try:
        gate_video_bytes = await gate_video.read()
        
        if not gate_video_bytes:
            return JSONResponse(
                status_code=400,
                content={"detail": "Empty gate video file"}
            )
            
        face_video_bytes = None
        if face_video is not None:
            face_video_bytes = await face_video.read()
            
            if not face_video_bytes:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Empty face video file"}
                )
        
        processor = VideoProcessor(db)
        result = processor.process_video(gate_video_bytes, face_video_bytes)
        
        if "error" in result:
            return JSONResponse(
                status_code=400,
                content={"detail": result["error"]}
            )
        
        result["access_granted"] = result.get("plate_match", False) and result.get("face_match", False)
        
        response = {
            "all_plates": result.get("all_plates", []),
            "access_granted": result.get("access_granted", False),
            "plate_match": result.get("plate_match", False),
            "face_match": result.get("face_match", False),
            "confidence": result.get("confidence", 0),
            "face_confidence": result.get("face_confidence", 0),
            "user_id": result.get("user_id"), 
            "plate_number": result.get("plate_number") 
          }
    
        
        return JSONResponse(content=response)
        plate_number = result.get("plate_number")
        details = result.get("details", {})

        response["details"] = {
            "vehicle_info": {
                "plate_number": plate_number or "N/A",
                "model": details.get("vehicle_info", {}).get("model", "N/A"),
                "color": details.get("vehicle_info", {}).get("color", "N/A")
            },
            "user_info": {
                "name": details.get("user_info", {}).get("name", "N/A"),
                "email": details.get("user_info", {}).get("email", "N/A")
            }
        }
    except Exception as e:
        logging.error(f"Gate video processing error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error during video processing: {str(e)}"}
        )