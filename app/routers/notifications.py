from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from app.database import SessionLocal
from app import models
from app.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_unread_notifications_count(db, user_id):
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).count()

@router.get("/", response_class=HTMLResponse)
def list_notifications(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    notifications = db.query(models.Notification)\
        .filter(models.Notification.user_id == user.id)\
        .order_by(models.Notification.created_at.desc())\
        .all()
    unread_count = get_unread_notifications_count(db, user.id)
    return templates.TemplateResponse(
        "notifications_list.html",
        {
            "request": request,
            "notifications": notifications,
            "user": user,
            "unread_count": unread_count
        }
    )

@router.post("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    notif = db.query(models.Notification)\
        .filter(models.Notification.id == notification_id, models.Notification.user_id == user.id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"success": True}