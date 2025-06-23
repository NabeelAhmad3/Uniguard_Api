from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User,UserData
from ..schemas import UserResponse,UserSearch,NormalUserResponse
from ..utils.dependencies import get_current_user, get_admin_user
# from ..utils.face_processing import encode_face_image

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0, 
    limit: int = 100,
    current_user: User = Depends(get_admin_user)  # Keep admin-only for listing all users
):
    db = next(get_db())
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Endpoint for users to get their own information"""
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this user")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.post("/get_user_data", response_model=NormalUserResponse)
def get_user_detail(
    user_search: UserSearch,
    db: Session = Depends(get_db)
):
  
    user = db.query(UserData).filter(UserData.cnic == user_search.cnic).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user





















# @router.post("/face-embedding", status_code=status.HTTP_200_OK)
# async def upload_face_embedding(
#     face_image: UploadFile = File(...),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     if not face_image.content_type.startswith('image/'):
#         raise HTTPException(status_code=400, detail="Uploaded file is not an image")
    
#     # Read and process the image
#     image_data = await face_image.read()
#     face_embedding = encode_face_image(image_data)
    
#     if not face_embedding:
#         raise HTTPException(status_code=400, detail="No face detected in the image")
    
#     # Update the user's face embedding
#     current_user.face_embedding = face_embedding
#     db.commit()
    
#     return {"detail": "Face embedding uploaded successfully"}