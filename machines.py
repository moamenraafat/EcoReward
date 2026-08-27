import sys
import pygame
import json
import os

# ==============================================================================
# 1. كود الزميل مع ضبط مسار التخزين فقط ليقرأ ويكتب داخل مجلد data/
# ==============================================================================
class machinemanager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.file_path = os.path.join(self.data_dir, "machines.json")
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """التأكد من وجود مجلد data"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def load_machines(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except:
            return []    
        
    def save_machines(self, machines):
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(machines, file, indent=4, ensure_ascii=False)  

    def display_machine(self):
        machines = self.load_machines()
        print("\n==== Machines ====")

        for m in machines:
            print(f"machine: {m['machine_id']} | location: {m['location']} | status: {m['status']}")

    def check_availability(self, machine_id):
        machines = self.load_machines()
        for m in machines:
            if m["machine_id"] == machine_id:
                return m["status"] == "Available"

        return False 
               
    def change_status(self, machine_id, new_status):
        machines = self.load_machines()

        for m in machines:
            if m["machine_id"] == machine_id:
                m["status"] = new_status
                self.save_machines(machines)
                print(f"status of {machine_id} changed to {new_status}")
                return True

        print(f"Machine {machine_id} not found")
        return False       

    def add_machine(self, machine_id, location, accepted_materials):
        machines = self.load_machines()
        new_machine = {
            "machine_id": machine_id,
            "location": location,
            "status": "Available",
            "accepted_materials": accepted_materials,
            "capacity": "0%"
        }
        machines.append(new_machine)
        self.save_machines(machines)
        print(f"machine {machine_id} added successfully")

    def remove_machine(self, machine_id):
        machines = self.load_machines()
        for m in machines:
            if m["machine_id"] == machine_id:
                machines.remove(m)
                self.save_machines(machines)

                print(f"machine {machine_id} removed successfully")
                return True

        print("Machine NOT found")
        return False    


# ==============================================================================
# 2. واجهة Pygame GUI متكاملة دون مساس باللوجيك الأصلي
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


class MachineManagerGUI:
    """واجهة إدارة الماكينات الرسومية"""
    def __init__(self, manager: machinemanager):
        self.manager = manager
        self.width = 900
        self.height = 600

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EcoReward - Machine Management Panel")

        # الألوان
        BG_COLOR = (245, 247, 250)
        WHITE = (255, 255, 255)
        PRIMARY_BLUE = (33, 150, 243)
        DARK_HEADER = (35, 45, 60)
        GREEN_COLOR = (46, 125, 50)
        RED_COLOR = (211, 47, 47)
        TEXT_DARK = (33, 33, 33)

        # الخطوط
        FONT_TITLE = pygame.font.SysFont("Arial", 20, bold=True)
        FONT_BODY = pygame.font.SysFont("Arial", 14)
        FONT_BOLD = pygame.font.SysFont("Arial", 14, bold=True)
        FONT_BTN = pygame.font.SysFont("Arial", 13, bold=True)

        # مدخلات التفاعل
        input_id = InputBox(30, 480, 160, 40, "Machine ID")
        input_location = InputBox(200, 480, 180, 40, "Location")
        input_materials = InputBox(390, 480, 200, 40, "Materials (comma sep)")

        btn_add = Button(600, 480, 120, 40, "Add Machine", GREEN_COLOR, (76, 175, 80))
        btn_toggle_status = Button(730, 480, 140, 40, "Toggle Status", PRIMARY_BLUE, (66, 165, 245))
        btn_delete = Button(730, 530, 140, 35, "Delete Selected", RED_COLOR, (229, 115, 115))

        status_msg = "Select a machine from the list to view or update status."
        selected_machine_id = None

        clock = pygame.time.Clock()
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                input_id.handle_event(event)
                input_location.handle_event(event)
                input_materials.handle_event(event)

                # اختيار ماكينة من القائمة
                if event.type == pygame.MOUSEBUTTONDOWN and event.pos[1] >= 130 and event.pos[1] <= 440:
                    machines = self.manager.load_machines()
                    clicked_index = (event.pos[1] - 130) // 45
                    if clicked_index < len(machines):
                        selected_machine_id = machines[clicked_index]["machine_id"]
                        status_msg = f"Selected machine: {selected_machine_id}"

                # إضافة ماكينة
                if btn_add.is_clicked(mouse_pos, event.type):
                    if input_id.text and input_location.text:
                        m_materials = [m.strip() for m in input_materials.text.split(",")] if input_materials.text else ["Plastic"]
                        self.manager.add_machine(input_id.text, input_location.text, m_materials)
                        status_msg = f"Machine '{input_id.text}' added successfully!"
                        input_id.text, input_location.text, input_materials.text = "", "", ""
                    else:
                        status_msg = "Error: Machine ID & Location are required!"

                # تغيير حالة ماكينة
                if btn_toggle_status.is_clicked(mouse_pos, event.type):
                    target_id = input_id.text if input_id.text else selected_machine_id
                    if target_id:
                        is_available = self.manager.check_availability(target_id)
                        new_stat = "Maintenance" if is_available else "Available"
                        if self.manager.change_status(target_id, new_stat):
                            status_msg = f"Status of {target_id} updated to {new_stat}"
                    else:
                        status_msg = "Please select or type a Machine ID first!"

                # حذف ماكينة
                if btn_delete.is_clicked(mouse_pos, event.type):
                    target_id = input_id.text if input_id.text else selected_machine_id
                    if target_id:
                        if self.manager.remove_machine(target_id):
                            status_msg = f"Machine {target_id} removed!"
                            selected_machine_id = None
                        else:
                            status_msg = f"Machine {target_id} not found."
                    else:
                        status_msg = "Please select a machine to delete."

            btn_add.check_hover(mouse_pos)
            btn_toggle_status.check_hover(mouse_pos)
            btn_delete.check_hover(mouse_pos)

            screen.fill(BG_COLOR)

            # Header
            pygame.draw.rect(screen, DARK_HEADER, (0, 0, self.width, 65))
            screen.blit(FONT_TITLE.render("EcoReward - Machine Management Console", True, WHITE), (20, 20))

            # Banner Status
            status_box = pygame.Rect(30, 75, self.width - 60, 35)
            pygame.draw.rect(screen, WHITE, status_box, border_radius=6)
            pygame.draw.rect(screen, (220, 225, 230), status_box, width=1, border_radius=6)
            screen.blit(FONT_BODY.render(f"System Message: {status_msg}", True, TEXT_DARK), (40, 83))

            # قائمة الماكينات (Machine List Container)
            list_rect = pygame.Rect(30, 120, self.width - 60, 330)
            pygame.draw.rect(screen, WHITE, list_rect, border_radius=8)
            pygame.draw.rect(screen, (220, 225, 230), list_rect, width=1, border_radius=8)

            # Table Header
            pygame.draw.rect(screen, (240, 243, 246), (30, 120, self.width - 60, 35), border_top_left_radius=8, border_top_right_radius=8)
            screen.blit(FONT_BOLD.render("MACHINE ID", True, TEXT_DARK), (50, 128))
            screen.blit(FONT_BOLD.render("LOCATION", True, TEXT_DARK), (250, 128))
            screen.blit(FONT_BOLD.render("STATUS", True, TEXT_DARK), (500, 128))
            screen.blit(FONT_BOLD.render("CAPACITY", True, TEXT_DARK), (720, 128))

            # عرض الماكينات
            machines = self.manager.load_machines()
            y_offset = 160

            for m in machines[:6]:
                is_selected = selected_machine_id == m["machine_id"]
                row_rect = pygame.Rect(35, y_offset - 5, self.width - 70, 40)

                if is_selected:
                    pygame.draw.rect(screen, (227, 242, 253), row_rect, border_radius=5)
                    pygame.draw.rect(screen, PRIMARY_BLUE, row_rect, width=1, border_radius=5)

                screen.blit(FONT_BODY.render(str(m.get("machine_id", "N/A")), True, TEXT_DARK), (50, y_offset + 5))
                screen.blit(FONT_BODY.render(str(m.get("location", "N/A")), True, TEXT_DARK), (250, y_offset + 5))

                status_str = str(m.get("status", "N/A"))
                status_color = GREEN_COLOR if status_str == "Available" else RED_COLOR
                screen.blit(FONT_BOLD.render(status_str, True, status_color), (500, y_offset + 5))
                screen.blit(FONT_BODY.render(str(m.get("capacity", "0%")), True, TEXT_DARK), (720, y_offset + 5))

                y_offset += 45

            # رسم أدوات الإدخال والأزرار
            input_id.draw(screen, FONT_BODY)
            input_location.draw(screen, FONT_BODY)
            input_materials.draw(screen, FONT_BODY)

            btn_add.draw(screen, FONT_BTN)
            btn_toggle_status.draw(screen, FONT_BTN)
            btn_delete.draw(screen, FONT_BTN)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


# --- تشغيل وتجربة الكود ---
if __name__ == "__main__":
    manager = machinemanager()
    gui = MachineManagerGUI(manager)
    gui.run()