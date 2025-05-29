from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from sqlalchemy.orm import Session
from app import schemas, models, auth
from app.database import SessionLocal
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from app.auth import get_current_user  # يجب أن يكون لديك هذا الديبندنسي



import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

router = APIRouter(prefix="/auth", tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# دالة لجلب التوكن من الكوكيز
def get_token_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # احذف Bearer إذا موجودة
    if token.startswith("Bearer "):
        token = token[len("Bearer "):]
    return token

# صفحة تسجيل الدخول (GET)
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None, "user": None}
    )


# معالجة تسجيل الدخول (POST)
@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not user.verify_password(password):
        # بدلاً من رفع استثناء، أعد نفس الصفحة مع رسالة الخطأ:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "البريد الإلكتروني أو كلمة المرور غير صحيحة",
                "user": None
            },
            status_code=401
        )

    # إنشاء التوكن
    token_data = {"user_id": user.id, "email": user.email}
    access_token = auth.create_access_token(token_data)

    # إعادة التوجيه للوحة التحكم مع حفظ التوكن في الكوكيز
    response = RedirectResponse(url="/auth/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


# عرض لوحة التحكم (DASHBOARD)

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, token: str = Depends(get_token_from_cookie), db: Session = Depends(get_db)):

    payload = auth.decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(models.User).filter(models.User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "manager":
        user_requests = db.query(models.Request).all()
    elif user.role == "engineer":
        user_requests = db.query(models.Request).filter(models.Request.assigned_engineer_id == user.id).all()
    else:
        user_requests = db.query(models.Request).filter(models.Request.requester_name == user.name).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "requests": user_requests
    })



@router.get("/logout")
def logout():
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    return response