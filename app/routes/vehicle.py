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
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vehicle = db.query(UserData).filter(UserData.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    if current_user.role.name != "admin" and vehicle.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this vehicle")
    
    vehicle_dict = vehicle.__dict__.copy()
    vehicle_dict.pop("face_image_data", None)  # remove image field

    return vehicle_dict
