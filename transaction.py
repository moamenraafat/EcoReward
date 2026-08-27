import sys
import os
import json
from datetime import datetime
import pygame

# استدعاء مدير التخزين الموحد إن وجد، أو الاعتماد على اللوجيك المحلي
try:
    from storage import JSONStorageManager
    storage_db = JSONStorageManager()
except ImportError:
    storage_db = None

TRANSACTION_FILE = "transactions.json"


# ==============================================================================
# 1. كود إدارة المعاملات (Business Logic)
# ==============================================================================

class Transaction:
    """Represent a recycling transaction."""

    def __init__(
        self,
        transaction_id,
        user_id,
        user_name,
        machine_id,
        materials,
        date
    ):
        self.transaction_id = transaction_id
        self.user_id = user_id
        self.user_name = user_name
        self.machine_id = machine_id
        self.materials = materials
        self.date = date

        self.points_earned = self.calculate_points()

    def calculate_points(self):
        """Calculate points earned from all recycled materials."""
        total_points = 0
        for material in self.materials:
            points = (
                material["quantity"]
                * material["points_per_unit"]
            )
            material["points_earned"] = points
            total_points += points

        return total_points

    def to_dict(self):
        """Convert transaction object into a dictionary for JSON."""
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "machine_id": self.machine_id,
            "materials": self.materials,
            "points_earned": self.points_earned,
            "date": self.date
        }


def get_transaction_history():
    """Return all saved transactions."""
    if storage_db:
        return storage_db.load_data(TRANSACTION_FILE, default=[])
    
    file_path = os.path.join("data", TRANSACTION_FILE)
    try:
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def generate_transaction_id():
    """Generate a unique transaction ID."""
    transactions = get_transaction_history()
    transaction_number = 1001 + len(transactions)
    return f"TXN-{transaction_number}"


def save_transaction(transaction):
    """Save a transaction object into the JSON file."""
    if storage_db:
        storage_db.append_item(TRANSACTION_FILE, transaction.to_dict())
    else:
        os.makedirs("data", exist_ok=True)
        file_path = os.path.join("data", TRANSACTION_FILE)
        transactions = get_transaction_history()
        transactions.append(transaction.to_dict())

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(transactions, file, indent=4, ensure_ascii=False)
        except OSError as error:
            print(f"Error saving transaction: {error}")


def create_transaction(user, machine, materials):
    """Create, calculate, update and save a transaction."""
    transaction_id = generate_transaction_id()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    transaction = Transaction(
        transaction_id,
        user.get("id", user.get("user_id", "U000")),
        user.get("name", "Unknown User"),
        machine.get("machine_id", machine.get("id", "M000")),
        materials,
        current_date
    )

    # تحديث نقاط المستخدم
    user["points"] = user.get("points", 0) + transaction.points_earned

    # حفظ النقاط الجديدة للمستخدم في users.json إذا كان مدير التخزين متاحاً
    if storage_db:
        storage_db.update_data("users.json", user.get("id", user.get("user_id")), {"points": user["points"]}, id_key="id")

    # حفظ العملية
    save_transaction(transaction)

    return transaction


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


class TransactionGUI:
    """واجهة عرض سجل المعاملات وإدارتها"""
    def __init__(self):
        self.width = 900
        self.height = 620

    def run(self):
        if not pygame.get_init():
            pygame.init()

        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EcoReward - Transactions History Hub")

        # الألوان
        BG_COLOR = (245, 247, 250)
        WHITE = (255, 255, 255)
        DARK_HEADER = (35, 45, 60)
        PRIMARY_GREEN = (46, 125, 50)
        PRIMARY_BLUE = (33, 150, 243)
        TEXT_DARK = (33, 33, 33)

        # الخطوط
        FONT_TITLE = pygame.font.SysFont("Arial", 20, bold=True)
        FONT_BODY = pygame.font.SysFont("Arial", 14)
        FONT_BOLD = pygame.font.SysFont("Arial", 14, bold=True)
        FONT_BTN = pygame.font.SysFont("Arial", 13, bold=True)

        btn_refresh = Button(710, 75, 160, 35, "Refresh History", PRIMARY_BLUE, (66, 165, 245))

        transactions_data = get_transaction_history()
        status_msg = f"Total Recorded Transactions: {len(transactions_data)}"

        clock = pygame.time.Clock()
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if btn_refresh.is_clicked(mouse_pos, event.type):
                    transactions_data = get_transaction_history()
                    status_msg = f"Refreshed! Total Transactions: {len(transactions_data)}"

            btn_refresh.check_hover(mouse_pos)
            screen.fill(BG_COLOR)

            # Header
            pygame.draw.rect(screen, DARK_HEADER, (0, 0, self.width, 65))
            screen.blit(FONT_TITLE.render("EcoReward - Recycling Transactions Log", True, WHITE), (20, 20))

            # Banner Status
            status_box = pygame.Rect(30, 75, 660, 35)
            pygame.draw.rect(screen, WHITE, status_box, border_radius=6)
            pygame.draw.rect(screen, (220, 225, 230), status_box, width=1, border_radius=6)
            screen.blit(FONT_BODY.render(status_msg, True, TEXT_DARK), (40, 83))

            btn_refresh.draw(screen, FONT_BTN)

            # جدول عرض المعاملات
            list_rect = pygame.Rect(30, 125, self.width - 60, 460)
            pygame.draw.rect(screen, WHITE, list_rect, border_radius=8)
            pygame.draw.rect(screen, (220, 225, 230), list_rect, width=1, border_radius=8)

            # Table Header
            pygame.draw.rect(screen, (240, 243, 246), (30, 125, self.width - 60, 40), border_top_left_radius=8, border_top_right_radius=8)
            screen.blit(FONT_BOLD.render("TXN ID", True, TEXT_DARK), (45, 135))
            screen.blit(FONT_BOLD.render("USER NAME", True, TEXT_DARK), (170, 135))
            screen.blit(FONT_BOLD.render("MACHINE", True, TEXT_DARK), (370, 135))
            screen.blit(FONT_BOLD.render("DATE & TIME", True, TEXT_DARK), (510, 135))
            screen.blit(FONT_BOLD.render("EARNED PTS", True, TEXT_DARK), (730, 135))

            # Render Rows
            y_offset = 180
            if transactions_data:
                for txn in reversed(transactions_data[-7:]):
                    row_rect = pygame.Rect(35, y_offset - 8, self.width - 70, 45)
                    pygame.draw.rect(screen, (250, 250, 252), row_rect, border_radius=5)

                    screen.blit(FONT_BOLD.render(str(txn.get("transaction_id", "N/A")), True, TEXT_DARK), (45, y_offset + 5))
                    screen.blit(FONT_BODY.render(str(txn.get("user_name", "N/A")), True, TEXT_DARK), (170, y_offset + 5))
                    screen.blit(FONT_BODY.render(str(txn.get("machine_id", "N/A")), True, TEXT_DARK), (370, y_offset + 5))
                    screen.blit(FONT_BODY.render(str(txn.get("date", "N/A")), True, TEXT_DARK), (510, y_offset + 5))
                    screen.blit(FONT_BOLD.render(f"+{txn.get('points_earned', 0)} Pts", True, PRIMARY_GREEN), (730, y_offset + 5))

                    y_offset += 52
            else:
                screen.blit(FONT_BODY.render("No transactions found in transactions.json.", True, (150, 150, 150)), (50, 200))

            pygame.display.flip()
            clock.tick(60)


# --- تجربة الكود منفصلاً ---
if __name__ == "__main__":
    gui = TransactionGUI()
    gui.run()