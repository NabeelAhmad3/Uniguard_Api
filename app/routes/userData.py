from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import numpy as np
import io
import base64
from ..database import get_db
from ..models import User, UserData
from ..schemas import UserDataCreate, UserDataResponse
from ..utils.dependencies import get_current_user
from ..utils.face_processing import encode_face_image
from pydantic import BaseModel



router = APIRouter()


@router.post("/", response_model=UserDataResponse)
async def create_UserData(
    name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    cnic: str = Form(...),
    registration_number: str = Form(...),
    face_image: UploadFile = File(...),
    plate_number:str =  Form(...),
    model:str = Form(None),
    color:str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Ensure only admin can create UserData
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admin can add user data")

    # Check if CNIC already exists
    check_Cnic = db.query(UserData).filter(UserData.cnic == cnic).first()
    if check_Cnic:
        raise HTTPException(status_code=400, detail="User with this CNIC already registered")
    
    # Ensure uploaded file is an image
    if not face_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image")
    
    # Read and process the image
    image_data = await face_image.read()
    face_embedding = encode_face_image(image_data)
    
    if not face_embedding:
        raise HTTPException(status_code=400, detail="No face detected in the image")
    
    # Create new UserData entry
    new_userData = UserData(
        name=name,
        email=email,
        phone_number=phone_number,
        cnic=cnic,
        registration_number=registration_number,
        face_embedding=face_embedding,  # Store actual embedding
        face_image_data=image_data,
        plate_number=plate_number,
        model=model,
        color=color,
        user_id=current_user.id
    )

    db.add(new_userData)
    db.commit()
    db.refresh(new_userData)

    new_userData.face_image_data = base64.b64encode(image_data).decode()
   
    return new_userData


class UserDataUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    cnic: Optional[str] = None
    registration_number: Optional[str] = None
    plate_number: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    face_embedding: Optional[str] = None

@router.get("/", response_model=List[UserDataResponse])
async def get_users(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access this data")

    query = db.query(UserData)

    user_data = query.all()

    for user in user_data:
        if user.face_image_data:
            user.face_image_data = base64.b64encode(user.face_image_data).decode('utf-8')


    return user_data  






@router.get("/cnic/{cnic}", response_model=UserDataResponse)
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

    return user_data




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
