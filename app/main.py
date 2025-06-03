from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base

from .routes import auth,access, user, api_processor,userData,vehicle


app = FastAPI(title="UniGuard Security System API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(vehicle.router, prefix="/vehicles", tags=["Vehicles"])
app.include_router(access.router, prefix="/access", tags=["Access Logs"])
app.include_router(api_processor.router, prefix="/api", tags=["API Processing"])
app.include_router(userData.router, prefix="/userdata", tags=["Users Data"])

@app.get("/")
def read_root():
    return {"message": "Welcome to UniGuard Security System"}