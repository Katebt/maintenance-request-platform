import os
import uuid
import shutil
from fastapi import UploadFile
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# إعداد Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def save_file(file: UploadFile) -> str | None:
    """
    رفع فوري لملف (غير مستخدم الآن بعد التحسين)
    """
    try:
        result = cloudinary.uploader.upload(file.file, resource_type="image")
        url = result.get("secure_url")
        print(f"✅ Cloudinary upload success: {url}")
        return url
    except Exception as e:
        print(f"❌ Cloudinary upload failed: {e}")
        return None

def save_temp_image(upload_file: UploadFile) -> str:
    """
    حفظ مؤقت للصورة على الخادم لتستخدمها background task
    """
    temp_filename = f"/tmp/{uuid.uuid4().hex}_{upload_file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    print(f"✅ Saved temp image: {temp_filename}")
    return temp_filename

def upload_to_cloudinary_and_save_attachment(request_id: int, temp_file_path: str, original_filename: str):
    """
    دالة تُستخدم في background task لرفع الصورة من ملف مؤقت إلى Cloudinary
    ثم حفظ الرابط في قاعدة البيانات كمرفق
    """
    from app import models, database
    db = database.SessionLocal()
    try:
        result = cloudinary.uploader.upload(temp_file_path, resource_type="image")
        url = result.get("secure_url")

        if url:
            attachment = models.Attachment(
                request_id=request_id,
                file_name=original_filename,
                file_path=url,
                file_type="completion_proof"
            )
            db.add(attachment)
            db.commit()
            print(f"✅ Uploaded to Cloudinary and saved: {url}")
        else:
            print("⚠️ Upload to Cloudinary returned no URL.")

    except Exception as e:
        print(f"❌ Error uploading in background: {e}")

    finally:
        db.close()
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"🧹 Deleted temp file: {temp_file_path}")