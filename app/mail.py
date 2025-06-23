# app/mail.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()  # تحميل متغيرات البيئة من .env

def send_email(to_email: str, subject: str, body: str):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")

def build_email(request_obj, request_title):
    subject = f"تم استلام طلبك - رقم الطلب {request_obj.id}"
    body = f"""
    <html>
        <body>
            <h3>عزيزي/عزيزتي {request_obj.requester_name}،</h3>
            <p>تم استلام طلبك بنجاح.</p>
            <p><strong>عنوان الطلب:</strong> {request_title}</p>
            <p><strong>رقم الطلب:</strong> {request_obj.id}</p>
            <p>سنعمل على متابعته في أقرب وقت ممكن.</p>
            <br>
            <p>شكرًا لتواصلك معنا.</p>
        </body>
    </html>
    """
    return subject, body