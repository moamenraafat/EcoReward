import sys
import os
import json
from datetime import datetime
import pygame

# ==============================================================================
# 0. استدعاء موديول Reward الحقيقي (مع وجود fall-back للتجربة المنفصلة)
# ==============================================================================
try:
    from reward import RewardManager as Reward
except ImportError:
    try:
        from reward import Reward
    except ImportError:
        class Reward:
            """Mock Class للتجربة المنفصلة فقط في حال عدم وجود reward.py"""
            def get_reward_by_id(self, reward_id):
                rewards = {
                    "R101": {"reward_id": "R101", "name": "10 EGP Discount Voucher", "points_required": 100, "is_available": True},
                    "R102": {"reward_id": "R102", "name": "Free Metro Ticket", "points_required": 150, "is_available": True},
                    "R103": {"reward_id": "R103", "name": "Eco Shopping Bag", "points_required": 300, "is_available": False},
                }
                return rewards.get(reward_id, None)


# ==============================================================================
# 1. كود اللوجيك واستبدال النقاط
# ==============================================================================
class Redemption:

    REDEMPTIONS_FILE = os.path.join("data", "redemptions.json")

    def __init__(self):
        pass
        
    def load_redemptions(self):
        if not os.path.exists(self.REDEMPTIONS_FILE):
            return []
        try:
            with open(self.REDEMPTIONS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            print(f"[Redemption Error] Failed to load JSON: {e}")
            return []

    def save_redemptions(self, redemptions):
        os.makedirs("data", exist_ok=True)
        try:
            with open(self.REDEMPTIONS_FILE, "w", encoding="utf-8") as file:
                json.dump(redemptions, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Redemption Error] Failed to save JSON: {e}")

    def redeem_reward(self, user_id, user_points, reward_id):
        reward_manager = Reward()
        
        # التأكد من دعم أنواع الاستدعاء المختلفة في موديول المكافآت
        if hasattr(reward_manager, 'get_reward_by_id'):
            reward = reward_manager.get_reward_by_id(reward_id)
        elif hasattr(reward_manager, 'find_reward'):
            reward = reward_manager.find_reward(reward_id)
        else:
            reward = None

        if not reward:
            print("❌ Reward not found.")
            return False, user_points

        is_available = reward.get("is_available", True)
        points_required = reward.get("points_required", reward.get("points", 0))

        if not is_available:
            print("❌ Reward is currently unavailable.")
            return False, user_points

        # 2. Check Balance
        if user_points < points_required:
            print(f"❌ Insufficient points. You need {points_required} points.")
            return False, user_points

        # 3. Deduct Points
        new_balance = user_points - points_required

        # 4. Save Redemption Log
        redemption_record = {
            "redemption_id": f"RED-{int(datetime.now().timestamp())}",
            "user_id": user_id,
            "reward_id": reward_id,
            "reward_name": reward.get("name", "Unknown Reward"),
            "points_used": points_required,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        redemptions = self.load_redemptions()
        redemptions.append(redemption_record)
        self.save_redemptions(redemptions)

        print(f"✅ Success! You redeemed '{reward.get('name')}'. Remaining points: {new_balance}")
        return True, new_balance

    def get_redemption_history(self, user_id):
        redemptions = self.load_redemptions()
        user_history = [r for r in redemptions if r.get("user_id") == user_id]
        return user_history


# ==============================================================================
# 2. واجهة Pygame GUI
# ==============================================================================

class Button:
    def __init__(self, x, y, width, height, text, bg_color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface, font):
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (200, 205, 210), self.rect, width=1, border_radius=6)

        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos, event_type):
        return self.is_hovered and event_type == pygame.MOUSEBUTTONDOWN


