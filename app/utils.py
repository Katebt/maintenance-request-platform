import os
from fastapi import UploadFile
from datetime import datetime

UPLOAD_DIRECTORY = "uploads"

def save_file(file: UploadFile) -> str:
    # Create the uploads directory if it doesn't exist
    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)

    # Create a unique file name with a timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    file_name = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIRECTORY, file_name)

    # Save the file
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    print(f"File saved at: {file_path}")
    # رجع المسار المناسب للمتصفح وليس المسار الفعلي في النظام
    return f"/uploads/{file_name}"
