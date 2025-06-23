from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

# بيانات الدخول الجديدة
email = "balawikt@gmail.com"
new_password = "123456"  # ضع الباسوورد الجديد هنا

db = SessionLocal()
user = db.query(User).filter(User.email == email).first()

if user:
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    print("✅ تم تحديث كلمة المرور")
else:
    print("❌ لم يتم العثور على المستخدم")