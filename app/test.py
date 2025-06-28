import requests

BASE_URL = "http://127.0.0.1:8000"

# بيانات الدخول
email = "adel@moh.gov.sa"
password = "43214321"  # غيّرها لكلمة المرور الصحيحة

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

    # 2. إرسال الطلب مع التوكن
    headers = {
        "Authorization": f"Bearer {token}"
    }

    requests_response = requests.get(f"{BASE_URL}/api/requests/my", headers=headers)

    if requests_response.status_code == 200:
        print("✅ الطلبات المسترجعة:")
        for req in requests_response.json():
            print(f"- #{req['id']}: {req['title']} (الحالة: {req['status']})")
    else:
        print("❌ فشل في استرجاع الطلبات:", requests_response.status_code, requests_response.text)

else:
    print("❌ فشل تسجيل الدخول:", login_response.status_code, login_response.text)