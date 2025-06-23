from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import AccessLog, User, UserData
from ..schemas import AccessLogCreate, AccessLogResponse
from ..utils.dependencies import get_current_user, get_admin_user

router = APIRouter()


@router.post("/", response_model=AccessLogResponse)
def create_access_log(
    access_log: AccessLogCreate,
    db: Session = Depends(get_db)
):
    user = None
    vehicle = None

    if access_log.user_id:
        user = db.query(User).filter(User.id == access_log.user_id).first()
        if not user:
            print("User not found, logging as denied.")

    if access_log.vehicle_id:
        vehicle = db.query(UserData).filter(UserData.id == access_log.vehicle_id).first()
        if vehicle and access_log.user_id and vehicle.user_id != access_log.user_id:
            print("Vehicle does not belong to user, logging as denied.")
            vehicle = None  
    new_log = AccessLog(
        user_id=access_log.user_id if user else None,
        vehicle_id=access_log.vehicle_id if vehicle else None,
        entry_time=datetime.utcnow(),
        status=access_log.status
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return new_log


@router.patch("/{log_id}/exit", response_model=AccessLogResponse)
def record_exit(
    log_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    log = db.query(AccessLog).filter(AccessLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Access log not found")
    
    if log.exit_time:
        raise HTTPException(status_code=400, detail="Exit already recorded for this entry")
    
    log.exit_time = datetime.utcnow()
    db.commit()
    db.refresh(log)
    return log  

@router.get("/")
async def get_access_logs(db: Session = Depends(get_db)):
    logs = db.query(AccessLog).order_by(AccessLog.entry_time.desc()).all()
    
    result = []
    for log in logs:
        log_data = {
            "id": log.id,
            "user_id": log.user_id,
            "plate_number": log.plate_number,  
            "unrecognized_plate": log.unrecognized_plate,  
            "effective_plate_number": log.plate_number or log.unrecognized_plate,
            "is_recognized": log.plate_number is not None,
            "entry_time": log.entry_time.isoformat() if log.entry_time else None,
            "exit_time": log.exit_time.isoformat() if log.exit_time else None,
            "status": log.status.value
        }
        
        if log.plate_number and log.vehicle:
            log_data["vehicle_details"] = {
                "plate_number": log.vehicle.plate_number,
                "model": log.vehicle.model or "Unknown",
                "color": log.vehicle.color or "Unknown",
                "owner_name": log.vehicle.name,
                "owner_email": log.vehicle.email
            }
        else:
        
            log_data["vehicle_details"] = {
                "plate_number": log.unrecognized_plate or "Unknown",
                "model": "Unknown",
                "color": "Unknown", 
                "owner_name": "Unknown",
                "owner_email": "Unknown"
            }
        
        result.append(log_data)
    
    return result