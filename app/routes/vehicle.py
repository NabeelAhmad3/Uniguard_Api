from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import UserData, User
from ..schemas import UserDataResponse
from ..utils.dependencies import get_current_user

router = APIRouter()

@router.get("/{vehicle_id}")
def read_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db)
):
    vehicle = db.query(UserData).filter(UserData.plate_number == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    vehicle_dict = vehicle.__dict__.copy()
    vehicle_dict.pop("face_image_data", None)  

    return vehicle_dict
