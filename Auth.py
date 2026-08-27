import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
import requests

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

OTP_VALID_MINUTES = 3


def hash_password(password, salt):
    """Hashes password with SHA-256 + salt."""
    combined = (password + salt).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def generate_salt():
    """Generates a secure random salt."""
    return secrets.token_hex(8)


def generate_otp():
    code = str(secrets.randbelow(1000000)).zfill(6)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return code, generated_at


def is_otp_expired(generated_at):
    if not generated_at:
        return True
    generated_time = datetime.strptime(generated_at, "%Y-%m-%d %H:%M:%S")
    expiry_time = generated_time + timedelta(minutes=OTP_VALID_MINUTES)
    return datetime.now() > expiry_time


def send_verification_email(receiver_email, otp_code):
    print(
        f"\n[DEV MODE] Verification Code for {receiver_email} is: {otp_code}\n"
    )
    return True


def save_user_data_to_file(user_data):
    """حفظ بيانات الجلسة داخل مجلد data/ تلقائياً"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    
    # التأكد من وجود مجلد data
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    file_path = os.path.join(data_dir, "user_session.json")
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(user_data, file, ensure_ascii=False, indent=4)
    print(f"User data successfully saved to: {file_path}")


def login_with_google():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "client_secret.json")

    if not os.path.exists(json_path):
        print(f"\nError: '{json_path}' was not found!")
        print("Please place the downloaded 'client_secret.json' inside the project folder.")
        return None

    try:
        flow = InstalledAppFlow.from_client_secrets_file(json_path, scopes=SCOPES)
        print("\n Opening browser for Google Sign-In... Please select your account.")
        credentials = flow.run_local_server(port=0)

        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {credentials.token}"})
        user_info = session.get("https://www.googleapis.com/oauth2/v3/userinfo").json()

        user_data = {
            "google_id": user_info.get("sub"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
        }

        save_user_data_to_file(user_data)
        return user_data

    except Exception as e:
        print(f"\nError during Google Sign-In: {e}")
        return None
      
      