import re
import json
import os

DATA_DIR = "data"

def _ensure_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def load_data(filename, default=None):
    if default is None:
        default = []
    _ensure_dir()
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default

def save_data(filename, data):
    _ensure_dir()
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except IOError as e:
        print(f"Storage Error: {e}")
        return False

def validate_name(name):
    if not isinstance(name, str):
        return False
    return len(name.strip()) >= 3

def validate_email(email):
    if not isinstance(email, str):
        return False

    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def validate_password(password):
    if not isinstance(password, str):
        return False

    if len(password) < 8:
        return False

    has_digit = any(char.isdigit() for char in password)
    return has_digit

def validate_university(university):
    return isinstance(university, str) and len(university.strip()) > 0

def validate_otp(otp_input, otp_correct):
    if not isinstance(otp_input, str):
        return False
    return otp_input.strip() == str(otp_correct)