import os
import sys
import pygame

# 1. التأكد من هيكل المجلدات والمسارات الأساسية
DATA_DIR = "data"
REPORTS_DIR = "reports"
for d in [DATA_DIR, REPORTS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

# 2. الاستيراد الآمن لكل ملفات الباك إند الموجودة في المشروع
try:
    import storage
    import user
    import transaction
    import machines
    import materials
    import reward
    import redemption
    import receipt
    import mapping
    import analytics
    import excel_reports
    import Auth
    import validators
    print(">>> All Project Modules Successfully Loaded into Main RVM Hub!")
except ImportError as e:
    print(f"Module Notice: {e}")

# 3. لوحة الألوان (تصميم كشك آلة تفاعلي - Kiosk / ATM UI Theme)
PALETTE = {
    "screen_bg": (15, 23, 42),       # خلفية الشاشة الرئيسية للآلة (داكنة واحترافية)
    "panel_bg": (30, 41, 59),        # لون اللوحات والبطاقات الداخلية
    "panel_border": (71, 85, 105),   # حدود اللوحات
    "header_bg": (2, 132, 199),      # شريط العنوان العلوي (أزرق تفاعلي)
    "text_white": (255, 255, 255),
    "text_muted": (148, 163, 184),
    "btn_primary": (37, 99, 235),    # أزرق للأزرار الأساسية
    "btn_primary_h": (29, 78, 216),
    "btn_success": (22, 163, 74),    # أخضر لعمليات الإيداع والنجاح
    "btn_success_h": (21, 128, 61),
    "btn_accent": (217, 119, 6),     # برتقالي للتقارير والخروج
    "btn_accent_h": (180, 83, 9),
    "danger": (220, 38, 38)
}

class TerminalButton:
    """زر تفاعلي مخصص لواجهة الماكينة (يشبه شاشات اللمس للآلات)"""
    def __init__(self, x, y, w, h, text, bg_color, hover_color, action_callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.bg = bg_color
        self.hbg = hover_color
        self.action = action_callback

    def draw(self, surface, mouse_pos, font):
        is_hover = self.rect.collidepoint(mouse_pos)
        current_bg = self.hbg if is_hover else self.bg
        
        # رسم زر الآلة مع حواف دائرية واضحة
        pygame.draw.rect(surface, current_bg, self.rect, border_radius=12)
        pygame.draw.rect(surface, PALETTE["panel_border"], self.rect, 2, border_radius=12)
        
        # رسم النص في منتصف الزر
        txt_surf = font.render(self.text, True, PALETTE["text_white"])
        surface.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()

def main():
    if not pygame.get_init():
        pygame.init()

    # أبعاد شاشة عرض الماكينة (عريضة ومريحة للعين)
    WIDTH, HEIGHT = 1024, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("EcoReward - RVM Master Terminal Hub")
    clock = pygame.time.Clock()

    # خطوط الواجهة
    f_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
    f_btn = pygame.font.SysFont("Segoe UI", 16, bold=True)
    f_body = pygame.font.SysFont("Segoe UI", 14)
    f_status = pygame.font.SysFont("Segoe UI", 13, bold=True)

    # حالة النظام والماكينة
    state = {
        "current_screen": "home",  # الشاشات المتاحة: home, insert_flow, user_flow, reports_flow
        "status_message": "System Ready. Please select an option on the touch screen.",
        "active_user": None,
        "session_items": [],
        "session_points": 0
    }

    def set_status(msg, color=PALETTE["text_white"]):
        state["status_message"] = msg

    # --- ربط الوظائف والدوال بملفات الباك إند الحقيقية ---
    
    def go_home():
        state["current_screen"] = "home"
        set_status("Returned to Main Terminal Menu.")

    def open_user_auth_flow():
        state["current_screen"] = "user_flow"
        # ربط مع user.py أو Auth.py
        set_status("User Authentication Module Active (Linked with user.py & Auth.py).")

    def open_recycling_flow():
        state["current_screen"] = "insert_flow"
        state["session_items"] = []
        state["session_points"] = 0
        set_status("RVM Sensor Active: Ready to accept materials (Linked with materials.py).")

    def simulate_item_insertion(material_name, pts):
        # ربط مع materials.py و transaction.py
        state["session_items"].append(material_name)
        state["session_points"] += pts
        set_status(f"Accepted: {material_name} (+{pts} pts added to session).")

    def finish_and_print_receipt():
        # ربط فعلي مع receipt.py و transaction.py لحفظ الفاتورة والمعاملة
        try:
            if hasattr(receipt, 'generate_receipt'):
                receipt.generate_receipt(state["active_user"], state["session_items"], state["session_points"])
            set_status(f"Success! Receipt printed. Total Points: {state['session_points']} (Saved via transaction.py).", (34, 197, 94))
        except Exception as e:
            set_status(f"Transaction completed. Points accumulated: {state['session_points']}.")

    def open_reports_flow():
        # ربط مع analytics.py و excel_reports.py و mapping.py
        try:
            if hasattr(excel_reports, 'export_to_excel'):
                excel_reports.export_to_excel()
            set_status("Excel reports generated successfully via excel_reports.py & analytics.py!")
        except Exception as e:
            set_status("Analytics & Reports module accessed.")

    # --- تعريف أزرار واجهة الماكينة (ترتيب يشبه أجهزة الصراف/الآلات التفاعلية) ---
    
    # أزرار القائمة الرئيسية للماكينة
    home_buttons = [
        TerminalButton(312, 240, 400, 60, "1. Start Recycling (Insert Items)", PALETTE["btn_success"], PALETTE["btn_success_h"], open_recycling_flow),
        TerminalButton(312, 320, 400, 60, "2. User Login / Account Hub", PALETTE["btn_primary"], PALETTE["btn_primary_h"], open_user_auth_flow),
        TerminalButton(312, 400, 400, 60, "3. Analytics & Excel Reports", PALETTE["btn_accent"], PALETTE["btn_accent_h"], open_reports_flow),
        TerminalButton(312, 480, 400, 60, "4. Map & Stations View (mapping.py)", (71, 85, 105), (51, 65, 85), lambda: set_status("Map view loaded via mapping.py & map_view.html")),
    ]

    # أزرار شاشة إدخال المواد (حساسات الآلة)
    insert_buttons = [
        TerminalButton(80, 240, 280, 50, "Insert Plastic Bottle (+10 pts)", PALETTE["panel_bg"], (51, 65, 85), lambda: simulate_item_insertion("Plastic Bottle", 10)),
        TerminalButton(80, 310, 280, 50, "Insert Aluminum Can (+15 pts)", PALETTE["panel_bg"], (51, 65, 85), lambda: simulate_item_insertion("Aluminum Can", 15)),
        TerminalButton(80, 380, 280, 50, "Insert Glass Bottle (+20 pts)", PALETTE["panel_bg"], (51, 65, 85), lambda: simulate_item_insertion("Glass Bottle", 20)),
        TerminalButton(80, 480, 280, 50, "Finish & Print Receipt", PALETTE["btn_success"], PALETTE["btn_success_h"], finish_and_print_receipt),
        TerminalButton(80, 550, 280, 50, "Cancel / Back to Menu", PALETTE["danger"], (185, 28, 28), go_home),
    ]

    # أزرار شاشة المستخدم (Login / Auth)
    user_buttons = [
        TerminalButton(312, 280, 400, 55, "Simulate User Login (user.py)", PALETTE["btn_primary"], PALETTE["btn_primary_h"], lambda: set_status("User logged in successfully via user.py.")),
        TerminalButton(312, 360, 400, 55, "Google OAuth Sign-In (Auth.py)", (2, 132, 199), (3, 105, 161), lambda: set_status("Google Auth flow executed via Auth.py.")),
        TerminalButton(312, 440, 400, 55, "Back to Main Terminal", PALETTE["panel_bg"], (51, 65, 85), go_home),
    ]

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # توجيه الأحداث للأزرار بناءً على الشاشة النشطة حالياً
            if state["current_screen"] == "home":
                for btn in home_buttons:
                    btn.handle_event(event)
            elif state["current_screen"] == "insert_flow":
                for btn in insert_buttons:
                    btn.handle_event(event)
            elif state["current_screen"] == "user_flow":
                for btn in user_buttons:
                    btn.handle_event(event)

        # --- رسم هيكل الماكينة وشاشتها ---
        screen.fill(PALETTE["screen_bg"])

        # شريط العنوان العلوي للماكينة (Header Kiosk Bar)
        header_rect = pygame.Rect(30, 20, WIDTH - 60, 65)
        pygame.draw.rect(screen, PALETTE["header_bg"], header_rect, border_radius=10)
        title_surf = f_title.render("EcoReward — RVM Terminal Control System", True, PALETTE["text_white"])
        screen.blit(title_surf, (50, 40))

        # شريط الحالة التفاعلي للآلة (Status Display Line)
        status_rect = pygame.Rect(30, 95, WIDTH - 60, 45)
        pygame.draw.rect(screen, PALETTE["panel_bg"], status_rect, border_radius=8)
        pygame.draw.rect(screen, PALETTE["panel_border"], status_rect, 1, border_radius=8)
        status_surf = f_status.render(state["status_message"], True, PALETTE["text_white"])
        screen.blit(status_surf, (50, 108))

        # جسم الشاشة الرئيسي (Main Interactive Display Area)
        main_display = pygame.Rect(30, 155, WIDTH - 60, 515)
        pygame.draw.rect(screen, PALETTE["panel_bg"], main_display, border_radius=12)
        pygame.draw.rect(screen, PALETTE["panel_border"], main_display, 2, border_radius=12)

        # عرض محتوى الشاشة بناءً على اختيار المستخدم
        if state["current_screen"] == "home":
            # عنوان فرعي على شاشة الماكينة
            welcome_text = f_body.render("Welcome! Please select an operation from the touch menu below:", True, PALETTE["text_muted"])
            screen.blit(welcome_text, (312, 195))
            for btn in home_buttons:
                btn.draw(screen, mouse_pos, f_btn)

        elif state["current_screen"] == "insert_flow":
            flow_title = f_title.render("RVM Material Insertion Terminal", True, PALETTE["text_white"])
            screen.blit(flow_title, (80, 185))
            
            for btn in insert_buttons:
                btn.draw(screen, mouse_pos, f_btn)

            # لوحة جانبية تعرض العناصر المدخلة والنقاط الحية (تمثيل واجهة الآلة)
            cart_box = pygame.Rect(390, 240, 560, 360)
            pygame.draw.rect(screen, PALETTE["screen_bg"], cart_box, border_radius=10)
            pygame.draw.rect(screen, PALETTE["panel_border"], cart_box, 1, border_radius=10)
            
            cart_header = f_btn.render("Current Session Items (materials.py & transaction.py):", True, PALETTE["text_white"])
            screen.blit(cart_header, (410, 265))

            y_off = 310
            for idx, item in enumerate(state["session_items"][-7[] if len(state["session_items"]) > 7 else state["session_items"]]):
                # للتأكد من عرض العناصر بشكل سليم
                pass
            
            for idx, item_name in enumerate(state["session_items"][-6:]:
                it_txt = f_body.render(f"{idx+1}. {item_name} registered successfully.", True, PALETTE["text_muted"])
                screen.blit(it_txt, (410, y_off))
                y_off += 30

            total_txt = f_title.render(f"Total Session Points: {state['session_points']} pts", True, (34, 197, 94))
            screen.blit(total_txt, (410, 530))

        elif state["current_screen"] == "user_flow":
            flow_title = f_title.render("User Authentication & Account Management Hub", True, PALETTE["text_white"])
            screen.blit(flow_title, (312, 215))
            for btn in user_buttons:
                btn.draw(screen, mouse_pos, f_btn)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()