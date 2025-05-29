# create_admin.py
from app.database import SessionLocal
from app.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

admin_email = "admin@mail.com"
phone_number = "0580000505"
admin_password = "M@m2025"
admin_name = "مدير النظام"

existing_admin = db.query(User).filter(User.email == admin_email).first()
if existing_admin:
    print("مدير النظام موجود مسبقًا.")
else:
    admin_user = User(
        name=admin_name,
        email=admin_email,
        phone_number=phone_number,
        password=pwd_context.hash(admin_password),
        role="superuser",
        department="الإدارة"
    )
    db.add(admin_user)
    db.commit()
    print("تم إنشاء مدير النظام بنجاح.")

db.close()