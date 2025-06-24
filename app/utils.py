import os
from fastapi import UploadFile
from datetime import datetime
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
    try:
        # رفع الملف إلى Cloudinary مباشرة
        result = cloudinary.uploader.upload(file.file, resource_type="image")
        url = result.get("secure_url")
        print(f"✅ Cloudinary upload success: {url}")
        return url
    except Exception as e:
        print(f"❌ Cloudinary upload failed: {e}")
        return None