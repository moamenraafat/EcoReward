import sys
import pygame
from collections import Counter
from tabulate import tabulate
from storage import JSONStorageManager


class AnalyticsManager:
    """كلاس مسؤول عن حساب واستخراج كافة تحليلات وإحصائيات النظام من ملفات JSON"""
    def __init__(self):
        self.storage = JSONStorageManager()

    def get_total_users(self) -> int:
        """Returns the total number of registered users."""
        users = self.storage.load_data("users.json")
        return len(users)

    def get_total_transactions(self) -> int:
        """Returns the total number of recycling transactions."""
        transactions = self.storage.load_data("transactions.json")
        return len(transactions)

    def get_total_recycled_by_material(self) -> dict:
        """
        Calculates total weight recycled per material type (e.g., Plastic, Aluminum, Glass).
        Returns a dictionary with values in kilograms.
        """
        transactions = self.storage.load_data("transactions.json")
        recycled_summary = {}

        for tx in transactions:
            material = tx.get("material_type", tx.get("material_name", "Unknown"))
            weight = tx.get("weight_kg", tx.get("weight", tx.get("quantity", 0.0)))
            try:
                weight = float(weight)
            except (ValueError, TypeError):
                weight = 0.0
                
            recycled_summary[material] = recycled_summary.get(material, 0.0) + weight

        return {mat: round(w, 2) for mat, w in recycled_summary.items()}

    def get_total_points(self) -> int:
        """Returns total points issued across all transactions."""
        transactions = self.storage.load_data("transactions.json")
        total = 0
        for tx in transactions:
            try:
                total += int(tx.get("points_earned", 0))
            except (ValueError, TypeError):
                pass
        return total

    def get_top_material(self) -> str:
        """Finds the most frequently recycled material."""
        transactions = self.storage.load_data("transactions.json")
        materials = [tx.get("material_type", tx.get("material_name")) for tx in transactions if tx.get("material_type") or tx.get("material_name")]
        
        if not materials:
            return "N/A"

        counter = Counter(materials)
        return counter.most_common(1)[0][0]

    def get_top_machine(self) -> str:
        """Finds the most active machine by transaction count."""
        transactions = self.storage.load_data("transactions.json")
        machines = [tx.get("machine_id") for tx in transactions if tx.get("machine_id")]
        
        if not machines:
            return "N/A"

        counter = Counter(machines)
        return counter.most_common(1)[0][0]

    def get_analytics_summary(self) -> dict:
        """
        Main analytical function to be imported by teammates.
        Returns live metrics in a structured dictionary.
        """
        return {
            "total_users": self.get_total_users(),
            "total_transactions": self.get_total_transactions(),
            "recycled_by_material": self.get_total_recycled_by_material(),
            "total_points": self.get_total_points(),
            "top_material": self.get_top_material(),
            "top_machine": self.get_top_machine()
        }

    def print_analytics_dashboard(self):
        """Prints a formatted ASCII dashboard in English for clean terminal display."""
        summary = self.get_analytics_summary()

        print("\n" + "=" * 18 + " 📊 EcoReward Analytics Dashboard " + "=" * 18)
        
        # 1. General Metrics
        general_stats = [
            ["Total Registered Users", f"{summary['total_users']:,}"],
            ["Total Recycling Transactions", f"{summary['total_transactions']:,}"],
            ["Total Points Issued", f"{summary['total_points']:,}"],
            ["Most Recycled Material", summary['top_material']],
            ["Most Active Machine", summary['top_machine']]
        ]
        print(tabulate(general_stats, headers=["Metric", "Current Value"], tablefmt="fancy_grid"))

        # 2. Material Breakdown
        print("\n📦 Recycled Materials Breakdown (in kg):")
        recycled_data = summary['recycled_by_material']
        if recycled_data:
            material_table = [[mat, f"{weight} kg"] for mat, weight in recycled_data.items()]
            print(tabulate(material_table, headers=["Material Type", "Total Weight"], tablefmt="simple"))
        else:
            print("  - No recycling transactions recorded yet.")
            
        print("=" * 68 + "\n")


# --- Wrapper Function عشان التوافق المباشر مع excel_reports.py ---
def get_analytics_summary() -> dict:
    analyzer = AnalyticsManager()
    return analyzer.get_analytics_summary()


# ==============================================================================
#  قسم الواجهة الرسومية GUI (Pygame Analytics Dashboard - OOP)
# ==============================================================================

class Button:
    """فئة زرار تفاعلي للواجهة"""
    def __init__(self, x, y, width, height, text, bg_color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface, font):
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, width=1, border_radius=8)

        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos, event_type):
        return self.is_hovered and event_type == pygame.MOUSEBUTTONDOWN


