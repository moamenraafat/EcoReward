import sys
import os
import json
import pygame

# ==============================================================================
# 1. كود إدارة المكافآت (Business Logic)
# ==============================================================================
class Reward:
    def __init__(self, reward_id, name, points_required, is_available):
        self.reward_id = reward_id
        self.name = name
        self.points_required = points_required
        self.is_available = is_available

    def to_dict(self):
        return {
            "reward_id": self.reward_id,
            "name": self.name,
            "points_required": self.points_required,
            "is_available": self.is_available
        }

class RewardManager:
    REWORDS_FILE = os.path.join("data", "rewards.json")

    def load_rewards(self):
        if not os.path.exists(self.REWORDS_FILE):
            return []
        try:
            with open(self.REWORDS_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            rewards = []

            for r in data:
                reward = Reward(
                    r["reward_id"],
                    r["name"],
                    r["points_required"],
                    r["is_available"]
                )
                rewards.append(reward)
            return rewards
        except Exception as e:
            print(f"[RewardManager Error] {e}")
            return []

    def show_rewards(self):
        rewards = self.load_rewards()

        print("\n--- Available Rewards ---")
        for r in rewards:
            status = "Available" if r.is_available else "Out of Stock"
            print(
                f"ID: {r.reward_id} \n "
                f"Name: {r.name} \n "
                f"Points: {r.points_required} \n "
                f"Status: {status}"
            )
            print("_"*30)
        return rewards

    def check_reward_availability(self, reward_id):
        rewards = self.load_rewards()

        for r in rewards:
            if r.reward_id == reward_id:
                return r.is_available, r

        return False, None

    # دالة مساعدة سريعة لربطها بـ redemption.py
    def get_reward_by_id(self, reward_id):
        is_avail, reward_obj = self.check_reward_availability(reward_id)
        if reward_obj:
            return reward_obj.to_dict()
        return None


# ==============================================================================
# 2. واجهة Pygame GUI
# ==============================================================================

class Button:
    """زر تفاعلي للواجهة الرسومية"""
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
    """صندوق إدخال نصوص تفاعلي"""
    def __init__(self, x, y, w, h, placeholder=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (200, 205, 210)
        self.color_active = (33, 150, 243)
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


class RewardManagerGUI:
    """واجهة استعراض المكافآت الرسومية بـ Pygame"""
    def __init__(self, manager: RewardManager):
        self.manager = manager
        self.width = 900
        self.height = 620

    def run(self):
        if not pygame.get_init():
            pygame.init()
            
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EcoReward - Rewards Catalog Visualizer")

        # الألوان
        BG_COLOR = (245, 247, 250)
        WHITE = (255, 255, 255)
        DARK_HEADER = (35, 45, 60)
        PRIMARY_BLUE = (33, 150, 243)
        GREEN_COLOR = (46, 125, 50)
        RED_COLOR = (211, 47, 47)
        TEXT_DARK = (33, 33, 33)
        GOLD_COLOR = (255, 179, 0)

        # الخطوط
        FONT_TITLE = pygame.font.SysFont("Arial", 20, bold=True)
        FONT_BODY = pygame.font.SysFont("Arial", 14)
        FONT_BOLD = pygame.font.SysFont("Arial", 14, bold=True)
        FONT_BTN = pygame.font.SysFont("Arial", 13, bold=True)

        input_check_id = InputBox(30, 540, 220, 40, "Check ID (e.g. R101)")
        btn_check = Button(260, 540, 160, 40, "Check Availability", PRIMARY_BLUE, (66, 165, 245))

        status_msg = "Select or search a Reward ID to check availability status."
        selected_reward_id = None

        clock = pygame.time.Clock()
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                input_check_id.handle_event(event)

                # اختيار مكافأة من القائمة
                if event.type == pygame.MOUSEBUTTONDOWN and event.pos[1] >= 130 and event.pos[1] <= 480:
                    rewards = self.manager.load_rewards()
                    clicked_index = (event.pos[1] - 130) // 55
                    if clicked_index < len(rewards):
                        selected_reward_id = rewards[clicked_index].reward_id
                        status_msg = f"Selected Reward ID: '{selected_reward_id}'"

                # زر فحص التوفر
                if btn_check.is_clicked(mouse_pos, event.type):
                    target_id = input_check_id.text.strip() if input_check_id.text else selected_reward_id
                    if target_id:
                        is_avail, reward_obj = self.manager.check_reward_availability(target_id)
                        if reward_obj:
                            st_text = "Available" if is_avail else "Out of Stock"
                            status_msg = f"Reward '{reward_obj.name}' ({target_id}) Status: {st_text}"
                        else:
                            status_msg = f"❌ Reward ID '{target_id}' not found in catalog!"
                    else:
                        status_msg = "Please select or type a Reward ID first!"

            btn_check.check_hover(mouse_pos)
            screen.fill(BG_COLOR)

            # Header
            pygame.draw.rect(screen, DARK_HEADER, (0, 0, self.width, 65))
            screen.blit(FONT_TITLE.render("EcoReward - Rewards Catalog", True, WHITE), (20, 20))

            # Banner Status
            status_box = pygame.Rect(30, 75, self.width - 60, 35)
            pygame.draw.rect(screen, WHITE, status_box, border_radius=6)
            pygame.draw.rect(screen, (220, 225, 230), status_box, width=1, border_radius=6)
            screen.blit(FONT_BODY.render(f"System Status: {status_msg}", True, TEXT_DARK), (40, 83))

            # جدول/كروت عرض المكافآت
            list_rect = pygame.Rect(30, 120, self.width - 60, 390)
            pygame.draw.rect(screen, WHITE, list_rect, border_radius=8)
            pygame.draw.rect(screen, (220, 225, 230), list_rect, width=1, border_radius=8)

            # Table Header
            pygame.draw.rect(screen, (240, 243, 246), (30, 120, self.width - 60, 40), border_top_left_radius=8, border_top_right_radius=8)
            screen.blit(FONT_BOLD.render("REWARD ID", True, TEXT_DARK), (50, 130))
            screen.blit(FONT_BOLD.render("REWARD NAME", True, TEXT_DARK), (220, 130))
            screen.blit(FONT_BOLD.render("REQUIRED POINTS", True, TEXT_DARK), (520, 130))
            screen.blit(FONT_BOLD.render("AVAILABILITY", True, TEXT_DARK), (720, 130))

            # عرض القائمة من دالة load_rewards
            rewards = self.manager.load_rewards()
            y_offset = 175

            if rewards:
                for r in rewards[:6]:
                    is_selected = selected_reward_id == r.reward_id
                    row_rect = pygame.Rect(35, y_offset - 8, self.width - 70, 48)

                    if is_selected:
                        pygame.draw.rect(screen, (227, 242, 253), row_rect, border_radius=6)
                        pygame.draw.rect(screen, PRIMARY_BLUE, row_rect, width=1, border_radius=6)

                    screen.blit(FONT_BOLD.render(str(r.reward_id), True, TEXT_DARK), (50, y_offset + 5))
                    screen.blit(FONT_BODY.render(str(r.name), True, TEXT_DARK), (220, y_offset + 5))
                    screen.blit(FONT_BOLD.render(f"{r.points_required} Pts", True, GOLD_COLOR), (520, y_offset + 5))

                    status_str = "Available" if r.is_available else "Out of Stock"
                    status_color = GREEN_COLOR if r.is_available else RED_COLOR
                    screen.blit(FONT_BOLD.render(status_str, True, status_color), (720, y_offset + 5))

                    y_offset += 55
            else:
                screen.blit(FONT_BODY.render("No rewards found in rewards.json", True, (150, 150, 150)), (50, 190))

            # رسم أدوات الإدخال والأزرار
            input_check_id.draw(screen, FONT_BODY)
            btn_check.draw(screen, FONT_BTN)

            pygame.display.flip()
            clock.tick(60)


# --- تجربة وتشغيل الملف منفصلاً ---
if __name__ == "__main__":
    mgr = RewardManager()
    gui = RewardManagerGUI(mgr)
    gui.run()