# app/routers/attachments.py
from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from app import schemas, models, crud, utils
from app.database import SessionLocal
from typing import List

router = APIRouter(prefix="/attachments", tags=["Attachments"])

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.AttachmentOut, status_code=status.HTTP_201_CREATED)
def upload_attachment(request_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = utils.save_file(file)
    attachment_data = schemas.AttachmentCreate(request_id=request_id, file_name=file.filename, file_path=file_path)
    db_attachment = crud.create_attachment(db, attachment_data)
    return db_attachment

@router.get("/request/{request_id}", response_model=List[schemas.AttachmentOut])
def get_attachments_by_request(request_id: int, db: Session = Depends(get_db)):
    return crud.get_attachments_by_request(db, request_id)