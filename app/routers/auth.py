#app/router/auth/py
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from app import schemas, models, auth, crud
from app.database import SessionLocal
from fastapi.responses import HTMLResponse, RedirectResponse
from app.mail import send_email
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/auth", tags=["Auth"])
templates = Jinja2Templates(directory="templates")

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))



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

    # ✅ تحويل الدور إذا كان الإيميل هو المطلوب
    if user and user.email == "ktalbalawi@moh.gov.sa" and user.role != "superuser":
        user.role = "superuser"
        db.commit()

    if not user or not user.verify_password(password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "البريد الإلكتروني أو كلمة المرور غير صحيحة",
                "user": None
            },
            status_code=401
        )

    token_data = {"user_id": user.id, "email": user.email}
    access_token = auth.create_access_token(token_data)

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

    if user.role == "manager" or user.role == "superuser" :
        user_requests = db.query(models.Request).all()
    elif user.role == "engineer":
        user_requests = db.query(models.Request).filter(models.Request.assigned_engineer_id == user.id).all()
    else:
        user_requests = db.query(models.Request).filter(models.Request.email == user.email).all()

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


BASE_URL = "https://maintenance.onrender.com"

#BASE_URL = "http://127.0.0.1:8000"

@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@router.post("/forgot-password")
def send_reset_email(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email)
    if not user:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "error": "لم يتم العثور على البريد"
        })

    token = auth.create_reset_token(user.email)
    reset_link = f"{BASE_URL}/auth/reset-password?token={token}"

    subject = "إعادة تعيين كلمة المرور"
    body = f"""
    <p>تم طلب إعادة تعيين كلمة المرور لحسابك.</p>
    <p>اضغط على الرابط التالي لتعيين كلمة مرور جديدة:</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>إذا لم تطلب ذلك، يمكنك تجاهل هذه الرسالة.</p>
    """
    send_email(to_email=email, subject=subject, body=body)

    return templates.TemplateResponse("forgot_password.html", {
        "request": request,
        "message": "تم إرسال الرابط إلى بريدك"
    })



@router.get("/reset-password", response_class=HTMLResponse, name="reset_password_form")
def reset_password_form(request: Request, token: str):
    email = auth.verify_reset_token(token)
    if not email:
        return HTMLResponse("❌ الرابط غير صالح أو منتهي", status_code=400)
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})


@router.post("/reset-password")
def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if new_password != confirm_password:
        return HTMLResponse("❌ كلمات المرور غير متطابقة", status_code=400)

    email = auth.verify_reset_token(token)
    if not email:
        return HTMLResponse("❌ الرابط غير صالح أو منتهي", status_code=400)

    user = crud.get_user_by_email(db, email)
    from app.auth import get_password_hash
    #user.hashed_password = get_password_hash(new_password)
    user.password = get_password_hash(new_password)
    db.commit()


    # Redirect to login with success message

    return RedirectResponse(
        url="/auth/login?msg=✅ تم تغيير كلمة المرور بنجاح",
        status_code=status.HTTP_303_SEE_OTHER
    )

