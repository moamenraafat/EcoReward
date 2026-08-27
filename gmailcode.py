import json
import os
import threading
import pygame
from google_auth_oauthlib.flow import InstalledAppFlow
import requests

# 1. إعدادات جوجل OAuth
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

def save_user_data_to_file(user_data):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "user_session.json")

    all_users = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                all_users = json.load(file)
                if not isinstance(all_users, list):
                    all_users = [all_users]
        except Exception:
            all_users = []

    updated = False
    for i, user in enumerate(all_users):
        if user.get("google_id") == user_data.get("google_id"):
            all_users[i] = user_data
            updated = True
            break

    if not updated:
        all_users.append(user_data)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(all_users, file, ensure_ascii=False, indent=4)

def login_with_google():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "client_secret.json")

    flow = InstalledAppFlow.from_client_secrets_file(json_path, scopes=SCOPES)
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

# 2. إعدادات نافذة Pygame
pygame.init()
WIDTH, HEIGHT = 500, 350
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Google OAuth Login")

# الألوان
BG_COLOR = (30, 30, 36)
BTN_COLOR = (26, 115, 232)
BTN_HOVER = (21, 87, 176)
WHITE = (255, 255, 255)
GREEN = (46, 160, 67)
RED = (235, 87, 87)
YELLOW = (230, 194, 0)

# الخطوط
font_title = pygame.font.SysFont("Arial", 28, bold=True)
font_btn = pygame.font.SysFont("Arial", 18, bold=True)
font_status = pygame.font.SysFont("Arial", 16)

# زر تسجيل الدخول
button_rect = pygame.Rect(125, 120, 250, 50)
status_text = ""
status_color = WHITE
is_loading = False

def run_login_thread():
    global status_text, status_color, is_loading
    try:
        user = login_with_google()
        status_text = f"Logged in: {user['name']}"
        status_color = GREEN
    except Exception as e:
        status_text = "Login Failed!"
        status_color = RED
    is_loading = False

# اللوب الرئيسية لـ Pygame
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and button_rect.collidepoint(mouse_pos) and not is_loading:
                is_loading = True
                status_text = "Opening Browser..."
                status_color = YELLOW
                threading.Thread(target=run_login_thread, daemon=True).start()

    # الرسم على الشاشة
    screen.fill(BG_COLOR)

    # رسم العنوان
    title_surface = font_title.render("Google OAuth Login", True, WHITE)
    screen.blit(title_surface, title_surface.get_rect(center=(WIDTH // 2, 50)))

    # رسم الزر
    color = BTN_HOVER if button_rect.collidepoint(mouse_pos) and not is_loading else BTN_COLOR
    pygame.draw.rect(screen, color, button_rect, border_radius=10)
    
    btn_text = "Please Wait..." if is_loading else "Login with Google"
    btn_surface = font_btn.render(btn_text, True, WHITE)
    screen.blit(btn_surface, btn_surface.get_rect(center=button_rect.center))

    # رسم النص التوضيحي للحالة
    if status_text:
        status_surface = font_status.render(status_text, True, status_color)
        screen.blit(status_surface, status_surface.get_rect(center=(WIDTH // 2, 230)))

    pygame.display.flip()

pygame.quit()