import json
import os
import sys
import uuid
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pygame

# ==========================================
# 1. إعدادات سيرفر الإيميل (تم وضع بياناتك هنا)
# ==========================================
SENDER_EMAIL = "raafaat7@gmail.com"
SENDER_APP_PASSWORD = "dyfl vtgw vywu pznn"

def send_verification_email(recipient_email, otp_code):
    """ترسل إيميل تأكيد حقيقي عبر سيرفر Gmail وتُرجع سبب الخطأ لو فشلت"""
    if not SENDER_EMAIL or "your_email" in SENDER_EMAIL:
        return False, "قم بكتابة SENDER_EMAIL الصحيح داخل الكود أولاً!"
    if not SENDER_APP_PASSWORD or "xxxx" in SENDER_APP_PASSWORD:
        return False, "قم بكتابة SENDER_APP_PASSWORD (16 حرف من جوجل) داخل الكود!"

    try:
        msg = MIMEMultipart()
        msg['From'] = f"EcoReward System <{SENDER_EMAIL}>"
        msg['To'] = recipient_email
        msg['Subject'] = f"{otp_code} is your EcoReward verification code"

        body = (
            f"Hello,\n\n"
            f"Thank you for registering at EcoReward.\n"
            f"Your email verification code is: {otp_code}\n\n"
            f"Please enter this code in the app to complete your registration.\n\n"
            f"Best regards,\nEcoReward Team"
        )
        msg.attach(MIMEText(body, 'plain'))

        # الاتصال بسيرفر Google SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD.replace(" ", ""))
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"SMTP Error: {str(e)}"


# ==========================================
# 2. وحدات التوثيق والتحقق
# ==========================================
try:
    from Auth import (
        generate_otp,
        generate_salt,
        hash_password,
        is_otp_expired,
        login_with_google,
    )
    from validators import (
        validate_email,
        validate_name,
        validate_otp,
        validate_password,
        validate_university,
    )
except ImportError:
    def generate_otp(): return "123456", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    def generate_salt(): return "sample_salt"
    def hash_password(pwd, salt): return f"hashed_{pwd}"
    def is_otp_expired(t): return False
    def login_with_google(): return None
    def validate_email(e): return "@" in e
    def validate_name(n): return len(n) >= 3
    def validate_otp(i, c): return str(i).strip() == str(c).strip()
    def validate_password(p): return len(p) >= 8
    def validate_university(u): return len(u) > 0

try:
    from storage import JSONStorageManager
    storage_db = JSONStorageManager()
except ImportError:
    storage_db = None

DATA_FILE = os.path.join("data", "users.json")
MAX_LOGIN_ATTEMPTS = 5


# ==========================================
# 3. إدارة نظام المستخدمين
# ==========================================
class User:
    def __init__(self, user_id, name, email, password_hash, salt, university, auth_provider="local"):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.salt = salt
        self.university = university
        self.auth_provider = auth_provider
        self.points = 0
        self.recycling_history = []
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.is_verified = False
        self.otp_code = None
        self.otp_generated_at = None
        self.failed_login_attempts = 0
        self.is_locked = False

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "id": self.user_id,
            "name": self.name,
            "email": self.email,
            "password_hash": self.password_hash,
            "salt": self.salt,
            "university": self.university,
            "auth_provider": self.auth_provider,
            "points": self.points,
            "recycling_history": self.recycling_history,
            "created_at": self.created_at,
            "is_verified": self.is_verified,
            "otp_code": self.otp_code,
            "otp_generated_at": self.otp_generated_at,
            "failed_login_attempts": self.failed_login_attempts,
            "is_locked": self.is_locked,
        }

    @staticmethod
    def from_dict(data):
        user = User(
            data.get("user_id", data.get("id")),
            data["name"],
            data["email"],
            data.get("password_hash"),
            data.get("salt"),
            data.get("university"),
            data.get("auth_provider", "local"),
        )
        user.points = data.get("points", 0)
        user.recycling_history = data.get("recycling_history", [])
        user.created_at = data.get("created_at", "")
        user.is_verified = data.get("is_verified", False)
        user.otp_code = data.get("otp_code")
        user.otp_generated_at = data.get("otp_generated_at")
        user.failed_login_attempts = data.get("failed_login_attempts", 0)
        user.is_locked = data.get("is_locked", False)
        return user


