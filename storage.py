import json
import os
import sys
import pygame


class JSONStorageManager:
    """كلاس مسؤول عن إدارة قراءة وحفظ وتحديث بيانات ملفات الـ JSON داخل مجلد data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """التأكد من وجود مجلد البيانات"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _get_file_path(self, filename: str) -> str:
        """إرجاع المسار الكامل للملف مع ضمان امتداد .json"""
        if not filename.endswith('.json'):
            filename += '.json'
        return os.path.join(self.data_dir, filename)

    def load_data(self, filename: str, default=None):
        """قراءة البيانات من ملف JSON. وإذا لم يوجد، يتم إنشاؤه بالقيمة الافتراضية"""
        if default is None:
            default = []
            
        filepath = self._get_file_path(filename)
        
        if not os.path.exists(filepath):
            self.save_data(filename, default)
            return default
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Storage Error] فشل قراءة الملف {filename}: {e}")
            return default

    def save_data(self, filename: str, data) -> bool:
        """حفظ البيانات كـ JSON"""
        filepath = self._get_file_path(filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"[Storage Error] فشل حفظ البيانات في {filename}: {e}")
            return False

    def append_item(self, filename: str, item) -> bool:
        """إضافة عنصر جديد مباشرة إلى القائمة الحالية داخل الملف"""
        data = self.load_data(filename, default=[])
        if isinstance(data, list):
            data.append(item)
            return self.save_data(filename, data)
        return False

    def update_data(self, filename: str, item_id: str, new_item_data: dict, id_key: str = "id") -> bool:
        """تحديث عنصر معين داخل ملف بناءً على الـ ID الخاص به"""
        items = self.load_data(filename, default=[])
        updated = False
        
        if isinstance(items, list):
            for idx, item in enumerate(items):
                if isinstance(item, dict) and item.get(id_key) == item_id:
                    items[idx].update(new_item_data)
                    updated = True
                    break
                
        if updated:
            return self.save_data(filename, items)
        else:
            print(f"[Storage Warning] العنصر صاحب الـ {id_key}='{item_id}' غير موجود في {filename}")
            return False

    def delete_data(self, filename: str, item_id: str, id_key: str = "id") -> bool:
        """حذف عنصر معين من القائمة بناءً على الـ ID"""
        items = self.load_data(filename, default=[])
        if isinstance(items, list):
            initial_count = len(items)
            items = [item for item in items if not (isinstance(item, dict) and item.get(id_key) == item_id)]
            if len(items) < initial_count:
                return self.save_data(filename, items)
        return False


# ==============================================================================
# قسم الواجهة الرسومية GUI (Pygame Monitor)
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


class StorageGUI:
    """كلاس إدارة واجهة استعراض حالة التخزين بـ Pygame"""
    def __init__(self, storage_manager: JSONStorageManager = None):
        self.storage = storage_manager if storage_manager else JSONStorageManager()
        self.width = 800
        self.height = 500
        
        # الألوان
        self.DARK_BLUE = (33, 150, 243)
        self.ACCENT_BLUE = (66, 165, 245)
        self.DARK_GREEN = (46, 125, 50)
        self.ACCENT_GREEN = (76, 175, 80)
        self.BG_COLOR = (245, 247, 250)
        self.WHITE = (255, 255, 255)
        self.TEXT_DARK = (33, 33, 33)

    def run(self):
        if not pygame.get_init():
            pygame.init()

        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EcoReward - JSON Storage Manager")

        font_title = pygame.font.SysFont("Arial", 22, bold=True)
        font_body = pygame.font.SysFont("Arial", 16)
        font_btn = pygame.font.SysFont("Arial", 15, bold=True)

        btn_save = Button(180, 400, 200, 45, "Save Sample Machines", self.DARK_GREEN, self.ACCENT_GREEN)
        btn_load = Button(420, 400, 200, 45, "Load & Refresh Data", self.DARK_BLUE, self.ACCENT_BLUE)

        log_message = "Click 'Load' or 'Save' to test storage functions."
        loaded_items = self.storage.load_data("machines.json", default=[])

        clock = pygame.time.Clock()
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if btn_save.is_clicked(mouse_pos, event.type):
                    test_machines = [
                        {"id": "M001", "name": "ماكينة محطة مترو السادات (وسط البلد)", "lat": 30.0444, "lon": 31.2357, "status": "active"},
                        {"id": "M002", "name": "ماكينة مول العرب (6 أكتوبر)", "lat": 30.0074, "lon": 30.9734, "status": "active"},
                        {"id": "M003", "name": "ماكينة جامعة القاهرة (الجيزة)", "lat": 30.0276, "lon": 31.2089, "status": "active"}
                    ]
                    if self.storage.save_data("machines.json", test_machines):
                        log_message = "Successfully saved sample machines to data/machines.json!"
                        loaded_items = self.storage.load_data("machines.json", default=[])

                if btn_load.is_clicked(mouse_pos, event.type):
                    loaded_items = self.storage.load_data("machines.json", default=[])
                    log_message = f"Loaded {len(loaded_items)} items from machines.json."

            btn_save.check_hover(mouse_pos)
            btn_load.check_hover(mouse_pos)

            screen.fill(self.BG_COLOR)

            # Header
            pygame.draw.rect(screen, (40, 50, 70), (0, 0, self.width, 70))
            title_surf = font_title.render("EcoReward Data Storage Monitor (JSON)", True, self.WHITE)
            screen.blit(title_surf, (20, 22))

            # Log Status Box
            status_rect = pygame.Rect(30, 90, self.width - 60, 45)
            pygame.draw.rect(screen, self.WHITE, status_rect, border_radius=6)
            pygame.draw.rect(screen, (200, 200, 200), status_rect, width=1, border_radius=6)
            log_surf = font_body.render(f"Status: {log_message}", True, self.TEXT_DARK)
            screen.blit(log_surf, (45, 103))

            # Data Display Box
            data_rect = pygame.Rect(30, 150, self.width - 60, 230)
            pygame.draw.rect(screen, self.WHITE, data_rect, border_radius=8)
            pygame.draw.rect(screen, (220, 224, 230), data_rect, width=1, border_radius=8)

            start_y = 165
            screen.blit(font_body.render(f"Current File: data/machines.json ({len(loaded_items)} records)", True, self.DARK_BLUE), (45, start_y))
            start_y += 35

            if isinstance(loaded_items, list):
                for idx, item in enumerate(loaded_items[:4], 1):
                    item_str = f"{idx}. ID: {item.get('id', 'N/A')} | Name: {item.get('name', 'N/A')} | Status: {item.get('status', 'N/A')}"
                    screen.blit(font_body.render(item_str, True, self.TEXT_DARK), (45, start_y))
                    start_y += 35

            btn_save.draw(screen, font_btn)
            btn_load.draw(screen, font_btn)

            pygame.display.flip()
            clock.tick(60)


# --- تجربة سريعة عند تشغيل الملف منفصلاً ---
if __name__ == "__main__":
    storage_mgr = JSONStorageManager()
    gui = StorageGUI(storage_mgr)
    gui.run()