class InputBox:
    def __init__(self, x, y, w, h, placeholder=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (200, 205, 210)
        self.color_active = (76, 175, 80)
        self.color = self.color_inactive
        self.text = ""
        self.placeholder = placeholder
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key != pygame.K_RETURN:
                self.text += event.unicode

    def draw(self, screen, font):
        pygame.draw.rect(screen, (255, 255, 255), self.rect, border_radius=5)
        pygame.draw.rect(screen, self.color, self.rect, 2, border_radius=5)
        
        display_text = self.text if self.text else self.placeholder
        text_color = (33, 33, 33) if self.text else (150, 150, 150)
        txt_surface = font.render(display_text, True, text_color)
        screen.blit(txt_surface, (self.rect.x + 10, self.rect.y + 10))


class RedemptionGUI:
    def __init__(self, redemption_manager: Redemption, user_id="U001", user_points=1000):
        self.manager = redemption_manager
        self.user_id = user_id
        self.user_points = user_points
        self.width = 900
        self.height = 620

    def run(self):
        if not pygame.get_init():
            pygame.init()

        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EcoReward - Rewards Redemption Hub")

        # الألوان
        BG_COLOR = (245, 247, 250)
        WHITE = (255, 255, 255)
        DARK_HEADER = (35, 45, 60)
        PRIMARY_GREEN = (46, 125, 50)
        TEXT_DARK = (33, 33, 33)
        GOLD_COLOR = (255, 179, 0)

        # الخطوط
        FONT_TITLE = pygame.font.SysFont("Arial", 20, bold=True)
        FONT_BODY = pygame.font.SysFont("Arial", 14)
        FONT_BOLD = pygame.font.SysFont("Arial", 14, bold=True)
        FONT_BTN = pygame.font.SysFont("Arial", 13, bold=True)

        input_reward_id = InputBox(30, 540, 220, 40, "Enter Reward ID (e.g. R101)")
        btn_redeem = Button(260, 540, 160, 40, "Redeem Reward", PRIMARY_GREEN, (76, 175, 80))

        status_msg = f"Logged in as {self.user_id} | Available Points: {self.user_points}"

        clock = pygame.time.Clock()
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                input_reward_id.handle_event(event)

                if btn_redeem.is_clicked(mouse_pos, event.type):
                    target_id = input_reward_id.text.strip()
                    if target_id:
                        success, new_pts = self.manager.redeem_reward(self.user_id, self.user_points, target_id)
                        if success:
                            self.user_points = new_pts
                            status_msg = f"✅ Success! Reward '{target_id}' redeemed. Remaining: {self.user_points} Pts"
                            input_reward_id.text = ""
                        else:
                            status_msg = f"❌ Failed to redeem '{target_id}'. Check ID, balance, or availability."
                    else:
                        status_msg = "Please enter a valid Reward ID!"

            btn_redeem.check_hover(mouse_pos)
            screen.fill(BG_COLOR)

            # Header
            pygame.draw.rect(screen, DARK_HEADER, (0, 0, self.width, 65))
            screen.blit(FONT_TITLE.render("EcoReward - Rewards & Redemption Center", True, WHITE), (20, 20))
            screen.blit(FONT_BOLD.render(f"Balance: {self.user_points} Pts", True, GOLD_COLOR), (730, 22))

            # Banner Status
            status_box = pygame.Rect(30, 75, self.width - 60, 35)
            pygame.draw.rect(screen, WHITE, status_box, border_radius=6)
            pygame.draw.rect(screen, (220, 225, 230), status_box, width=1, border_radius=6)
            screen.blit(FONT_BODY.render(status_msg, True, TEXT_DARK), (40, 83))

            # Section Title: History Table
            screen.blit(FONT_BOLD.render(f"Redemption History for {self.user_id}:", True, TEXT_DARK), (30, 125))

            # جدول عرض سجل الاستبدالات
            list_rect = pygame.Rect(30, 150, self.width - 60, 360)
            pygame.draw.rect(screen, WHITE, list_rect, border_radius=8)
            pygame.draw.rect(screen, (220, 225, 230), list_rect, width=1, border_radius=8)

            # Table Header
            pygame.draw.rect(screen, (240, 243, 246), (30, 150, self.width - 60, 35), border_top_left_radius=8, border_top_right_radius=8)
            screen.blit(FONT_BOLD.render("DATE & TIME", True, TEXT_DARK), (50, 158))
            screen.blit(FONT_BOLD.render("REWARD NAME", True, TEXT_DARK), (320, 158))
            screen.blit(FONT_BOLD.render("POINTS USED", True, TEXT_DARK), (680, 158))

            # عرض قائمة السجلات
            history = self.manager.get_redemption_history(self.user_id)
            y_offset = 195

            if history:
                for item in history[:6]:
                    row_rect = pygame.Rect(35, y_offset - 5, self.width - 70, 40)
                    pygame.draw.rect(screen, (250, 250, 252), row_rect, border_radius=5)

                    screen.blit(FONT_BODY.render(str(item.get("date", "N/A")), True, TEXT_DARK), (50, y_offset + 5))
                    screen.blit(FONT_BODY.render(str(item.get("reward_name", "N/A")), True, TEXT_DARK), (320, y_offset + 5))
                    screen.blit(FONT_BOLD.render(f"-{item.get('points_used', 0)} Pts", True, (211, 47, 47)), (680, y_offset + 5))

                    y_offset += 45
            else:
                screen.blit(FONT_BODY.render("No redemptions found for this user.", True, (150, 150, 150)), (50, 205))

            # رسم أدوات الإدخال والأزرار
            input_reward_id.draw(screen, FONT_BODY)
            btn_redeem.draw(screen, FONT_BTN)

            pygame.display.flip()
            clock.tick(60)


# --- تشغيل وتجربة الكود ---
if __name__ == "__main__":
    redemption_mgr = Redemption()
    gui = RedemptionGUI(redemption_mgr, user_id="U001", user_points=1000)
    gui.run()