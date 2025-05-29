# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app import schemas, models, crud, auth
from app.auth import get_current_user
from app.database import SessionLocal
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List

from app.routers.auth import login

router = APIRouter(prefix="/users", tags=["Users"])
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_class=HTMLResponse)
def get_users(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)  # ضروري!
):
    if user.role not in ["manager", "admin","superuser"]:
        raise HTTPException(status_code=403, detail="غير مصرح لك بعرض المستخدمين")
    users = crud.get_users(db)
    return templates.TemplateResponse("users.html", {"request": request, "users": users, "user": user})


@router.get("/register", response_class=HTMLResponse)
def register_user_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
def register_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = crud.get_user_by_email(db, email)
    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "البريد الإلكتروني مستخدم مسبقًا!",
                "name": name,
                "email": email,
                "phone_number": phone_number
            }
        )

    if len(password) < 8:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "كلمة المرور يجب أن تكون على الأقل 8 أحرف.",
                "name": name,
                "email": email,
                "phone_number": phone_number
            }
        )

    new_user = schemas.UserCreate(
        name=name,
        email=email,
        phone_number=phone_number,
        password=password,
        role="user",
    )
    crud.create_user(db, new_user)
    return RedirectResponse(url="/auth/login?success=1", status_code=302)


@router.get("/list", response_class=HTMLResponse)
def list_users(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role != "manager" and user.role != "admin" and user.role != "superuser":
        raise HTTPException(status_code=403, detail="Access denied")
    users = db.query(models.User).all()
    return templates.TemplateResponse("users_list.html", {"request": request, "user": user, "users": users})

@router.get("/{user_id}/edit", response_class=HTMLResponse)
def edit_user(user_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role != "manager" and user.role != "admin" and user.role != "superuser":
        raise HTTPException(status_code=403, detail="Access denied")
    edit_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not edit_user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("edit_user.html", {"request": request, "user": user, "edit_user": edit_user})

@router.post("/{user_id}/update")
def update_user(
    user_id: int,
    role: str = Form(...),
    department: str = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if user.role != "manager" and user.role != "admin" and user.role != "superuser":
        raise HTTPException(status_code=403, detail="Access denied")
    edit_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not edit_user:
        raise HTTPException(status_code=404, detail="User not found")
    edit_user.role = role
    if role in ["manager", "engineer", "superuser"]:
        edit_user.department = department
    else:
        edit_user.department = None
    db.commit()
    return RedirectResponse(url="/users/list", status_code=302)



@router.get("/{user_id}/profile", response_class=HTMLResponse)
def get_user_profile(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("user_profile.html", {"request": request, "user": user})


@router.post("/{user_id}/update")
def update_user_profile(user_id: int, name: str = Form(...), email: str = Form(...), department: str = Form(None),
                        password: str = Form(None), db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = name
    user.email = email
    user.department = department

    if password:
        user.password = auth.get_password_hash(password)

    db.commit()
    db.refresh(user)
    return {"message": "User profile updated successfully"}



@router.post("/{user_id}/delete")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # تحقق من الصلاحيات
    if current_user.role not in ["manager", "admin","superuser"]:
        raise HTTPException(status_code=403, detail="غير مصرح لك بحذف المستخدمين")

    # لا تسمح للمدير بحذف نفسه!
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="لا يمكنك حذف حسابك الخاص!")

    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