class UserSystem:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.users = self._load_users()

    def _load_users(self):
        raw_data = []
        if storage_db:
            raw_data = storage_db.load_data("users.json", default=[])
        else:
            folder = os.path.dirname(self.data_file)
            if folder and not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
            if os.path.exists(self.data_file):
                with open(self.data_file, "r", encoding="utf-8") as f:
                    try:
                        raw_data = json.load(f)
                    except json.JSONDecodeError:
                        raw_data = []
        return [User.from_dict(item) for item in raw_data]

    def _save_users(self):
        existing_users_map = {}
        old_users = self._load_users()
        for u in old_users:
            if u.email:
                existing_users_map[u.email.lower()] = u.to_dict()

        for u in self.users:
            if u.email:
                existing_users_map[u.email.lower()] = u.to_dict()

        final_user_list = list(existing_users_map.values())

        if storage_db:
            storage_db.save_data("users.json", final_user_list)
        else:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(final_user_list, f, ensure_ascii=False, indent=4)

    def _find_by_email(self, email):
        if not email:
            return None
        email_clean = email.strip().lower()
        for user in self.users:
            if user.email and user.email.lower() == email_clean:
                return user
        return None

    def register_user(self, name, email, password, confirm_password, university):
        clean_email = email.strip().lower()
        self.users = self._load_users()

        if not validate_name(name):
            return False, "Name must be at least 3 characters", None
        if not validate_email(clean_email):
            return False, "Invalid email format", None
        if not validate_password(password):
            return False, "Password must be at least 8 characters", None
        if password != confirm_password:
            return False, "Passwords do not match", None
        if not validate_university(university):
            return False, "University is required", None
        if self._find_by_email(clean_email):
            return False, "Email is already registered", None

        salt = generate_salt()
        pwd_hash = hash_password(password, salt)
        new_user = User(str(uuid.uuid4()), name, clean_email, pwd_hash, salt, university)

        otp_code, otp_time = generate_otp()
        new_user.otp_code = otp_code
        new_user.otp_generated_at = otp_time

        # محاولة إرسال الإيميل الحقيقي
        sent_ok, msg = send_verification_email(clean_email, otp_code)
        if not sent_ok:
            return False, f"Email Failed: {msg}", None

        self.users.append(new_user)
        self._save_users()
        return True, "Verification email sent to your inbox!", new_user

    def resend_otp(self, email):
        user = self._find_by_email(email)
        if not user:
            return False, "User not found"
        if user.is_verified:
            return False, "Account is already verified"
        
        otp_code, otp_time = generate_otp()
        user.otp_code = otp_code
        user.otp_generated_at = otp_time
        
        sent_ok, msg = send_verification_email(user.email, otp_code)
        if not sent_ok:
            return False, f"Email Failed: {msg}"
            
        self._save_users()
        return True, "A new code has been sent to your email!"

    def verify_email(self, email, otp_input):
        self.users = self._load_users()
        user = self._find_by_email(email)
        if not user:
            return False, "User not found"
        if is_otp_expired(user.otp_generated_at):
            return False, "Verification code has expired"
        if validate_otp(otp_input, user.otp_code):
            user.is_verified = True
            user.otp_code = None
            user.otp_generated_at = None
            self._save_users()
            return True, "Account verified successfully"
        return False, "Invalid verification code"

    def login_user(self, email, password):
        self.users = self._load_users()
        user = self._find_by_email(email)
        if not user:
            return False, "No account found with this email"
        if user.auth_provider == "google" and not user.password_hash:
            return False, "This account uses Google Sign-In"
        if user.is_locked:
            return False, "Account is locked due to failed attempts"
        if hash_password(password, user.salt) != user.password_hash:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.is_locked = True
            self._save_users()
            return False, "Incorrect password"
        if not user.is_verified:
            return False, "Please verify your account via OTP first"
        user.failed_login_attempts = 0
        self._save_users()
        return True, user

    def get_user_summary(self, email):
        user = self._find_by_email(email)
        if not user:
            return None
        return {
            "name": user.name,
            "university": user.university,
            "provider": user.auth_provider,
            "points": user.points,
            "total_items_recycled": len(user.recycling_history),
            "member_since": user.created_at,
        }


