import os
import sys
import subprocess
import pandas as pd
import pygame

from storage import JSONStorageManager
from analytics import get_analytics_summary


class ExcelReportExporter:
    """كلاس مسؤول عن قراءة البيانات وتجهيز ملف إكسيل شامل ومتعدد الشيتات"""
    
    def __init__(self, reports_dir: str = "reports", report_filename: str = "EcoReward_Report.xlsx"):
        self.reports_dir = reports_dir
        self.report_filename = report_filename
        self.storage = JSONStorageManager()

    def _ensure_reports_dir(self):
        """التأكد من وجود مجلد التقارير"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)

    def generate_excel_report(self) -> str:
        """قراءة البيانات من ملفات JSON وتحويلها لـ Excel Multi-sheet"""
        self._ensure_reports_dir()
        file_path = os.path.join(self.reports_dir, self.report_filename)

        # 1. جلب البيانات من الموديولات المختلفة
        users_data = self.storage.load_data("users.json")
        machines_data = self.storage.load_data("machines.json")
        materials_data = self.storage.load_data("materials.json")
        transactions_data = self.storage.load_data("transactions.json")
        rewards_data = self.storage.load_data("rewards.json")
        redemptions_data = self.storage.load_data("redemptions.json")

        # 2. جلب التحليلات وتجهيزها للعرض
        analytics_dict = get_analytics_summary()
        
        analytics_flat = {
            "Total Users": [analytics_dict.get("total_users", 0)],
            "Total Transactions": [analytics_dict.get("total_transactions", 0)],
            "Total Points Issued": [analytics_dict.get("total_points", 0)],
            "Most Recycled Material": [analytics_dict.get("top_material", "N/A")],
            "Most Active Machine": [analytics_dict.get("top_machine", "N/A")]
        }
        
        for mat, weight in analytics_dict.get("recycled_by_material", {}).items():
            analytics_flat[f"Recycled {mat} (kg)"] = [weight]

        # 3. إنشاء DataFrames
        df_users = pd.DataFrame(users_data)
        df_machines = pd.DataFrame(machines_data)
        df_materials = pd.DataFrame(materials_data)
        df_transactions = pd.DataFrame(transactions_data)
        df_rewards = pd.DataFrame(rewards_data)
        df_redemptions = pd.DataFrame(redemptions_data)
        df_analytics = pd.DataFrame(analytics_flat)

        # 4. التصدير لملف Excel واحد بشيتات متعددة
        try:
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                df_users.to_excel(writer, sheet_name="Users", index=False)
                df_machines.to_excel(writer, sheet_name="Machines", index=False)
                df_materials.to_excel(writer, sheet_name="Materials", index=False)
                df_transactions.to_excel(writer, sheet_name="Transactions", index=False)
                df_rewards.to_excel(writer, sheet_name="Rewards", index=False)
                df_redemptions.to_excel(writer, sheet_name="Redemptions", index=False)
                df_analytics.to_excel(writer, sheet_name="Analytics", index=False)

            print(f"[Excel Report Success] Report successfully generated at: {file_path}")
            return file_path

        except Exception as e:
            print(f"[Excel Report Error] Failed to generate report: {e}")
            return ""

    @staticmethod
    def open_file_or_folder(path: str):
        """فتح ملف التقرير أو مجلد التقارير عبر نظام التشغيل مباشرة"""
        if not os.path.exists(path):
            return
        try:
            if sys.platform == "win32":
                os.startfile(os.path.abspath(path))
            elif sys.platform == "darwin":
                subprocess.run(["open", os.path.abspath(path)])
            else:
                subprocess.run(["xdg-open", os.path.abspath(path)])
        except Exception as e:
            print(f"[OS Open Error] {e}")


# ==============================================================================
#  قسم الواجهة الرسومية GUI (Pygame Generator UI - OOP)
# ==============================================================================

class Button:
    """كلاس الزرار التفاعلي للواجهة"""
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


class ExcelReportGUI:
    """كلاس إدارة واجهة توليد واستعراض تقارير الإكسيل بـ Pygame"""
    def __init__(self, exporter: ExcelReportExporter):
        self.exporter = exporter
        self.width = 800
        self.height = 500
        
        # الألوان
        self.PRIMARY_GREEN = (46, 125, 50)
        self.ACCENT_GREEN = (76, 175, 80)
        self.DARK_BLUE = (33, 150, 243)
        self.ACCENT_BLUE = (66, 165, 245)
        self.BG_COLOR = (245, 247, 250)
        self.WHITE = (255, 255, 255)
        self.TEXT_DARK = (33, 33, 33)

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EcoReward - Excel Report Generator")

        font_title = pygame.font.SysFont("Arial", 22, bold=True)
        font_body = pygame.font.SysFont("Arial", 16)
        font_btn = pygame.font.SysFont("Arial", 15, bold=True)

        btn_generate = Button(80, 390, 200, 50, "Generate Excel Report", self.PRIMARY_GREEN, self.ACCENT_GREEN)
        btn_open_file = Button(300, 390, 200, 50, "Open Generated Excel", self.DARK_BLUE, self.ACCENT_BLUE)
        btn_open_dir = Button(520, 390, 200, 50, "Open Reports Folder", (100, 110, 120), (130, 140, 150))

        status_msg = "Ready to generate Excel business report."
        generated_path = ""

        clock = pygame.time.Clock()
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if btn_generate.is_clicked(mouse_pos, event.type):
                    res_path = self.exporter.generate_excel_report()
                    if res_path:
                        generated_path = res_path
                        status_msg = f"Report successfully created: {res_path}"
                    else:
                        status_msg = "Error generating Excel report! Check console."

                if btn_open_file.is_clicked(mouse_pos, event.type):
                    if generated_path and os.path.exists(generated_path):
                        self.exporter.open_file_or_folder(generated_path)
                    else:
                        status_msg = "No generated file found! Click 'Generate' first."

                if btn_open_dir.is_clicked(mouse_pos, event.type):
                    self.exporter.open_file_or_folder(self.exporter.reports_dir)

            btn_generate.check_hover(mouse_pos)
            btn_open_file.check_hover(mouse_pos)
            btn_open_dir.check_hover(mouse_pos)

            screen.fill(self.BG_COLOR)

            # Header
            pygame.draw.rect(screen, (30, 80, 50), (0, 0, self.width, 70))
            title_surf = font_title.render("EcoReward - Excel Business Report Exporter", True, self.WHITE)
            screen.blit(title_surf, (20, 22))

            # Status Banner
            status_rect = pygame.Rect(30, 90, self.width - 60, 45)
            pygame.draw.rect(screen, self.WHITE, status_rect, border_radius=6)
            pygame.draw.rect(screen, (200, 200, 200), status_rect, width=1, border_radius=6)
            log_surf = font_body.render(f"Status: {status_msg}", True, self.TEXT_DARK)
            screen.blit(log_surf, (45, 103))

            # Details Box
            info_rect = pygame.Rect(30, 150, self.width - 60, 210)
            pygame.draw.rect(screen, self.WHITE, info_rect, border_radius=8)
            pygame.draw.rect(screen, (220, 224, 230), info_rect, width=1, border_radius=8)

            sheets_info = [
                "Includes 7 Multi-Sheet Reports:",
                "• Users & Machines",
                "• Materials & Pricing Rates",
                "• Recycling Transactions Logs",
                "• Rewards Catalog & Redemptions History",
                "• Executive Analytics Summary"
            ]

            start_y = 165
            for line in sheets_info:
                color = self.PRIMARY_GREEN if "Includes" in line else self.TEXT_DARK
                screen.blit(font_body.render(line, True, color), (45, start_y))
                start_y += 32

            btn_generate.draw(screen, font_btn)
            btn_open_file.draw(screen, font_btn)
            btn_open_dir.draw(screen, font_btn)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


# --- تجربة سريعة عند تشغيل الملف منفصلاً ---
if __name__ == "__main__":
    print("--- Generating EcoReward Excel Business Report GUI (OOP) ---")
    exporter = ExcelReportExporter()
    gui = ExcelReportGUI(exporter)
    gui.run()