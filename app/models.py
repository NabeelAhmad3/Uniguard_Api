from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, BigInteger,LargeBinary
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime
from .schemas import AccessStatusEnum



class Role(enum.Enum):
    admin = "admin"
    user = "user"


# this table is for admins who will control the web app dont confuse this User with the userdata
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(Role), default=Role.user)
    

    logs = relationship("AccessLog", back_populates="user")

# class Vehicle(Base):
#     __tablename__ = "vehicles"
#     id = Column(Integer, primary_key=True, index=True)
#     plate_number = Column(String, unique=True, nullable=False)
#     model = Column(String, nullable=False)
#     color = Column(String, nullable=False)
#     user_id = Column(Integer, ForeignKey("users.id"))
    
#     owner = relationship("User", back_populates="vehicles")
#     logs = relationship("AccessLog", back_populates="vehicle")



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

    # password = Column(String, nullable=False)
    user = relationship("User")
    logs = relationship("AccessLog", back_populates="vehicle")


class AccessLog(Base):
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("userdata.id"), nullable=True)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    status = Column(Enum(AccessStatusEnum), default=AccessStatusEnum.pending)  # Fix: Use Enum instead of String

    user = relationship("User", back_populates="logs")
    vehicle = relationship("UserData", back_populates="logs")
