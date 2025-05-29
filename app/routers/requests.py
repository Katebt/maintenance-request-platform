# app/routers/requests.py
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, Request
from sqlalchemy.orm import Session
from app import schemas, models, crud, utils
from app.database import SessionLocal
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user  # يجب أن يكون لديك هذا الديبندنسي

router = APIRouter(prefix="/requests", tags=["Requests"])
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/new", response_class=HTMLResponse)
def new_request(request: Request):
    return templates.TemplateResponse("create_request.html", {"request": request})


#for Maint eng boards
# app/routers/requests.py

@router.get("/my_requests", response_class=HTMLResponse)
def my_requests(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # اجلب الطلبات الخاصة بالمستخدم أو المهندس
    if user.role == "engineer":
        requests_q = db.query(models.Request).filter(models.Request.assigned_engineer_id == user.id)
    else:
        requests_q = db.query(models.Request).filter(models.Request.email == user.email)

    # احصائيات الطلبات حسب الحالة
    pending_count = requests_q.filter(models.Request.status == "Pending").count()
    inprogress_count = requests_q.filter(models.Request.status == "In Progress").count()
    completed_count = requests_q.filter(models.Request.status == "Completed").count()
    closed_count = requests_q.filter(models.Request.status == "Closed").count()
    requests_list = requests_q.all()

    return templates.TemplateResponse(
        "engineer_requests_list.html",
        {
            "request": request,
            "user": user,
            "requests": requests_list,
            "pending_count": pending_count,
            "inprogress_count": inprogress_count,
            "completed_count": completed_count,
            "closed_count": closed_count,
        }
    )

@router.get("/list", response_class=HTMLResponse)
def list_requests(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    all_requests = db.query(models.Request).all()
    # احصائيات
    pending_count = db.query(models.Request).filter(models.Request.status == "Pending").count()
    inprogress_count = db.query(models.Request).filter(models.Request.status == "In Progress").count()
    completed_count = db.query(models.Request).filter(models.Request.status == "Completed").count()
    closed_count = db.query(models.Request).filter(models.Request.status == "Closed").count()
    pending_approval_count = db.query(models.Request).filter(models.Request.status == "Pending Approval").count()

    return templates.TemplateResponse(
        "requests_list.html",
        {
            "pending_approval_count":pending_approval_count,
            "request": request,
            "user": user,
            "requests": all_requests,
            "pending_count": pending_count,
            "inprogress_count": inprogress_count,
            "completed_count": completed_count,
            "closed_count": closed_count,
        }
    )
@router.post("/", response_class=HTMLResponse)
async def create_request(
        request: Request,
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
    if image:
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
            file_type="completion_proof"  # استخدم file_type للتمييز

        )

        db.add(db_attachment)
        db.commit()
        return RedirectResponse(
            url="/?success=1",
            status_code=302
        )


    return templates.TemplateResponse("index.html", {"request": request, "message": "تم إرسال الطلب بنجاح!"})

@router.get("/{request_id}", response_class=HTMLResponse)
def get_request_details(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    req = crud.get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    comments = crud.get_comments_by_request(db, request_id)
    # جلب المرفقات الخاصة بالطلب
    attachments = db.query(models.Attachment).filter(models.Attachment.request_id == request_id).all()

    return templates.TemplateResponse(
        "request_details.html",
        {
            "request": request,
            "req": req,
            "comments": comments,
            "user": user,
            "attachments": attachments,  # أضف المرفقات هنا
        }
    )

@router.post("/{request_id}/comments")
def add_comment(
    request_id: int,
    content: str = Form(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_comment = models.Comment(
        request_id=request_id,
        content=content,
        user_id=user.id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    # إعادة التوجيه إلى صفحة تفاصيل البلاغ بعد الإضافة
    return RedirectResponse(
        url=f"/requests/{request_id}",
        status_code=302
    )

@router.get("/{request_id}/edit", response_class=HTMLResponse)
def edit_request(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),  # هنا!
):
    req = crud.get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    engineers = crud.get_engineers(db)
    return templates.TemplateResponse(
        "update_request.html",
        {
            "request": request,
            "req": req,
            "engineers": engineers,
            "user": user,
        }
    )


@router.post("/{request_id}/update")
async def update_request(
    request_id: int,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    sub_category: str = Form(...),
    status: str = Form(...),
    assigned_engineer_id: str = Form(None),    # استقبال كـ str هنا!
    completion_proof: UploadFile = File(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    req = crud.get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    req.title = title
    req.description = description
    req.category = category
    req.sub_category = sub_category
#    req.status = status
    # بدل: req.status = status
    if user.role == "engineer" and status == "Completed":
        req.status = "Pending Approval"
    else:
        req.status = status

    # تعيين مهندس الصيانة بشكل آمن
    if assigned_engineer_id:
        req.assigned_engineer_id = int(assigned_engineer_id)
    else:
        req.assigned_engineer_id = None

    # إذا تم رفع إثبات إتمام، احفظه في المرفقات مع file_type
    if completion_proof:
        file_path = utils.save_file(completion_proof)
        db_attachment = models.Attachment(
            request_id=req.id,
            file_name=completion_proof.filename,
            file_path=file_path,
            file_type="completion_proof",
        )
        db.add(db_attachment)

    db.commit()
    db.refresh(req)
    return RedirectResponse(url=f"/requests/{request_id}", status_code=302)

#final Approve by Manager
@router.post("/{request_id}/approve")
def approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
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