class AnalyticsGUI:
    """كلاس إدارة واجهة لوحة التحليلات باستخدام Pygame"""
    def __init__(self, analyzer: AnalyticsManager):
        self.analyzer = analyzer
        self.width = 850
        self.height = 550

    def draw_card(self, screen, x, y, width, height, title, value, color, font_title, font_val):
        """دالة رسم كارت إحصائي"""
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=10)
        pygame.draw.rect(screen, (220, 225, 230), rect, width=1, border_radius=10)
        
        # Top Accent Line
        pygame.draw.rect(screen, color, (x, y, width, 5), border_top_left_radius=10, border_top_right_radius=10)

        t_surf = font_title.render(title, True, (100, 110, 120))
        v_surf = font_val.render(str(value), True, (33, 33, 33))

        screen.blit(t_surf, (x + 15, y + 15))
        screen.blit(v_surf, (x + 15, y + 42))

    def run(self):
        """عرض لوحة التحليلات تفاعلياً"""
        pygame.init()

        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EcoReward - Realtime Analytics Dashboard")

        PRIMARY_BLUE = (33, 150, 243)
        PRIMARY_GREEN = (46, 125, 50)
        ACCENT_ORANGE = (255, 152, 0)
        ACCENT_PURPLE = (156, 39, 176)
        BG_COLOR = (245, 247, 250)
        WHITE = (255, 255, 255)
        TEXT_DARK = (33, 33, 33)

        FONT_TITLE = pygame.font.SysFont("Arial", 22, bold=True)
        FONT_CARD_T = pygame.font.SysFont("Arial", 13, bold=True)
        FONT_CARD_V = pygame.font.SysFont("Arial", 22, bold=True)
        FONT_BODY = pygame.font.SysFont("Arial", 15)
        FONT_BTN = pygame.font.SysFont("Arial", 14, bold=True)

        btn_refresh = Button(325, 480, 200, 45, "Refresh Analytics", PRIMARY_BLUE, (66, 165, 245))

        summary = self.analyzer.get_analytics_summary()

        clock = pygame.time.Clock()
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if btn_refresh.is_clicked(mouse_pos, event.type):
                    summary = self.analyzer.get_analytics_summary()

            btn_refresh.check_hover(mouse_pos)

            screen.fill(BG_COLOR)

            # Header
            pygame.draw.rect(screen, (35, 45, 60), (0, 0, self.width, 70))
            title_surf = FONT_TITLE.render("EcoReward Analytics & Metrics Visualizer", True, WHITE)
            screen.blit(title_surf, (20, 22))

            # Metrics Cards Row
            self.draw_card(screen, 30, 90, 180, 85, "TOTAL USERS", f"{summary['total_users']:,}", PRIMARY_BLUE, FONT_CARD_T, FONT_CARD_V)
            self.draw_card(screen, 230, 90, 180, 85, "TRANSACTIONS", f"{summary['total_transactions']:,}", PRIMARY_GREEN, FONT_CARD_T, FONT_CARD_V)
            self.draw_card(screen, 430, 90, 180, 85, "POINTS ISSUED", f"{summary['total_points']:,}", ACCENT_ORANGE, FONT_CARD_T, FONT_CARD_V)
            self.draw_card(screen, 630, 90, 190, 85, "TOP MATERIAL", str(summary['top_material']), ACCENT_PURPLE, FONT_CARD_T, FONT_CARD_V)

            # Detailed Material Breakdown Box
            detail_rect = pygame.Rect(30, 195, self.width - 60, 265)
            pygame.draw.rect(screen, WHITE, detail_rect, border_radius=10)
            pygame.draw.rect(screen, (220, 225, 230), detail_rect, width=1, border_radius=10)

            screen.blit(FONT_CARD_T.render("RECYCLED MATERIALS BREAKDOWN (KG)", True, (100, 110, 120)), (50, 215))

            materials_data = summary['recycled_by_material']
            start_y = 250

            if materials_data:
                max_weight = max(materials_data.values()) if max(materials_data.values()) > 0 else 1
                for mat, weight in list(materials_data.items())[:4]:
                    # Material Name
                    screen.blit(FONT_BODY.render(f"{mat}: {weight} kg", True, TEXT_DARK), (50, start_y))
                    
                    # Progress Bar Visualization
                    bar_bg = pygame.Rect(250, start_y + 4, 450, 14)
                    pygame.draw.rect(screen, (235, 240, 245), bar_bg, border_radius=7)
                    
                    fill_w = int((weight / max_weight) * 450)
                    if fill_w > 0:
                        bar_fill = pygame.Rect(250, start_y + 4, fill_w, 14)
                        pygame.draw.rect(screen, PRIMARY_GREEN, bar_fill, border_radius=7)
                    
                    start_y += 45
            else:
                screen.blit(FONT_BODY.render("No recycling transaction data recorded yet.", True, (120, 120, 120)), (50, 260))

            btn_refresh.draw(screen, FONT_BTN)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


def run_analytics_gui():
    analyzer = AnalyticsManager()
    gui = AnalyticsGUI(analyzer)
    gui.run()


# --- تجربة سريعة عند تشغيل الملف منفصلاً ---
if __name__ == "__main__":
    print("--- Launching EcoReward Analytics Pygame GUI ---")
    run_analytics_gui()