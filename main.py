import os
import sys
import pygame
from datetime import datetime

# ==============================================================================
# 1. تهيئة المسارات واستدعاء الموديولات
# ==============================================================================
DATA_DIR = "data"
REPORTS_DIR = "reports"
for d in [DATA_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

# استدعاء الموديولات الأساسية
try:
    from storage import JSONStorageManager
    storage_mgr = JSONStorageManager()
except ImportError:
    storage_mgr = None

try:
    from user import UserSystem, run_gui as run_user_gui
    from transaction import create_transaction, get_transaction_history, TransactionGUI
    from materials import materialmanager, MaterialManagerGUI
    from reward import RewardManager, RewardManagerGUI
    from redemption import Redemption, RedemptionGUI
    from receipt import generate_receipt
    from mapping import LocationService, MachineManager, MappingGUI
except ImportError as e:
    print(f"[Import Warning]: {e}")
    materialmanager = None
    RewardManager = None
    Redemption = None

# ==============================================================================
# 2. الثيم الموحد والألوان (مطابق لملفات user / transaction / materials)
# ==============================================================================
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
    "gold": (217, 119, 6)
}

# ==============================================================================
# 3. مكونات واجهة المستخدم (Buttons & Inputs)
# ==============================================================================
class Button:
    def __init__(self, x, y, w, h, text, bg, hbg, action=None, text_color=PALETTE["text_white"]):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.bg = bg
        self.hbg = hbg
        self.action = action
        self.tc = text_color
        self.hovered = False

    def draw(self, surf, mpos, font, is_active=False):
        self.hovered = self.rect.collidepoint(mpos)
        if is_active:
            pygame.draw.rect(surf, PALETTE["sidebar_active"], self.rect, border_radius=6)
            pygame.draw.rect(surf, PALETTE["card_border"], self.rect, 1, border_radius=6)
            pygame.draw.rect(surf, PALETTE["accent_blue"], (self.rect.x, self.rect.y, 5, self.rect.h), border_radius=2)
            txt_color = PALETTE["accent_blue"]
        else:
            bg_color = self.hbg if self.hovered else self.bg
            pygame.draw.rect(surf, bg_color, self.rect, border_radius=6)
            txt_color = self.tc

        t_surf = font.render(self.text, True, txt_color)
        surf.blit(t_surf, t_surf.get_rect(center=self.rect.center))

    def check(self, mpos):
        if self.rect.collidepoint(mpos) and self.action:
            self.action()


