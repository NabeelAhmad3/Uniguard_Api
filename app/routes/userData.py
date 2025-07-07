import base64
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from base64 import b64encode
from ..database import get_db
from ..models import User, UserData
from ..schemas import NormalUserResponse, UserDataUpdate, UserDataResponse
from ..utils.dependencies import get_current_user
from ..utils.face_processing import encode_face_image
from pydantic import BaseModel

router = APIRouter()

def get_user_response(user_data: UserData) -> UserDataResponse:
    face_image_base64 = None
    if user_data.face_image_data:
        face_image_base64 = b64encode(user_data.face_image_data).decode('utf-8')

    return UserDataResponse(
        id=user_data.id,
        name=user_data.name,
        email=user_data.email,
        car_name=user_data.car_name,
        cnic=user_data.cnic,
        registration_number=user_data.registration_number,
        plate_number=user_data.plate_number,
        model=user_data.model,
        color=user_data.color,
        user_id=user_data.user_id,
        face_image_data=face_image_base64,
    )

@router.post("/", response_model=UserDataResponse)
async def create_UserData(
    name: str = Form(...),
    email: str = Form(...),
    car_name: str = Form(...),
    cnic: str = Form(...),
    registration_number: str = Form(...),
    face_image: UploadFile = File(...),
    plate_number: str = Form(...),
    model: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admin can add user data")

    if db.query(UserData).filter(UserData.cnic == cnic).first():
        raise HTTPException(status_code=400, detail="User with this CNIC already exists")

    if not face_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image")

    image_data = await face_image.read()
    face_embedding = encode_face_image(image_data)

    if not face_embedding:
        raise HTTPException(status_code=400, detail="No face detected in the image")

    new_userData = UserData(
        name=name,
        email=email,
        car_name=car_name,
        cnic=cnic,
        registration_number=registration_number,
        face_embedding=face_embedding,
        face_image_data=image_data,
        plate_number=plate_number,
        model=model,
        color=color,
        user_id=current_user.id
    )

    db.add(new_userData)
    db.commit()
    db.refresh(new_userData)

    return get_user_response(new_userData)

@router.get("/", response_model=List[UserDataResponse])
async def get_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access this data")

    users = db.query(UserData).all()
    return [get_user_response(user) for user in users]

@router.get("/cnic/{cnic}", response_model=NormalUserResponse)
async def get_user_by_cnic(
    cnic: str, 
    db: Session = Depends(get_db)
):

    user_data = db.query(UserData).filter(UserData.cnic == cnic).first()

    if user_data:
        if user_data.face_image_data:
            user_data.face_image_data = base64.b64encode(user_data.face_image_data).decode('utf-8')

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user_data

@router.put("/{id}", response_model=UserDataResponse)
async def update_user_by_id(
    id: int,
    userData: UserDataUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update user data")

    user_data = db.query(UserData).filter(UserData.id == id).first()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = userData.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user_data, key, value)

    db.commit()
    db.refresh(user_data)

    return get_user_response(user_data)

@router.delete("/{id}")
async def delete_user_by_id(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete user data")

    user_data = db.query(UserData).filter(UserData.id == id).first()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user_data)
    db.commit()

    return {"message": "User data deleted successfully"}
