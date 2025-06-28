# app/routers/requests.py
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, Request
from sqlalchemy.orm import Session
from app import  models, crud, utils
from app.database import SessionLocal
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user
from app.mail import send_email
from typing import Optional
from fastapi import BackgroundTasks

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

@router.get("/my_requests", response_class=HTMLResponse)
def my_requests(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):

    # المهندس: الطلبات المسندة له
    if user.role == "engineer":
        requests_q = db.query(models.Request).filter(models.Request.assigned_engineer_id == user.id)

    # المستخدم العادي: الطلبات اللي هو أنشأها (حسب الإيميل)
    elif user.role == "user":
        requests_q = db.query(models.Request).filter(models.Request.email == user.email)

    # المدير أو المشرف يشوف كل الطلبات
    else:
        requests_q = db.query(models.Request)

    new = requests_q.filter(models.Request.status == "new").count()
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
            "new": new,
            "inprogress_count": inprogress_count,
            "completed_count": completed_count,
            "closed_count": closed_count,
        }
    )

@router.get("/list", response_class=HTMLResponse)
def list_requests(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    # المهندس والمدير يشوفون كل الطلبات
    if user.role in ["manager", "engineer", "admin", "superuser"]:
        requests_q = db.query(models.Request)
    else:
        # المستخدم العادي: فقط الطلبات اللي أرسلها بنفس إيميله
        requests_q = db.query(models.Request).filter(models.Request.email == user.email)

    # الإحصائيات حسب الطلبات المتاحة له
    new = requests_q.filter(models.Request.status == "new").count()
    inprogress_count = requests_q.filter(models.Request.status == "In Progress").count()
    completed_count = requests_q.filter(models.Request.status == "Completed").count()
    closed_count = requests_q.filter(models.Request.status == "Closed").count()
    pending_approval_count = requests_q.filter(models.Request.status == "Pending Approval").count()
    requests_list = requests_q.all()

    return templates.TemplateResponse(
        "requests_list.html",
        {
            "pending_approval_count": pending_approval_count,
            "request": request,
            "user": user,
            "requests": requests_list,
            "new": new,
            "inprogress_count": inprogress_count,
            "completed_count": completed_count,
            "closed_count": closed_count,
        }
    )

@router.get("/export_excel")
def export_requests_excel(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    # جلب الطلبات حسب الدور
    if user.role in ["admin", "manager", "engineer", "superuser"]:
        requests_q = db.query(models.Request)
    else:
        requests_q = db.query(models.Request).filter(models.Request.email == user.email)

    requests_list = requests_q.all()

    # تحويل البيانات إلى DataFrame
    data = []
    for req in requests_list:
        data.append({
            "رقم الطلب": req.id,
            "العنوان": req.title,
            "الوصف": req.description,
            "القسم": req.department,
            "الموقع": req.location,
            "الحالة": req.status,
            "تاريخ الإنشاء": req.created_at.strftime('%Y-%m-%d %H:%M') if req.created_at else '',
        })

    df = pd.DataFrame(data)

    # حفظ الملف في الذاكرة
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="الطلبات")

    output.seek(0)
    filename = "requests.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/", response_class=HTMLResponse)