# ==========================================
# 4. الواجهة الرسمية والتفاعل (Pygame GUI)
# ==========================================
PALETTE = {
    "header_bg": (11, 19, 43),
    "header_title": (255, 255, 255),
    "main_bg": (219, 226, 234),
    "sidebar_bg": (245, 247, 250),
    "sidebar_border": (180, 190, 205),
    "sidebar_hover": (225, 232, 242),
    "sidebar_active": (255, 255, 255),
    "card_bg": (255, 255, 255),
    "card_border": (180, 190, 205),
    "input_bg": (255, 255, 255),
    "input_border": (140, 155, 175),
    "input_focus": (2, 132, 199),
    "btn_green": (21, 128, 61),
    "btn_green_h": (22, 101, 52),
    "btn_blue": (2, 132, 199),
    "btn_blue_h": (3, 105, 161),
    "btn_danger": (220, 38, 38),
    "btn_danger_h": (185, 28, 28),
    "text_dark": (15, 23, 42),
    "text_muted": (71, 85, 105),
    "text_white": (255, 255, 255),
    "accent_blue": (2, 132, 199),
    "accent_green": (21, 128, 61),
}


class InputField:
    def __init__(self, x, y, w, h, label, is_pwd=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.text = ""
        self.is_pwd = is_pwd
        self.active = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_TAB:
                self.active = False
            elif len(self.text) < 36:
                if event.unicode and event.unicode.isprintable():
                    self.text += event.unicode

    def draw(self, surf, f_sm, f_bd):
        label_surf = f_sm.render(self.label, True, PALETTE["text_dark"])
        surf.blit(label_surf, (self.rect.x, self.rect.y - 20))

        pygame.draw.rect(surf, PALETTE["input_bg"], self.rect, border_radius=6)
        border_color = PALETTE["input_focus"] if self.active else PALETTE["input_border"]
        border_w = 2 if self.active else 1
        pygame.draw.rect(surf, border_color, self.rect, border_w, border_radius=6)

        display_val = "•" * len(self.text) if self.is_pwd else self.text
        text_surf = f_bd.render(display_val, True, PALETTE["text_dark"])
        surf.blit(text_surf, (self.rect.x + 12, self.rect.y + 8))


class Button:
    def __init__(self, x, y, w, h, text, bg, hbg, action, text_color=PALETTE["text_white"]):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.bg = bg
        self.hbg = hbg
        self.action = action
        self.tc = text_color

    def draw(self, surf, mpos, font, is_active=False):
        hover = self.rect.collidepoint(mpos)
        if is_active:
            pygame.draw.rect(surf, PALETTE["sidebar_active"], self.rect, border_radius=6)
            pygame.draw.rect(surf, PALETTE["card_border"], self.rect, 1, border_radius=6)
            pygame.draw.rect(surf, PALETTE["accent_blue"], (self.rect.x, self.rect.y, 5, self.rect.h), border_radius=2)
            txt_color = PALETTE["accent_blue"]
        else:
            bg_color = self.hbg if hover else self.bg
            pygame.draw.rect(surf, bg_color, self.rect, border_radius=6)
            txt_color = self.tc

        t_surf = font.render(self.text, True, txt_color)
        surf.blit(t_surf, t_surf.get_rect(center=self.rect.center))

    def check(self, mpos):
        if self.rect.collidepoint(mpos) and self.action:
            self.action()


def run_gui():
    if not pygame.get_init():
        pygame.init()

    screen = pygame.display.set_mode((940, 620))
    clock = pygame.time.Clock()
    pygame.display.set_caption("EcoReward - User System & Auth Hub")

    f_title = pygame.font.SysFont("Segoe UI", 18, bold=True)
    f_sub = pygame.font.SysFont("Segoe UI", 15, bold=True)
    f_btn = pygame.font.SysFont("Segoe UI", 14, bold=True)
    f_body = pygame.font.SysFont("Segoe UI", 14, bold=True)
    f_label = pygame.font.SysFont("Segoe UI", 13, bold=True)
    f_status = pygame.font.SysFont("Segoe UI", 12, bold=True)

    sys_obj = UserSystem()
    state = {
        "view": "login",
        "user": None,
        "msg": "Status: Ready.",
        "msg_col": PALETTE["text_dark"],
    }

    running = True

    def nav(view_name):
        state["view"] = view_name
        state["msg"] = "Status: Ready."
        state["msg_col"] = PALETTE["text_dark"]

    def do_logout():
        state["user"] = None
        nav("login")

    l_email = InputField(270, 175, 420, 38, "Email Address")
    l_pass = InputField(270, 245, 420, 38, "Password", is_pwd=True)

    r_name = InputField(270, 160, 420, 34, "Full Name")
    r_email = InputField(270, 215, 420, 34, "Email Address")
    r_univ = InputField(270, 270, 420, 34, "University")
    r_pass = InputField(270, 325, 420, 34, "Password", is_pwd=True)
    r_cpass = InputField(270, 380, 420, 34, "Confirm Password", is_pwd=True)

    v_email = InputField(270, 175, 420, 38, "Email Address")
    v_code = InputField(270, 245, 420, 38, "Verification Code")

    def do_login():
        ok, res = sys_obj.login_user(l_email.text, l_pass.text)
        if ok:
            state["user"] = res
            state["view"] = "dash"
            state["msg"] = f"Status: Logged in successfully as '{res.name}'"
            state["msg_col"] = PALETTE["accent_green"]
        else:
            state["msg"] = f"Status: Error - {res}"
            state["msg_col"] = PALETTE["btn_danger"]

    def do_reg():
        state["msg"] = "Status: Sending email, please wait..."
        state["msg_col"] = PALETTE["accent_blue"]
        
        ok, msg, user_obj = sys_obj.register_user(r_name.text, r_email.text, r_pass.text, r_cpass.text, r_univ.text)
        if ok:
            v_email.text = r_email.text
            v_code.text = ""
            nav("verify")
            state["msg"] = f"Status: {msg}"
            state["msg_col"] = PALETTE["accent_green"]
        else:
            state["msg"] = f"Status: {msg}"
            state["msg_col"] = PALETTE["btn_danger"]

    def do_ver():
        ok, msg = sys_obj.verify_email(v_email.text, v_code.text)
        if ok:
            state["msg"] = "Status: Account verified successfully! You can login now."
            state["msg_col"] = PALETTE["accent_green"]
            l_email.text = v_email.text
            nav("login")
        else:
            state["msg"] = f"Status: Error - {msg}"
            state["msg_col"] = PALETTE["btn_danger"]

    def do_resend():
        ok, msg = sys_obj.resend_otp(v_email.text)
        if ok:
            state["msg"] = f"Status: {msg}"
            state["msg_col"] = PALETTE["accent_green"]
        else:
            state["msg"] = f"Status: {msg}"
            state["msg_col"] = PALETTE["btn_danger"]

    def do_google():
        g_data = login_with_google()
        if g_data and "email" in g_data:
            g_email = g_data["email"].strip().lower()
            filepath = os.path.join("data", "users.json")
            existing_data = []
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                except Exception:
                    existing_data = []
            
            users_dict = {item["email"].lower(): item for item in existing_data if "email" in item and item["email"]}
            
            if g_email in users_dict:
                user_obj = User.from_dict(users_dict[g_email])
            else:
                user_obj = User(
                    str(uuid.uuid4()),
                    g_data.get("name", "Google User"),
                    g_email,
                    None,
                    None,
                    "Not Specified",
                    "google"
                )
                user_obj.is_verified = True
                users_dict[g_email] = user_obj.to_dict()

            final_list = list(users_dict.values())
            os.makedirs("data", exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(final_list, f, ensure_ascii=False, indent=4)

            sys_obj.users = [User.from_dict(d) for d in final_list]
            state["user"] = user_obj
            state["view"] = "dash"
            state["msg"] = f"Status: Authenticated as '{user_obj.name}'"
            state["msg_col"] = PALETTE["accent_green"]

    nav_buttons = [
        ("login", Button(15, 80, 180, 42, "Login", PALETTE["sidebar_bg"], PALETTE["sidebar_hover"], lambda: nav("login"), PALETTE["text_dark"])),
        ("reg", Button(15, 130, 180, 42, "Register", PALETTE["sidebar_bg"], PALETTE["sidebar_hover"], lambda: nav("reg"), PALETTE["text_dark"])),
        ("verify", Button(15, 180, 180, 42, "Verify OTP", PALETTE["sidebar_bg"], PALETTE["sidebar_hover"], lambda: nav("verify"), PALETTE["text_dark"])),
    ]

    l_buttons = [
        Button(270, 310, 200, 42, "Sign In", PALETTE["btn_green"], PALETTE["btn_green_h"], do_login),
        Button(490, 310, 200, 42, "Google Sign-In", PALETTE["btn_blue"], PALETTE["btn_blue_h"], do_google),
    ]

    r_button = Button(270, 435, 420, 42, "Create Account", PALETTE["btn_green"], PALETTE["btn_green_h"], do_reg)

    v_buttons = [
        Button(270, 310, 200, 42, "Verify Account", PALETTE["btn_green"], PALETTE["btn_green_h"], do_ver),
        Button(490, 310, 200, 42, "Resend OTP", PALETTE["btn_blue"], PALETTE["btn_blue_h"], do_resend),
    ]

    logout_btn = Button(820, 12, 95, 32, "Logout", PALETTE["btn_danger"], PALETTE["btn_danger_h"], do_logout)

    while running:
        mpos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state["view"] == "login":
                l_email.handle(event)
                l_pass.handle(event)
            elif state["view"] == "reg":
                for f in [r_name, r_email, r_univ, r_pass, r_cpass]:
                    f.handle(event)
            elif state["view"] == "verify":
                v_email.handle(event)
                v_code.handle(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                for _, b in nav_buttons:
                    b.check(mpos)
                if state["view"] == "login":
                    for b in l_buttons:
                        b.check(mpos)
                elif state["view"] == "reg":
                    r_button.check(mpos)
                elif state["view"] == "verify":
                    for b in v_buttons:
                        b.check(mpos)
                elif state["view"] == "dash":
                    logout_btn.check(mpos)

        screen.fill(PALETTE["main_bg"])

        pygame.draw.rect(screen, PALETTE["header_bg"], (0, 0, 940, 56))
        screen.blit(f_title.render("EcoReward - User Control Center", True, PALETTE["header_title"]), (20, 16))

        pygame.draw.rect(screen, PALETTE["sidebar_bg"], (0, 56, 210, 564))
        pygame.draw.line(screen, PALETTE["sidebar_border"], (210, 56), (210, 620), 1)

        for route, btn in nav_buttons:
            btn.draw(screen, mpos, f_btn, is_active=(state["view"] == route))

        status_box = pygame.Rect(240, 75, 670, 46)
        pygame.draw.rect(screen, PALETTE["card_bg"], status_box, border_radius=6)
        pygame.draw.rect(screen, PALETTE["card_border"], status_box, 1, border_radius=6)
        screen.blit(f_status.render(state["msg"], True, state["msg_col"]), (250, 88))

        if state["view"] == "login":
            card_box = pygame.Rect(240, 135, 670, 240)
            pygame.draw.rect(screen, PALETTE["card_bg"], card_box, border_radius=8)
            pygame.draw.rect(screen, PALETTE["card_border"], card_box, 1, border_radius=8)
            l_email.draw(screen, f_label, f_body)
            l_pass.draw(screen, f_label, f_body)
            for btn in l_buttons:
                btn.draw(screen, mpos, f_btn)

        elif state["view"] == "reg":
            card_box = pygame.Rect(240, 130, 670, 365)
            pygame.draw.rect(screen, PALETTE["card_bg"], card_box, border_radius=8)
            pygame.draw.rect(screen, PALETTE["card_border"], card_box, 1, border_radius=8)
            for f in [r_name, r_email, r_univ, r_pass, r_cpass]:
                f.draw(screen, f_label, f_body)
            r_button.draw(screen, mpos, f_btn)

        elif state["view"] == "verify":
            card_box = pygame.Rect(240, 135, 670, 240)
            pygame.draw.rect(screen, PALETTE["card_bg"], card_box, border_radius=8)
            pygame.draw.rect(screen, PALETTE["card_border"], card_box, 1, border_radius=8)
            v_email.draw(screen, f_label, f_body)
            v_code.draw(screen, f_label, f_body)
            for btn in v_buttons:
                btn.draw(screen, mpos, f_btn)

        elif state["view"] == "dash" and state["user"]:
            s = sys_obj.get_user_summary(state["user"].email)
            logout_btn.draw(screen, mpos, f_btn)

            card_box = pygame.Rect(240, 135, 670, 240)
            pygame.draw.rect(screen, PALETTE["card_bg"], card_box, border_radius=8)
            pygame.draw.rect(screen, PALETTE["card_border"], card_box, 1, border_radius=8)

            screen.blit(f_sub.render(f"Logged User: {s['name']}", True, PALETTE["accent_blue"]), (260, 155))
            screen.blit(f_body.render(f"University: {s['university']}", True, PALETTE["text_dark"]), (260, 190))
            screen.blit(f_body.render(f"Points Balance: {s['points']} pts", True, PALETTE["text_dark"]), (260, 218))
            screen.blit(f_body.render(f"Auth Method: {s['provider'].capitalize()}", True, PALETTE["text_muted"]), (260, 246))

        pygame.display.flip()
        clock.tick(60)

    return state.get("user")


if __name__ == "__main__":
    run_gui()