# app/routers/comments.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app import schemas, crud
from app.database import SessionLocal
from typing import List

router = APIRouter(prefix="/comments", tags=["Comments"])

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(comment: schemas.CommentCreate, db: Session = Depends(get_db)):
    db_comment = crud.create_comment(db, comment)
    return db_comment

@router.get("/request/{request_id}", response_model=List[schemas.CommentOut])
def get_comments_by_request(request_id: int, db: Session = Depends(get_db)):
    return crud.get_comments_by_request(db, request_id)

