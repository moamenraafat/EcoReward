import sys
import os
import pygame
import json

# ==============================================================================
# 1. كود إدارة الخامات واللوجيك (Backend Material Manager)
# ==============================================================================
class materialmanager:
 
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.file_path = os.path.join(self.data_dir, "materials.json")
        self.materials = self.load_materials()

    def load_materials(self):
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            print(f"[Materials Error] Failed to load JSON: {e}")
            return []

    def save_materials(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as file:
                json.dump(self.materials, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Materials Error] Failed to save JSON: {e}")

    def list_materials(self):
        print("\n==== Available Materials ====")
        for i in self.materials:
            print(f"material: {i['material_name']} | type: {i['type']} | points: {i['points_per_kg']} point\\kg")

    def find_material(self, material_name):
        for m in self.materials:
            if m["material_name"].lower() == material_name.lower():
                return m
        return None
            
    def calculate_points(self, material_name, quantity):
        material = self.find_material(material_name)
        if material:
            return int(material["points_per_kg"] * quantity)
        else:
            print(f"{material_name} Not found")
            return 0
        
    def add_material(self, name, type, points_per_kg, unit="kg"):
        new_material = {
            "material_name": name,
            "type": type,
            "points_per_kg": points_per_kg,
            "unit": unit
        }

        self.materials.append(new_material)
        self.save_materials()
        print(f"{name} added successfully")


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


class MaterialManagerGUI:
    """واجهة إدارة الخامات وحساب النقاط"""
    def __init__(self, manager: materialmanager):
        self.manager = manager
        self.width = 900
        self.height = 620

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EcoReward - Material Management Panel")

        # الألوان
        BG_COLOR = (245, 247, 250)
        WHITE = (255, 255, 255)
        DARK_HEADER = (35, 45, 60)
        PRIMARY_GREEN = (46, 125, 50)
        ACCENT_BLUE = (33, 150, 243)
        TEXT_DARK = (33, 33, 33)

        # الخطوط
        FONT_TITLE = pygame.font.SysFont("Arial", 20, bold=True)
        FONT_BODY = pygame.font.SysFont("Arial", 14)
        FONT_BOLD = pygame.font.SysFont("Arial", 14, bold=True)
        FONT_BTN = pygame.font.SysFont("Arial", 13, bold=True)

        # مدخلات إضافة خامة جديدة
        input_name = InputBox(30, 480, 150, 40, "Material Name")
        input_type = InputBox(190, 480, 140, 40, "Type (e.g. Metal)")
        input_points = InputBox(340, 480, 130, 40, "Points / Kg")
        btn_add = Button(480, 480, 120, 40, "Add Material", PRIMARY_GREEN, (76, 175, 80))

        # مدخلات حاسبة النقاط
        input_calc_weight = InputBox(630, 480, 110, 40, "Weight (kg)")
        btn_calc = Button(750, 480, 120, 40, "Calculate", ACCENT_BLUE, (66, 165, 245))

        status_msg = "Select a material to view info or enter weight to calculate points."
        selected_material_name = None

        clock = pygame.time.Clock()
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                input_name.handle_event(event)
                input_type.handle_event(event)
                input_points.handle_event(event)
                input_calc_weight.handle_event(event)

                # اختيار خامة عند الضغط عليها في الجدول
                if event.type == pygame.MOUSEBUTTONDOWN and 130 <= event.pos[1] <= 440:
                    materials = self.manager.load_materials()
                    clicked_index = (event.pos[1] - 130) // 45
                    if clicked_index < len(materials):
                        selected_material_name = materials[clicked_index]["material_name"]
                        status_msg = f"Selected material: '{selected_material_name}'"

                # زر إضافة خامة
                if btn_add.is_clicked(mouse_pos, event.type):
                    if input_name.text and input_type.text and input_points.text:
                        try:
                            pts = float(input_points.text)
                            self.manager.add_material(input_name.text, input_type.text, pts)
                            status_msg = f"Material '{input_name.text}' added successfully!"
                            input_name.text, input_type.text, input_points.text = "", "", ""
                        except ValueError:
                            status_msg = "Error: Points per Kg must be a valid number!"
                    else:
                        status_msg = "Error: All fields for adding material are required!"

                # زر حساب النقاط
                if btn_calc.is_clicked(mouse_pos, event.type):
                    target_mat = input_name.text if input_name.text else selected_material_name
                    if target_mat and input_calc_weight.text:
                        try:
                            qty = float(input_calc_weight.text)
                            pts = self.manager.calculate_points(target_mat, qty)
                            status_msg = f"Calculated: {qty} kg of '{target_mat}' = {pts} Points!"
                        except ValueError:
                            status_msg = "Error: Weight must be a valid number!"
                    else:
                        status_msg = "Error: Select a material and enter weight first!"

            btn_add.check_hover(mouse_pos)
            btn_calc.check_hover(mouse_pos)

            screen.fill(BG_COLOR)

            # Header
            pygame.draw.rect(screen, DARK_HEADER, (0, 0, self.width, 65))
            screen.blit(FONT_TITLE.render("EcoReward - Materials & Points Calculator", True, WHITE), (20, 20))

            # Banner Status
            status_box = pygame.Rect(30, 75, self.width - 60, 35)
            pygame.draw.rect(screen, WHITE, status_box, border_radius=6)
            pygame.draw.rect(screen, (220, 225, 230), status_box, width=1, border_radius=6)
            screen.blit(FONT_BODY.render(f"System Message: {status_msg}", True, TEXT_DARK), (40, 83))

            # جدول عرض الخامات
            list_rect = pygame.Rect(30, 120, self.width - 60, 330)
            pygame.draw.rect(screen, WHITE, list_rect, border_radius=8)
            pygame.draw.rect(screen, (220, 225, 230), list_rect, width=1, border_radius=8)

            # Table Header
            pygame.draw.rect(screen, (240, 243, 246), (30, 120, self.width - 60, 35), border_top_left_radius=8, border_top_right_radius=8)
            screen.blit(FONT_BOLD.render("MATERIAL NAME", True, TEXT_DARK), (50, 128))
            screen.blit(FONT_BOLD.render("CATEGORY TYPE", True, TEXT_DARK), (300, 128))
            screen.blit(FONT_BOLD.render("POINTS / KG", True, TEXT_DARK), (550, 128))
            screen.blit(FONT_BOLD.render("UNIT", True, TEXT_DARK), (750, 128))

            # عرض قائمة الخامات
            materials = self.manager.load_materials()
            y_offset = 160

            for m in materials[:6]:
                is_selected = selected_material_name == m.get("material_name")
                row_rect = pygame.Rect(35, y_offset - 5, self.width - 70, 40)

                if is_selected:
                    pygame.draw.rect(screen, (232, 245, 233), row_rect, border_radius=5)
                    pygame.draw.rect(screen, PRIMARY_GREEN, row_rect, width=1, border_radius=5)

                screen.blit(FONT_BODY.render(str(m.get("material_name", "N/A")), True, TEXT_DARK), (50, y_offset + 5))
                screen.blit(FONT_BODY.render(str(m.get("type", "N/A")), True, TEXT_DARK), (300, y_offset + 5))
                screen.blit(FONT_BOLD.render(f"{m.get('points_per_kg', 0)} Pts", True, PRIMARY_GREEN), (550, y_offset + 5))
                screen.blit(FONT_BODY.render(str(m.get("unit", "kg")), True, TEXT_DARK), (750, y_offset + 5))

                y_offset += 45

            # رسم أدوات الإدخال والأزرار
            input_name.draw(screen, FONT_BODY)
            input_type.draw(screen, FONT_BODY)
            input_points.draw(screen, FONT_BODY)
            btn_add.draw(screen, FONT_BTN)

            input_calc_weight.draw(screen, FONT_BODY)
            btn_calc.draw(screen, FONT_BTN)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


# --- تشغيل وتجربة الكود ---
if __name__ == "__main__":
    manager = materialmanager()
    gui = MaterialManagerGUI(manager)
    gui.run()