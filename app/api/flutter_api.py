# 📁 app/api/flutter_api.py
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from app import models, crud, utils, auth
from app.auth import get_current_user, get_db, get_current_user_from_token

api = APIRouter(prefix="/api", tags=["API"])

@api.post("/auth/token")
def get_token(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user or not user.verify_password(password):
        raise HTTPException(status_code=401, detail="البريد أو كلمة المرور غير صحيحة")

    token_data = {"user_id": user.id, "email": user.email}
    access_token = auth.create_access_token(token_data)
    print("✅ تسجيل دخول:", user.email, "| الدور:", user.role)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "role": user.role,


    }

@api.get("/requests/my")
def get_my_requests(
    user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)):
    requests_q = db.query(models.Request)
    if user.role == "engineer":
        requests_q = requests_q.filter(models.Request.assigned_engineer_id == user.id)
    elif user.role == "user":
        requests_q = requests_q.filter(models.Request.email == user.email)
    return [
        {
            **req.to_dict(),
            "can_approve": user.role == "manager" and req.status == "Pending Approval",
            "can_complete": user.role == "engineer" and req.status == "In Progress"
        }
        for req in requests_q
    ]

@api.get("/list")
def list_requests(
    user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    requests_q = db.query(models.Request)
    if user.role not in ["manager", "engineer", "admin", "superuser"]:
        requests_q = requests_q.filter(models.Request.email == user.email)
    requests = requests_q.all()

    return [
        {
            **req.to_dict(),  # إذا عندك `.to_dict()` في الموديل
            "can_approve": user.role == "manager" and req.status == "Pending Approval"
        }
        for req in requests
    ]

@api.post("/")
async def create_request(
    requester_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    department: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    file_path = None
    if image and image.filename:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only images are allowed")
        file_path = utils.save_file(image)

    db_request = models.Request(
        title=title,
        description=description,
        location=location,
        department=department,
        requester_name=requester_name,
        email=email,
        phone_number=phone_number
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)

    if file_path:
        db_attachment = models.Attachment(
            request_id=db_request.id,
            file_name=image.filename,
            file_path=file_path,
            file_type="completion_proof"
        )
        db.add(db_attachment)
        db.commit()

    return {"id": db_request.id, "message": "Request created successfully"}


@api.get("/{request_id}")
def get_request_details(
        request_id: int,
        user: models.User = Depends(get_current_user_from_token),
        db: Session = Depends(get_db)
):
    req = crud.get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    comments = crud.get_comments_by_request(db, request_id)
    attachments = db.query(models.Attachment).filter(models.Attachment.request_id == request_id).all()

    return {
        "request": req.to_dict(),  # تأكد أن to_dict() موجود في الموديل
        "comments": [comment.to_dict() for comment in comments],
        "attachments": [att.to_dict() for att in attachments],
        "can_approve": user.role == "manager" and req.status == "Pending Approval"
    }

@api.post("/{request_id}/comments")
def add_comment(
    request_id: int,
    content: str = Form(...),
    user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)):
    db_comment = models.Comment(
        request_id=request_id,
        content=content,
        user_id=user.id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return {"message": "Comment added successfully"}

@api.post("/{request_id}/approve")
def approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_token)):
    req = crud.get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if user.role != "manager":
        raise HTTPException(status_code=403, detail="Not authorized")
    if req.status != "Pending Approval":
        raise HTTPException(status_code=400, detail="Request not pending approval")

    req.status = "Completed"
    db.commit()
    return {"msg": "Approved as completed"}

@api.put("/requests/{request_id}/update")
def update_request_details(
    request_id: int,
    status: str = Form(...),
    engineer_id: int = Form(None),
    category: str = Form(None),
    subcategory: str = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_token)
):
    if user.role != "manager":
        raise HTTPException(status_code=403, detail="غير مصرح لك")

    req = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")

    req.status = status
    req.assigned_engineer_id = engineer_id
    req.category = category
    req.sub_category = subcategory

    db.commit()
    return {"msg": "تم تحديث الطلب بنجاح"}