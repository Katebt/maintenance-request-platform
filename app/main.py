# app/main.py
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm.session import Session
from starlette.responses import HTMLResponse, RedirectResponse
from app.auth import get_current_user

from app.routers import users, requests, comments, notifications, attachments, auth
from app.database import engine, Base
from app import models
import os
from dotenv import load_dotenv

from app.routers.users import get_db

load_dotenv()

app = FastAPI()

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
# إعداد المجلدات الثابتة
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# إنشاء الجداول في قاعدة البيانات
models.Base.metadata.create_all(bind=engine)

# تسجيل المسارات

app.include_router(users.router)
app.include_router(requests.router)
app.include_router(comments.router)
app.include_router(notifications.router)
app.include_router(attachments.router)
app.include_router(auth.router)


from app.auth import get_optional_user  # بدّل للاسم الصحيح عندك

@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_optional_user)  # ← ليس get_current_user!
):
    if user:
        if user.role == "manager" or user.role == "superuser":
            return RedirectResponse(url="/auth/dashboard")
        elif user.role == "engineer":
            return RedirectResponse(url="/requests/my_requests")
        else:
            return RedirectResponse(url="/auth/dashboard")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})