async def create_request(
    request: Request,
    background_tasks: BackgroundTasks,
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
    # التحقق من الحقول المطلوبة
    if not all([
        requester_name.strip(),
        email.strip(),
        phone_number.strip(),
        title.strip(),
        description.strip(),
        location.strip(),
        department.strip()
    ]):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "جميع الحقول مطلوبة ما عدا الصورة",
        })

    # التحقق من نوع الملف (صورة فقط)
    if image and image.filename:
        if not image.content_type.startswith("image/"):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "الملف المرفق يجب أن يكون صورة."
            })

    # إنشاء سجل الطلب
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

    # ✅ رفع الصورة في الخلفية بعد إنشاء الطلب
    if image and image.filename:
        temp_path = utils.save_temp_image(image)
        background_tasks.add_task(
            utils.upload_to_cloudinary_and_save_attachment,
            db_request.id,
            temp_path,
            image.filename
        )

    # ✅ إرسال بريد للمستخدم (خلفية)
    subject = f"تم استلام طلبك - رقم الطلب {db_request.id}"
    body = f"""
    <html><body>
    <h3>عزيزي {requester_name}،</h3>
    <p>تم استلام طلبك بنجاح.</p>
    <p><strong>عنوان البلاغ:</strong> {title}</p>
    <p><strong>رقم البلاغ:</strong> {db_request.id}</p>
    <br>
    <p>سنعمل على متابعته في أقرب وقت ممكن.</p>
    <br><br>
    <p style="color: gray; font-size: 13px;">
      مع تحيات<br>
      فريق منصة بلاغات الصيانة<br>
      مستشفى النساء والأطفال بتبوك
    </p>
    </body></html>
    """
    background_tasks.add_task(send_email, email, subject, body)

    # ✅ إرسال بريد للمدير (خلفية)
    manager_email = "tabukmaternityandchildrenhospi@gmail.com"
    subject = f"بلاغ جديد بحاجة إلى تعيين مهندس - رقم الطلب {db_request.id}"
    body = f"""
    <html>
      <body>
        <h3>عزيزي المدير،</h3>
        <p>تم تسجيل بلاغ جديد في النظام، التفاصيل كالتالي:</p>
        <table border="1" cellpadding="6" cellspacing="0">
          <tr><td><strong>رقم البلاغ</strong></td><td>{db_request.id}</td></tr>
          <tr><td><strong>عنوان البلاغ</strong></td><td>{db_request.title}</td></tr>
          <tr><td><strong>الوصف</strong></td><td>{db_request.description}</td></tr>
          <tr><td><strong>الموقع</strong></td><td>{db_request.location}</td></tr>
          <tr><td><strong>القسم</strong></td><td>{db_request.department}</td></tr>
          <tr><td><strong>اسم المرسل</strong></td><td>{db_request.requester_name}</td></tr>
          <tr><td><strong>البريد الإلكتروني</strong></td><td>{db_request.email}</td></tr>
          <tr><td><strong>رقم الجوال</strong></td><td>{db_request.phone_number}</td></tr>
        </table>
        <p style="margin-top: 20px;">
          <a href='https://maintenance-request-platform.onrender.com/auth/login' style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            الدخول للنظام
          </a>
        </p>
        <br><br>
        <p style="color: gray; font-size: 13px;">
          مع تحيات<br>
          فريق منصة بلاغات الصيانة<br>
          مستشفى النساء والأطفال بتبوك
        </p>
      </body>
    </html>
    """
    background_tasks.add_task(send_email, manager_email, subject, body)

    # ✅ توجيه المستخدم فورًا بدون انتظار الإيميلات أو رفع الصورة
    return RedirectResponse(url="/?success=1", status_code=302)

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
    attachments = db.query(models.Attachment).filter(models.Attachment.request_id == request_id).all()

    return templates.TemplateResponse(
        "request_details.html",
        {
            "request": request,
            "req": req,
            "comments": comments,
            "user": user,
            "attachments": attachments,
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
    return RedirectResponse(url=f"/requests/{request_id}", status_code=302)

@router.get("/{request_id}/edit", response_class=HTMLResponse)
def edit_request(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
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
    background_tasks: BackgroundTasks,

    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    sub_category: str = Form(...),
    status: str = Form(...),
    assigned_engineer_id: Optional[int] = Form(None),
    completion_proof: UploadFile = File(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),

):
    req = crud.get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    req.title = title
    req.description = description
    req.category = category
    req.sub_category = sub_category

    if user.role == "engineer" and status == "Completed":
        req.status = "Pending Approval"
    else:
        req.status = status

    if assigned_engineer_id:
        req.assigned_engineer_id = assigned_engineer_id
        if req.status == "new":
            req.status = "In Progress"
    else:
        req.assigned_engineer_id = None


        ###

    if completion_proof and completion_proof.filename.strip():
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

    # ✅ إرسال إيميل عند تعيين المهندس
    if assigned_engineer_id:
        engineer = db.query(models.User).filter(models.User.id == assigned_engineer_id).first()
        if engineer and engineer.email:
            attachment = db.query(models.Attachment).filter(models.Attachment.request_id == req.id).first()
            image_url = attachment.file_path if attachment else None
            subject = f"تم إسناد بلاغ رقم {req.id} - {req.title}"
            body = f"""
            <h3>تم إسناد بلاغ جديد لك {engineer.name}</h3>
            <p>تفاصيل البلاغ:</p>
            <table border="1" cellpadding="6" cellspacing="0">
              <tr><td><strong>رقم البلاغ</strong></td><td>{req.id}</td></tr>
              <tr><td><strong>عنوان البلاغ</strong></td><td>{req.title}</td></tr>
              <tr><td><strong>الوصف</strong></td><td>{req.description}</td></tr>
              <tr><td><strong>الموقع</strong></td><td>{req.location}</td></tr>
              <tr><td><strong>القسم</strong></td><td>{req.department}</td></tr>
              <tr><td><strong>اسم المرسل</strong></td><td>{req.requester_name}</td></tr>
              <tr><td><strong>البريد الإلكتروني</strong></td><td>{req.email}</td></tr>
              <tr><td><strong>رقم الجوال</strong></td><td>{req.phone_number}</td></tr>
            </table>
            <p style="margin-top: 20px;">
              <a href='https://maintenance-request-platform.onrender.com/auth/login' style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                الدخول للنظام
              </a>
            </p>
            
                <br><br>
                <p style="color: gray; font-size: 13px;">
                مع تحيات<br>
                فريق منصة بلاغات الصيانة<br>
                مستشفى النساء والأطفال بتبوك
                </p>
            """

            background_tasks.add_task(send_email, engineer.email, subject, body)

            requester_subject = f"تم إسناد بلاغك رقم {req.id}"
            requester_body = f"""
            <h3>تم إسناد بلاغك</h3>
            <p>تم إسناد بلاغك بعنوان <strong>{req.title}</strong> إلى:</p>
            <ul>
              <li><strong>المهندس:</strong> {engineer.name}</li>
              <li><strong>رقم الجوال:</strong> {engineer.phone_number or "غير متوفر"}</li>
            </ul>
            <p>سيتم التواصل معك في أقرب وقت لمباشرة البلاغ.</p>
            
              <br><br>
                <p style="color: gray; font-size: 13px;">
                مع تحيات<br>
                فريق منصة بلاغات الصيانة<br>
                مستشفى النساء والأطفال بتبوك
                </p>
            """
            background_tasks.add_task(send_email, req.email, requester_subject, requester_body)

    return RedirectResponse(url=f"/requests/{request_id}", status_code=302)


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


from fastapi.responses import StreamingResponse
import pandas as pd
import io

