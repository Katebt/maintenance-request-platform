#main.py
import os
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm.session import Session
from starlette.responses import HTMLResponse, RedirectResponse
from dotenv import load_dotenv

from app.database import engine, Base
from app import models
from app.routers import users, requests, comments, notifications, attachments, auth
from app.auth import get_optional_user, get_db
app = FastAPI()

#API
from fastapi.middleware.cors import CORSMiddleware
origins = [
    "http://localhost",         # For direct access via localhost
    "http://localhost:8000",    # Common Flutter web dev server port (if used)
    "http://127.0.0.1",         # For direct access via 127.0.0.1
    "http://127.0.0.1:8000",    # If your backend is accessed directly via 127.0.0.1:8000
    "http://192.168.8.47:8000", # If your backend is accessed directly via your local IP:8000

    # --- CRITICAL ADDITION BASED ON YOUR LATEST SCREENSHOT ---
    "http://localhost:8000", # THIS IS THE EXACT ORIGIN FROM YOUR FLUTTER APP
    # --- END CRITICAL ADDITION ---

    # It's highly recommended to use wildcards for development to avoid this issue
    # every time Flutter assigns a new port:
    "http://localhost:*",       # Allows any port on localhost
    "http://127.0.0.1:*",       # Allows any port on 127.0.0.1
    "http://192.168.8.47:*",    # Allows any port on your local IP (replace with your actual local IP if different)
]
# تحميل المتغيرات البيئية في بيئة التطوير فقط
if os.getenv("ENV") != "production":
    load_dotenv()


#flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all standard methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # Allows all headers, including Authorization
)
# إعداد المجلدات الثابتة
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
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
#new add for flutter
from app.api import flutter_api
app.include_router(flutter_api.api)
#redirect
from fastapi.responses import JSONResponse
from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        if "text/html" in request.headers.get("accept", ""):
            return RedirectResponse(url="/auth/login")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# الصفحة الرئيسية
@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_optional_user)
):
    if user:
        if user.role == "manager":
            return RedirectResponse(url="/auth/dashboard")
        elif user.role == "superuser":
            return RedirectResponse(url="/users")
        elif user.role == "engineer":
            return RedirectResponse(url="/requests/my_requests")
        else:
            return RedirectResponse(url="/auth/dashboard")

    return templates.TemplateResponse("index.html", {"request": request, "user": user})


