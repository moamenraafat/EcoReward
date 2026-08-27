import sys
import os
import pygame
import json

# ==============================================================================
# 1. قراءة البيانات من ملف JSON
# ==============================================================================
def get_latest_transaction(data_dir="data"):
    """قراءة أحدث عملية معالجة من ملف transactions.json"""
    file_path = os.path.join(data_dir, "transactions.json")
    if not os.path.exists(file_path):
        print(f"[Receipt Error] File '{file_path}' not found!")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            transactions = json.load(file)
            if transactions and isinstance(transactions, list):
                return transactions[-1]
    except Exception as e:
        print(f"[Receipt Error] Failed to read JSON: {e}")
    return None


def generate_receipt(transaction=None):
    """Generate and display the receipt via GUI."""
    if transaction is None:
        transaction = get_latest_transaction()

    gui = ReceiptGUI(transaction)
    gui.run()


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


class ReceiptGUI:
    """واجهة عرض الإيصال الرقمي بـ Pygame"""
    def __init__(self, transaction_obj=None):
        self.transaction = transaction_obj
        self.width = 650
        self.height = 600

    def _get_val(self, key, default="N/A"):
        """دالة مساعدة لاستخراج البيانات سواء كان الكائن dict أو class instance"""
        if isinstance(self.transaction, dict):
            return self.transaction.get(key, default)
        return getattr(self.transaction, key, default)

    def run(self, transaction=None):
        if transaction:
            self.transaction = transaction

        if not pygame.get_init():
            pygame.init()

        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EcoReward - Digital Receipt Visualizer")

        # الألوان
        BG_COLOR = (245, 247, 250)
        WHITE = (255, 255, 255)
        DARK_HEADER = (35, 45, 60)
        PRIMARY_GREEN = (46, 125, 50)
        MONO_TEXT = (240, 240, 240)
        RECEIPT_BG = (25, 30, 36)

        # الخطوط
        FONT_TITLE = pygame.font.SysFont("Arial", 18, bold=True)
        FONT_BTN = pygame.font.SysFont("Arial", 13, bold=True)
        FONT_MONO = pygame.font.SysFont("Courier New", 14, bold=True)

        btn_close = Button(225, 520, 200, 42, "Close Receipt", PRIMARY_GREEN, (76, 175, 80))

        clock = pygame.time.Clock()
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if btn_close.is_clicked(mouse_pos, event.type):
                    running = False

            btn_close.check_hover(mouse_pos)

            screen.fill(BG_COLOR)

            # Header
            pygame.draw.rect(screen, DARK_HEADER, (0, 0, self.width, 60))
            screen.blit(FONT_TITLE.render("EcoReward - Digital Receipt Viewer", True, WHITE), (20, 18))

            # Terminal Card Box for Receipt Display
            card_rect = pygame.Rect(40, 85, self.width - 80, 410)
            pygame.draw.rect(screen, RECEIPT_BG, card_rect, border_radius=10)
            pygame.draw.rect(screen, PRIMARY_GREEN, card_rect, width=2, border_radius=10)

            # Receipt Top Accent Line
            pygame.draw.rect(screen, PRIMARY_GREEN, (40, 85, self.width - 80, 8), border_top_left_radius=10, border_top_right_radius=10)

            # كتابة محتوى الإيصال
            if self.transaction:
                y_pos = 115
                screen.blit(FONT_MONO.render(f"Transaction ID : {self._get_val('transaction_id')}", True, MONO_TEXT), (60, y_pos))
                y_pos += 25
                screen.blit(FONT_MONO.render(f"User           : {self._get_val('user_name')}", True, MONO_TEXT), (60, y_pos))
                y_pos += 25
                screen.blit(FONT_MONO.render(f"Machine        : {self._get_val('machine_id')}", True, MONO_TEXT), (60, y_pos))
                y_pos += 25
                screen.blit(FONT_MONO.render(f"Date           : {self._get_val('date')}", True, MONO_TEXT), (60, y_pos))
                y_pos += 35

                # Header Table
                header_str = f"{'Material':<16}{'Quantity':<12}{'Pts/Unit':>8}"
                screen.blit(FONT_MONO.render(header_str, True, (76, 175, 80)), (60, y_pos))
                y_pos += 20
                screen.blit(FONT_MONO.render("-" * 38, True, (100, 100, 100)), (60, y_pos))
                y_pos += 25

                # Materials List
                materials = self._get_val('materials', [])
                for mat in materials:
                    mat_name = mat.get('name', 'N/A') if isinstance(mat, dict) else getattr(mat, 'name', 'N/A')
                    mat_qty = mat.get('quantity', '0') if isinstance(mat, dict) else getattr(mat, 'quantity', '0')
                    mat_pts = mat.get('points_per_unit', 0) if isinstance(mat, dict) else getattr(mat, 'points_per_unit', 0)

                    line_str = f"{str(mat_name):<16}{str(mat_qty):<12}{str(mat_pts):>8}"
                    screen.blit(FONT_MONO.render(line_str, True, MONO_TEXT), (60, y_pos))
                    y_pos += 25

                screen.blit(FONT_MONO.render("-" * 38, True, (100, 100, 100)), (60, y_pos))
                y_pos += 30

                # Total Points
                total_str = f"{'TOTAL POINTS':<28}{str(self._get_val('points_earned', 0)):>8}"
                screen.blit(FONT_MONO.render(total_str, True, (255, 193, 7)), (60, y_pos))

            else:
                screen.blit(FONT_MONO.render("No Transaction Data Available", True, (200, 100, 100)), (60, 120))

            btn_close.draw(screen, FONT_BTN)

            pygame.display.flip()
            clock.tick(60)


if __name__ == "__main__":
    # تشغيل مباشر ويقرأ تلقائياً من data/transactions.json
    generate_receipt()