class InputField:
    def __init__(self, x, y, w, h, label, placeholder=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.text = ""
        self.placeholder = placeholder
        self.active = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_TAB:
                self.active = False
            elif len(self.text) < 20 and event.unicode.isprintable():
                self.text += event.unicode

    def draw(self, surf, f_sm, f_bd):
        if self.label:
            label_surf = f_sm.render(self.label, True, PALETTE["text_dark"])
            surf.blit(label_surf, (self.rect.x, self.rect.y - 18))

        pygame.draw.rect(surf, PALETTE["input_bg"], self.rect, border_radius=6)
        border_color = PALETTE["input_focus"] if self.active else PALETTE["input_border"]
        pygame.draw.rect(surf, border_color, self.rect, 2 if self.active else 1, border_radius=6)

        display_text = self.text if self.text else self.placeholder
        color = PALETTE["text_dark"] if self.text else PALETTE["text_muted"]
        text_surf = f_bd.render(display_text, True, color)
        surf.blit(text_surf, (self.rect.x + 10, self.rect.y + 8))

# ==============================================================================
# 4. Hub التطبيق الرئيسي والربط الشامل
# ==============================================================================
def main():
    pygame.init()
    screen_w, screen_h = 1000, 650
    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("EcoReward - RVM Main Operating Hub")
    clock = pygame.time.Clock()

    # الخطوط
    f_title = pygame.font.SysFont("Segoe UI", 18, bold=True)
    f_sub = pygame.font.SysFont("Segoe UI", 15, bold=True)
    f_btn = pygame.font.SysFont("Segoe UI", 13, bold=True)
    f_body = pygame.font.SysFont("Segoe UI", 13)
    f_label = pygame.font.SysFont("Segoe UI", 12, bold=True)
    f_status = pygame.font.SysFont("Segoe UI", 12, bold=True)

    # تهيئة الخدمات
    mat_manager = materialmanager() if materialmanager else None
    user_sys = UserSystem() if 'UserSystem' in globals() else None

    # الحالة العامة
    state = {
        "view": "dashboard",
        "user": None,  # المستخدم المسجل حالياً
        "current_machine": {"machine_id": "M001", "name": "Main Metro Station"},
        "cart_items": [],
        "session_points": 0,
        "selected_mat": None,
        "msg": "Welcome to EcoReward Main Hub. Please login or select a service.",
        "msg_color": PALETTE["text_dark"]
    }

    # دوال التنقل والعمليات
    def set_view(v):
        state["view"] = v

    def open_auth():
        # فتح نافذة المستخدمين وإرجاع المستخدم الحالي
        logged_user = run_user_gui()
        if logged_user:
            state["user"] = logged_user
            state["msg"] = f"Logged in as {logged_user.name} ({logged_user.points} Pts)"
            state["msg_color"] = PALETTE["accent_green"]
        # إعادة تعيين نافذة العرض للـ Main Hub بعد العودة
        pygame.display.set_mode((screen_w, screen_h))
        pygame.display.set_caption("EcoReward - RVM Main Operating Hub")

    def open_map():
        u_lat, u_lon = LocationService.get_current_user_location()
        mgr = MachineManager()
        gui = MappingGUI(u_lat, u_lon, mgr)
        gui.run()
        pygame.display.set_mode((screen_w, screen_h))
        pygame.display.set_caption("EcoReward - RVM Main Operating Hub")

    def open_rewards():
        if RewardManager:
            mgr = RewardManager()
            gui = RewardManagerGUI(mgr)
            gui.run()
            pygame.display.set_mode((screen_w, screen_h))
            pygame.display.set_caption("EcoReward - RVM Main Operating Hub")

    def open_redemption():
        if Redemption:
            u_id = state["user"].user_id if state["user"] else "GUEST"
            u_pts = state["user"].points if state["user"] else 0
            gui = RedemptionGUI(Redemption(), user_id=u_id, user_points=u_pts)
            gui.run()
            if state["user"]:
                # تحديث النقاط بعد الاستبدال
                user_data = user_sys._find_by_email(state["user"].email)
                if user_data:
                    state["user"] = user_data
            pygame.display.set_mode((screen_w, screen_h))
            pygame.display.set_caption("EcoReward - RVM Main Operating Hub")

    def open_history():
        gui = TransactionGUI()
        gui.run()
        pygame.display.set_mode((screen_w, screen_h))
        pygame.display.set_caption("EcoReward - RVM Main Operating Hub")

    # مدخلات التدوير
    inp_weight = InputField(250, 470, 150, 36, "Weight / Qty (kg)", "e.g. 2.5")

    def add_to_recycle():
        if not state["selected_mat"]:
            state["msg"] = "Please click a material from the table first!"
            state["msg_color"] = PALETTE["btn_danger"]
            return
        try:
            qty = float(inp_weight.text.strip())
            if qty <= 0:
                raise ValueError
            mat = state["selected_mat"]
            earned = int(mat["points_per_kg"] * qty)
            state["cart_items"].append({
                "name": mat["material_name"],
                "quantity": qty,
                "points_per_unit": mat["points_per_kg"],
                "points_earned": earned
            })
            state["session_points"] += earned
            state["msg"] = f"Added {qty}kg of {mat['material_name']} (+{earned} Pts)"
            state["msg_color"] = PALETTE["accent_green"]
            inp_weight.text = ""
        except ValueError:
            state["msg"] = "Please enter a valid numeric weight!"
            state["msg_color"] = PALETTE["btn_danger"]

    def finish_recycling():
        if not state["cart_items"]:
            state["msg"] = "Insertion cart is empty. Add materials first!"
            state["msg_color"] = PALETTE["btn_danger"]
            return

        user_info = {
            "id": state["user"].user_id if state["user"] else "GUEST_USER",
            "user_id": state["user"].user_id if state["user"] else "GUEST_USER",
            "name": state["user"].name if state["user"] else "Guest Recycler",
            "points": state["user"].points if state["user"] else 0
        }

        # حفظ المعاملة وتحديث رصيد المستخدم
        txn = create_transaction(user_info, state["current_machine"], state["cart_items"])
        
        # عرض الإيصال
        generate_receipt(txn)
        pygame.display.set_mode((screen_w, screen_h))
        pygame.display.set_caption("EcoReward - RVM Main Operating Hub")

        if state["user"]:
            state["user"].points = user_info["points"]

        state["cart_items"] = []
        state["session_points"] = 0
        state["msg"] = f"Recycling completed! TXN ID: {txn.transaction_id}"
        state["msg_color"] = PALETTE["accent_green"]

    # أزرار القائمة الجانبية الموحدة
    sidebar_buttons = [
        Button(15, 75, 190, 42, "Dashboard Hub", PALETTE["sidebar_bg"], PALETTE["sidebar_hover"], lambda: set_view("dashboard"), PALETTE["text_dark"]),
        Button(15, 125, 190, 42, "Recycle Material", PALETTE["sidebar_bg"], PALETTE["sidebar_hover"], lambda: set_view("recycle"), PALETTE["text_dark"]),
        Button(15, 175, 190, 42, "User Account / Auth", PALETTE["sidebar_bg"], PALETTE["sidebar_hover"], open_auth, PALETTE["text_dark"]),
        Button(15, 225, 190, 42, "Rewards Catalog", PALETTE["sidebar_bg"], PALETTE["sidebar_hover"], open_rewards, PALETTE["text_dark"]),
        Button(15, 275, 190, 42, "Redeem Points", PALETTE["sidebar_bg"], PALETTE["sidebar_hover"], open_redemption, PALETTE["text_dark"]),
        Button(15, 325, 190, 42, "Transactions Log", PALETTE["sidebar_bg"], PALETTE["sidebar_hover"], open_history, PALETTE["text_dark"]),
        Button(15, 375, 190, 42, "Find Machines Map", PALETTE["sidebar_bg"], PALETTE["sidebar_hover"], open_map, PALETTE["text_dark"]),
        Button(15, 580, 190, 40, "Exit Hub", PALETTE["btn_danger"], PALETTE["btn_danger_h"], sys.exit),
    ]

    # أزرار شاشة التدوير
    btn_add_mat = Button(420, 470, 140, 36, "Insert Item", PALETTE["btn_blue"], PALETTE["btn_blue_h"], add_to_recycle)
    btn_finish_recycle = Button(810, 580, 150, 42, "Finish & Print", PALETTE["btn_green"], PALETTE["btn_green_h"], finish_recycling)

    running = True
    while running:
        mpos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state["view"] == "recycle":
                inp_weight.handle(event)
                # اختيار مادة من الجدول
                if event.type == pygame.MOUSEBUTTONDOWN and 140 <= event.pos[1] <= 420 and 240 <= event.pos[0] <= 620:
                    materials = mat_manager.load_materials() if mat_manager else []
                    idx = (event.pos[1] - 140) // 45
                    if idx < len(materials):
                        state["selected_mat"] = materials[idx]
                        state["msg"] = f"Selected: {materials[idx]['material_name']} ({materials[idx]['points_per_kg']} Pts/kg)"
                        state["msg_color"] = PALETTE["accent_blue"]

            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn in sidebar_buttons:
                    btn.check(mpos)
                if state["view"] == "recycle":
                    btn_add_mat.check(mpos)
                    btn_finish_recycle.check(mpos)

        # رسم الخلفيات
        screen.fill(PALETTE["main_bg"])

        # Header Bar
        pygame.draw.rect(screen, PALETTE["header_bg"], (0, 0, screen_w, 56))
        screen.blit(f_title.render("EcoReward - Automated Reverse Vending Hub", True, PALETTE["header_title"]), (20, 16))
        
        # User Status Badge
        user_label = f"User: {state['user'].name} | {state['user'].points} Pts" if state["user"] else "User: Guest / Not Logged In"
        screen.blit(f_body.render(user_label, True, PALETTE["gold"] if state["user"] else PALETTE["text_white"]), (700, 20))

        # Sidebar
        pygame.draw.rect(screen, PALETTE["sidebar_bg"], (0, 56, 220, screen_h - 56))
        pygame.draw.line(screen, PALETTE["sidebar_border"], (220, 56), (220, screen_h), 1)

        for btn in sidebar_buttons:
            is_act = (btn.text == "Dashboard Hub" and state["view"] == "dashboard") or \
                     (btn.text == "Recycle Material" and state["view"] == "recycle")
            btn.draw(screen, mpos, f_btn, is_active=is_act)

        # System Status Bar
        status_box = pygame.Rect(240, 70, 730, 42)
        pygame.draw.rect(screen, PALETTE["card_bg"], status_box, border_radius=6)
        pygame.draw.rect(screen, PALETTE["card_border"], status_box, 1, border_radius=6)
        screen.blit(f_status.render(state["msg"], True, state["msg_color"]), (255, 83))

        # ==========================================
        # Dashboard View
        # ==========================================
        if state["view"] == "dashboard":
            # Welcome Card
            card = pygame.Rect(240, 130, 730, 220)
            pygame.draw.rect(screen, PALETTE["card_bg"], card, border_radius=8)
            pygame.draw.rect(screen, PALETTE["card_border"], card, 1, border_radius=8)

            screen.blit(f_sub.render("Welcome to EcoReward RVM Terminal", True, PALETTE["accent_blue"]), (265, 150))
            screen.blit(f_body.render("Insert recyclable materials to earn points and redeem them for real-world rewards.", True, PALETTE["text_dark"]), (265, 185))
            screen.blit(f_body.render(f"Current Machine ID : {state['current_machine']['machine_id']} ({state['current_machine']['name']})", True, PALETTE["text_muted"]), (265, 215))
            screen.blit(f_body.render("Quick Shortcuts:", True, PALETTE["text_dark"]), (265, 260))

            # Statistics Summary
            txns = get_transaction_history()
            stat_card = pygame.Rect(240, 370, 730, 180)
            pygame.draw.rect(screen, PALETTE["card_bg"], stat_card, border_radius=8)
            pygame.draw.rect(screen, PALETTE["card_border"], stat_card, 1, border_radius=8)
            screen.blit(f_sub.render("Machine Activity & Quick Stats", True, PALETTE["text_dark"]), (265, 390))
            screen.blit(f_body.render(f"• Total Recycling Operations : {len(txns)} transactions recorded", True, PALETTE["text_dark"]), (265, 430))
            screen.blit(f_body.render(f"• Current Active Machine     : {state['current_machine']['name']}", True, PALETTE["text_dark"]), (265, 460))
            screen.blit(f_body.render(f"• Database Connection        : JSON Storage Active", True, PALETTE["accent_green"]), (265, 490))

        # ==========================================
        # Recycle Flow View
        # ==========================================
        elif state["view"] == "recycle":
            # Material Selection Table
            mat_card = pygame.Rect(240, 125, 380, 320)
            pygame.draw.rect(screen, PALETTE["card_bg"], mat_card, border_radius=8)
            pygame.draw.rect(screen, PALETTE["card_border"], mat_card, 1, border_radius=8)
            screen.blit(f_sub.render("1. Select Material", True, PALETTE["accent_blue"]), (255, 135))

            materials = mat_manager.load_materials() if mat_manager else []
            y_off = 170
            for m in materials[:5]:
                is_sel = state["selected_mat"] and state["selected_mat"]["material_name"] == m["material_name"]
                row = pygame.Rect(250, y_off, 360, 38)
                if is_sel:
                    pygame.draw.rect(screen, (232, 245, 233), row, border_radius=4)
                    pygame.draw.rect(screen, PALETTE["btn_green"], row, 1, border_radius=4)
                screen.blit(f_body.render(m["material_name"], True, PALETTE["text_dark"]), (260, y_off + 10))
                screen.blit(f_body.render(f"{m['points_per_kg']} Pts/kg", True, PALETTE["accent_green"]), (520, y_off + 10))
                y_off += 45

            # Inputs
            inp_weight.draw(screen, f_label, f_body)
            btn_add_mat.draw(screen, mpos, f_btn)

            # Session Cart Table
            cart_card = pygame.Rect(640, 125, 330, 430)
            pygame.draw.rect(screen, PALETTE["card_bg"], cart_card, border_radius=8)
            pygame.draw.rect(screen, PALETTE["card_border"], cart_card, 1, border_radius=8)
            screen.blit(f_sub.render("2. Current Cart", True, PALETTE["accent_green"]), (655, 135))

            cy_off = 175
            for itm in state["cart_items"][-6:]:
                screen.blit(f_body.render(f"{itm['name']} ({itm['quantity']}kg)", True, PALETTE["text_dark"]), (655, cy_off))
                screen.blit(f_body.render(f"+{itm['points_earned']} Pts", True, PALETTE["gold"]), (900, cy_off))
                cy_off += 30

            pygame.draw.line(screen, PALETTE["card_border"], (655, 480), (950, 480), 1)
            screen.blit(f_sub.render("Total Points:", True, PALETTE["text_dark"]), (655, 500))
            screen.blit(f_sub.render(f"{state['session_points']} Pts", True, PALETTE["accent_green"]), (890, 500))

            btn_finish_recycle.draw(screen, mpos, f_btn)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()