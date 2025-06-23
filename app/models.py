from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, BigInteger,LargeBinary
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime
from .schemas import AccessStatusEnum


class Role(enum.Enum):
    admin = "admin"
    user = "user"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(Role), default=Role.user)
    

    logs = relationship("AccessLog", back_populates="user")


class UserData(Base):
    __tablename__="userdata"
    id = Column(Integer,primary_key=True,index=True)
    name = Column(String, nullable=False)
    email = Column(String,nullable=False)
    phone_number = Column(String,nullable=False,unique=True)
    cnic = Column(String,nullable=False,unique=True)
    registration_number = Column(String, nullable=False)
    face_embedding = Column(String, nullable=False)
    plate_number = Column(String, unique=True, nullable=False)
    face_image_data = Column(LargeBinary, nullable=True)
    model = Column(String, nullable=True)
    color = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User")
    logs = relationship("AccessLog", back_populates="vehicle", primaryjoin="UserData.plate_number == AccessLog.plate_number")


class AccessLog(Base):
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    plate_number = Column(String, ForeignKey("userdata.plate_number"), nullable=True)
    unrecognized_plate = Column(String, nullable=True)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    status = Column(Enum(AccessStatusEnum), default=AccessStatusEnum.pending)

    user = relationship("User", back_populates="logs")
    vehicle = relationship("UserData", back_populates="logs", primaryjoin="UserData.plate_number == AccessLog.plate_number")