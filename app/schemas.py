from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: RoleEnum = RoleEnum.user
class UserUpdate(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    
class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True


class AccessStatusEnum(str, Enum):
    pending = "Pending"
    granted = "Granted"
    denied = "Denied"

class AccessLogBase(BaseModel):
    user_id: Optional[int] = None
    plate_number: Optional[str] = None
    status: AccessStatusEnum = AccessStatusEnum.pending

class AccessLogCreate(AccessLogBase):
    pass

class AccessLogResponse(AccessLogBase):
    id: int
    entry_time: datetime
    exit_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserDataBase(BaseModel):
    name:str
    email : EmailStr
    phone_number : str
    cnic:str
    registration_number:str
    face_embedding:str
    plate_number:str
    model:Optional[str] = None
    color:Optional[str] = None


class UserDataCreate(UserDataBase):
    pass

class UserDataResponse(UserDataBase):
    id:int

    face_image_data: Optional[str] = None

    logs: List[AccessLogResponse] = []
    class Config:
        from_attributes = True


class UserSearch(BaseModel):
    cnic:str

class NormalUserResponse(BaseModel):
    name:str
    phone_number:str
    registration_number:str
    plate_number:str
    color:str
    email:EmailStr
    cnic:str
    model:str
    face_image_data: Optional[str] = None
    logs: List[AccessLogResponse] = []

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UserDataResponse(BaseModel):
    id: int
    name: str
    email: str
    phone_number: str
    cnic: str
    registration_number: str
    plate_number: str
    model: Optional[str] = None
    color: Optional[str] = None
    user_id: Optional[int] = None
    face_image_data: Optional[str] = None  # Base64-encoded image

    class Config:
        from_attributes = True
        
class UserDataUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    cnic: Optional[str] = None
    registration_number: Optional[str] = None
    plate_number: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    face_embedding: Optional[str] = None