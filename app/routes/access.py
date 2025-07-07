import openpyxl
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import AccessLog, User, UserData
from ..schemas import AccessLogCreate, AccessLogResponse
from ..utils.dependencies import get_current_user, get_admin_user
from fastapi.responses import StreamingResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

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
            "status": log.status.value
        }
        
        if log.plate_number and log.vehicle:
            log_data["vehicle_details"] = {
                "plate_number": log.vehicle.plate_number,
                "model": log.vehicle.model or "UnRecognized",
                "color": log.vehicle.color or "UnRecognized",
                "owner_name": log.vehicle.name,
                "owner_email": log.vehicle.email
            }
        else:
        
            log_data["vehicle_details"] = {
                "plate_number": log.unrecognized_plate or "UnRecognized",
                "model": "UnRecognized",
                "color": "UnRecognized", 
                "owner_name": "UnRecognized",
                "owner_email": "UnRecognized"
            }
        
        result.append(log_data)
    
    return result



@router.get("/export/pdf")
def export_logs_pdf(db: Session = Depends(get_db)):
    logs = db.query(AccessLog).order_by(AccessLog.entry_time.asc()).all()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 25)
    pdf.drawString(120, height - 50, " UniGuard Access Logs Report")
    pdf.setFont("Helvetica", 10)

    data = [["ID", "Owner Name", "Owner Email", "Plate", "Model", "Color", "Status", "Entry Time"]]

    for log in logs:
        vehicle = log.vehicle
        data.append([
            log.id,
            vehicle.name if vehicle else "UnRecognized",
            vehicle.email if vehicle else "UnRecognized",
            vehicle.plate_number if vehicle else (log.unrecognized_plate or "UnRecognized"),
            vehicle.model if vehicle else "UnRecognized",
            vehicle.color if vehicle else "UnRecognized",
            log.status.value,
            log.entry_time.strftime("%Y-%m-%d %H:%M:%S") if log.entry_time else "N/A"
        ])

    table = Table(data, colWidths=[25, 75, 165, 65, 65, 65, 50, 95])

    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  
        ('WORDWRAP', (0, 0), (-1, -1), 1),       
    ]))

    table_width, table_height = table.wrap(0, 0)

    table.drawOn(pdf, 3, height - 80 - table_height)

    pdf.save()
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=access_logs.pdf"})

@router.get("/export/excel")
def export_logs_excel(db: Session = Depends(get_db)):
    logs = db.query(AccessLog).order_by(AccessLog.entry_time.asc()).all()

    data = []
    for log in logs:
        vehicle = log.vehicle
        data.append({
            "ID": log.id,
            "Owner Name": vehicle.name if vehicle else "UnRecognized",
            "Owner Email": vehicle.email if vehicle else "UnRecognized",
            "Plate Number": vehicle.plate_number if vehicle else (log.unrecognized_plate or "UnRecognized"),
            "Model": vehicle.model if vehicle else "UnRecognized",
            "Color": vehicle.color if vehicle else "UnRecognized",
            "Status": log.status.value,
            "Entry Time": log.entry_time.strftime("%Y-%m-%d %H:%M:%S") if log.entry_time else "N/A"
        })

    df = pd.DataFrame(data)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Access Logs")
        workbook = writer.book
        worksheet = writer.sheets["Access Logs"]

        for row_idx, cell in enumerate(worksheet['G'][1:], start=2):
            status = cell.value
            fill_color = "00FF00" if status == "Granted" else "FF0000"
            cell.fill = openpyxl.styles.PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")

    buffer.seek(0)

    return StreamingResponse(buffer,
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=access_logs.xlsx"})
