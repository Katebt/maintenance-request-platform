from  app.mail import send_email
"""

send_email(
    to_email="tabukmaternityandchildrenhospi@gmail.com",
    subject="MAINTENANCE DEPARTMENT",
    body="<h3>This is a test from FastAPI via Gmail</h3>"
)"""

def send_request_notification(to_email: str, requester_name: str, title: str):
    subject = "📢 تم تسجيل بلاغ جديد"
    body = f"""
    <p>مرحباً،</p>
    <p>تم تسجيل بلاغ جديد بواسطة: <b>{requester_name}</b></p>
    <p>عنوان البلاغ: <b>{title}</b></p>
    <p>يرجى الدخول إلى النظام لمراجعته.</p>
    """
    send_email(to_email, subject, body)