# app/crud.py
from sqlalchemy.orm import Session
from app import models, schemas
from datetime import datetime

# 🗂️ Notifications

##

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        name=user.name,
        email=user.email,
        role=user.role,
        department=user.department,
        phone_number = user.phone_number  # أضف هذا السطر

    )
    db_user.set_password(user.password)  # Hash the password
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
# app/crud.py
def create_request(db: Session, request: schemas.RequestCreate):
    db_request = models.Request(
        requester_name=request.requester_name,
        email=request.email,
        phone_number=request.phone_number,
        title=request.title,
        description=request.description,
        location=request.location,
        department=request.department,
        category=request.category,
        sub_category=request.sub_category,
        assigned_engineer_id=request.assigned_engineer_id
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def get_request(db: Session, request_id: int):
    return db.query(models.Request).filter(models.Request.id == request_id).first()

def get_requests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Request).offset(skip).limit(limit).all()
##
def get_notifications(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Notification).order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()

def create_notification(db: Session, notification: schemas.NotificationCreate):
    db_notification = models.Notification(
        request_id=notification.request_id,
        user_id=notification.user_id,
        message=notification.message,
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

# 👤 Users


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()

# 📋 Requests


def update_request_status(db: Session, request_id: int, status: str):
    db_request = get_request(db, request_id)
    if not db_request:
        return None
    db_request.status = status
    db.commit()
    db.refresh(db_request)
    return db_request

# 💬 Comments
def create_comment(db: Session, request_id: int, content: str):
    db_comment = models.Comment(
        request_id=request_id,
        content=content,
        created_at=datetime.utcnow()
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments_by_request(db: Session, request_id: int):
    return db.query(models.Comment).filter(models.Comment.request_id == request_id).all()

# 📎 Attachments
def create_attachment(db: Session, attachment: schemas.AttachmentCreate):
    db_attachment = models.Attachment(
        request_id=attachment.request_id,
        file_name=attachment.file_name,
        file_path=attachment.file_path,
    )
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)
    return db_attachment

def get_attachments_by_request(db: Session, request_id: int):
    return db.query(models.Attachment).filter(models.Attachment.request_id == request_id).all()

##

# app/crud.py
def get_engineers(db: Session):
    return db.query(models.User).filter(models.User.role == "engineer").all()

