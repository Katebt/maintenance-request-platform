# create_admin.py
from app.database import SessionLocal
from app.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

admin_email = "balawikt@gmail.com"
phone_number = "0580000808"
admin_password = "M@m@2025"  # غيّرها لقيمة قوية
admin_name = "مدير النظام"

# تحقق إذا كان يوجد مدير مسبقًا
existing_admin = db.query(User).filter(User.email == admin_email).first()
if existing_admin:
    print("مدير النظام موجود مسبقًا.")
else:
    admin_user = User(
        name=admin_name,
        email=admin_email,
        phone_number=phone_number,

        password=pwd_context.hash(admin_password),
        role="superuser",  # أو "superuser" إذا أردت
        department="الادارة"
    )
    db.add(admin_user)
    db.commit()
    print("تم إنشاء مدير النظام بنجاح.")

db.close()