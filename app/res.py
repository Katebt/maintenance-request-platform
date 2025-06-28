import requests

BASE_URL = "http://127.0.0.1:8000"

# بيانات المستخدم
email = "adel@moh.gov.sa"
password = "43214321"

# 1. تسجيل الدخول للحصول على التوكن
login_response = requests.post(
    f"{BASE_URL}/api/auth/token",
    data={
        "email": email,
        "password": password
    }
)

if login_response.status_code == 200:
    token = login_response.json().get("access_token")
    print("✅ تم الحصول على التوكن:\n", token)

    # 2. إعداد الهيدر
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 3. إرسال الطلب لاسترجاع البلاغات
    response = requests.get(f"{BASE_URL}/api/requests/my", headers=headers)

    if response.status_code == 200:
        print("✅ الطلبات المسترجعة:")
        for req in response.json():
            print(f"- #{req['id']}: {req['title']} (الحالة: {req['status']})")
    else:
        print("❌ فشل في استرجاع الطلبات:", response.status_code, response.text)
else:
    print("❌ فشل تسجيل الدخول:", login_response.status_code, login_response.text)