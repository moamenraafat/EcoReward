import math
import sys
import os
import json
import webbrowser
import requests
import folium
import pygame

# ================= =================
#  إعدادات وتكفيج النظام
# ================= =================
USE_TEST_LOCATION = True  # خليها False لو عاوز يرجع يجيب موقعك الحقيقي من الـ IP
TEST_LAT = 30.0561
TEST_LON = 31.3301


class LocationService:
    """كلاس مسؤول عن العمليات الجغرافية (جلب الموقع + حساب المسافات)"""
    
    @staticmethod
    def get_current_user_location() -> tuple:
        """جلب موقع المستخدم (الموقع التجريبي أو الحقيقي من الـ IP)"""
        if USE_TEST_LOCATION:
            return TEST_LAT, TEST_LON

        try:
            # محاولة جلب الموقع الحقيقي عبر الـ IP
            response = requests.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data.get('lat'), data.get('lon')
        except Exception as e:
            print(f"[Location Warning] Could not fetch live location: {e}")
        
        # موقع افتراضي في حالة عدم وجود اتصالات
        return 30.0444, 31.2357

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """حساب المسافة الجغرافية بالكيلومتر باستخدام Haversine Formula"""
        R = 6371.0

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)


class MachineManager:
    """كلاس إدارة الماكينات ومعالجتها وتوليد الخرائط الشاملة لها"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.file_path = os.path.join(self.data_dir, "machines.json")

    def load_machines_from_json(self) -> list:
        """تحميل كافة الماكينات من ملف data/machines.json"""
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Mapping Error] Failed to load machines: {e}")
            return []

    def get_all_machines_with_distance(self, user_lat: float, user_lon: float) -> list:
        """حساب المسافات لجميع الماكينات وترتيبهم حسب القرب من المستخدم"""
        machines = self.load_machines_from_json()
        processed_machines = []

        for machine in machines:
            m_lat = machine.get("lat")
            m_lon = machine.get("lon")

            # يتخطى الماكينة لو ملهاش إحداثيات بدلاً من رسمها في القاهرة بالخطأ
            if m_lat is None or m_lon is None:
                continue

            dist = LocationService.calculate_distance(user_lat, user_lon, m_lat, m_lon)
            machine_info = machine.copy()
            machine_info["lat"] = m_lat
            machine_info["lon"] = m_lon
            machine_info["distance_km"] = dist
            machine_info["display_name"] = machine.get("location") or machine.get("name") or machine.get("machine_id", "Unknown Machine")
            
            processed_machines.append(machine_info)

        # الترتيب حسب الأقرب
        processed_machines.sort(key=lambda x: x["distance_km"])
        return processed_machines

    @staticmethod
    def generate_google_maps_url(user_lat: float, user_lon: float, machine_lat: float, machine_lon: float) -> str:
        """توليد رابط Google Maps للاتجاهات"""
        return f"https://www.google.com/maps/dir/?api=1&origin={user_lat},{user_lon}&destination={machine_lat},{machine_lon}"

    def open_interactive_map(self, user_lat: float, user_lon: float, all_machines: list):
        """إنشاء الخريطة التفاعلية مع إظهار كل الماكينات وتوسيع الخريطة لتشمل الجميع"""
        my_map = folium.Map(location=[user_lat, user_lon], zoom_start=10)

        # قائمة لتجميع كل الإحداثيات للتحكم في حدود الخريطة تلقائياً (Bounds)
        all_coordinates = [[user_lat, user_lon]]

        # 1. إشارة موقع المستخدم الحقيقي / التجريبي
        folium.Marker(
            [user_lat, user_lon],
            popup="<b>📍 موقعك الحالي</b>",
            tooltip="موقعك الحالي",
            icon=folium.Icon(color="blue", icon="user", prefix="fa")
        ).add_to(my_map)

        # البحث عن أقرب ماكينة متاحة
        nearest_active_machine = None
        for m in all_machines:
            status = str(m.get("status", "")).lower()
            if status in ["available", "active"]:
                nearest_active_machine = m
                break

        # 2. إضافة كافة الماكينات الموجودة في ملف JSON على الخريطة
        for m in all_machines:
            m_lat = m.get("lat")
            m_lon = m.get("lon")

            if m_lat is None or m_lon is None:
                continue

            all_coordinates.append([m_lat, m_lon])

            status = str(m.get("status", "")).lower()
            is_available = status in ["available", "active"]
            
            marker_color = "darkgreen" if is_available else "red"
            icon_name = "recycle" if is_available else "wrench"
            status_text = "متاحة للتدوير ✅" if is_available else "تحت الصيانة / غير متاحة ⚠️"
            
            is_nearest = (nearest_active_machine and m.get("machine_id") == nearest_active_machine.get("machine_id"))
            nearest_badge = "<b style='color: green;'>[⭐ الأقرب إليك!]</b><br>" if is_nearest else ""

            g_url = self.generate_google_maps_url(user_lat, user_lon, m_lat, m_lon)
            popup_html = f"""
            <div style="font-family: Arial; font-size: 14px; direction: rtl; text-align: right; min-width: 180px;">
                {nearest_badge}
                <b>♻️ ماكينة:</b> {m['display_name']}<br>
                <b>الحالة:</b> {status_text}<br>
                <b>📏 المسافة:</b> {m.get('distance_km', 'N/A')} كم<br><br>
                <a href="{g_url}" target="_blank" style="background-color: #2e7d32; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; display: inline-block;">فتح الاتجاهات في Google Maps</a>
            </div>
            """
            
            folium.Marker(
                [m_lat, m_lon],
                popup=popup_html,
                tooltip=f"{m['display_name']} ({m.get('distance_km')} km)",
                icon=folium.Icon(color=marker_color, icon=icon_name, prefix="fa")
            ).add_to(my_map)

        # 3. رسم مسار يصل المستخدم بأقرب ماكينة نشطة
        if nearest_active_machine:
            folium.PolyLine(
                locations=[[user_lat, user_lon], [nearest_active_machine['lat'], nearest_active_machine['lon']]],
                color="#1E88E5",
                weight=3.5,
                opacity=0.8,
                tooltip=f"أقرب مسار لماكينة: {nearest_active_machine['display_name']}"
            ).add_to(my_map)

        # 4. ضبط أبعاد الخريطة تلقائياً لتظهر كافة الماكينات في المحافظات
        if len(all_coordinates) > 1:
            my_map.fit_bounds(all_coordinates, padding=[30, 30])

        map_filename = "map_view.html"
        my_map.save(map_filename)
        webbrowser.open(map_filename)


# ================= =================
#  قسم الواجهة الرسومية GUI (Pygame OOP)
# ================= =================

class Button:
    """كلاس الزرار التفاعلي"""
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


class MappingGUI:
    """كلاس إدارة وتطبيق واجهة شاشة الخرائط بـ Pygame"""
    def __init__(self, user_lat: float, user_lon: float, machine_manager: MachineManager):
        self.user_lat = user_lat
        self.user_lon = user_lon
        self.machine_manager = machine_manager
        self.all_machines = self.machine_manager.get_all_machines_with_distance(self.user_lat, self.user_lon)
        
        self.width = 850
        self.height = 550
        
        self.container_x = 30
        self.container_y = 115
        self.container_w = self.width - 60
        self.container_h = 350

        self.scroll_y = 0
        self.scroll_speed = 20

        self.DARK_GREEN = (46, 125, 50)
        self.ACCENT_GREEN = (76, 175, 80)
        self.BG_COLOR = (245, 247, 250)
        self.WHITE = (255, 255, 255)
        self.TEXT_DARK = (33, 33, 33)
        self.RED_COLOR = (211, 47, 47)

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EcoReward - Nearest Machines Finder")

        font_title = pygame.font.SysFont("Arial", 24, bold=True)
        font_body = pygame.font.SysFont("Arial", 15)
        font_btn = pygame.font.SysFont("Arial", 16, bold=True)

        btn_open_map = Button(220, 485, 250, 45, "Open Interactive Map", self.DARK_GREEN, self.ACCENT_GREEN)
        btn_exit = Button(490, 485, 140, 45, "Exit", (180, 40, 40), (220, 60, 60))

        card_height = 55
        card_gap = 10
        total_content_h = len(self.all_machines) * (card_height + card_gap)
        max_scroll = max(0, total_content_h - self.container_h)

        clock = pygame.time.Clock()
        running = True

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        self.scroll_y = max(0, self.scroll_y - self.scroll_speed)
                    elif event.button == 5:
                        self.scroll_y = min(max_scroll, self.scroll_y + self.scroll_speed)

                if btn_open_map.is_clicked(mouse_pos, event.type):
                    self.machine_manager.open_interactive_map(self.user_lat, self.user_lon, self.all_machines)

                if btn_exit.is_clicked(mouse_pos, event.type):
                    running = False

            btn_open_map.check_hover(mouse_pos)
            btn_exit.check_hover(mouse_pos)

            screen.fill(self.BG_COLOR)

            # Header
            pygame.draw.rect(screen, self.DARK_GREEN, (0, 0, self.width, 70))
            title_surf = font_title.render("EcoReward - RVM Machines Map Finder", True, self.WHITE)
            screen.blit(title_surf, (20, 20))

            loc_text = font_body.render(f"Current User Location: Lat {self.user_lat}, Lon {self.user_lon}", True, self.TEXT_DARK)
            screen.blit(loc_text, (30, 85))

            # القائمة القابلة للتمرير
            list_surface = pygame.Surface((self.container_w, self.container_h))
            list_surface.fill(self.BG_COLOR)

            if not self.all_machines:
                no_data_surf = font_body.render("No machines found with valid coordinates.", True, (150, 50, 50))
                list_surface.blit(no_data_surf, (20, 20))
            else:
                curr_y = -self.scroll_y

                for idx, m in enumerate(self.all_machines, 1):
                    card_rect = pygame.Rect(0, curr_y, self.container_w - 18, card_height)
                    pygame.draw.rect(list_surface, self.WHITE, card_rect, border_radius=8)
                    pygame.draw.rect(list_surface, (220, 224, 230), card_rect, width=1, border_radius=8)

                    status_str = str(m.get("status", "")).lower()
                    is_available = status_str in ["available", "active"]
                    status_text = "Available" if is_available else "Maintenance"
                    status_color = self.DARK_GREEN if is_available else self.RED_COLOR

                    name_surf = font_body.render(f"{idx}. {m['display_name']}", True, self.TEXT_DARK)
                    dist_surf = font_body.render(f"{m['distance_km']} km", True, self.TEXT_DARK)
                    stat_surf = font_body.render(status_text, True, status_color)

                    list_surface.blit(name_surf, (20, curr_y + 16))
                    list_surface.blit(stat_surf, (self.container_w - 280, curr_y + 16))
                    list_surface.blit(dist_surf, (self.container_w - 120, curr_y + 16))

                    curr_y += card_height + card_gap

                if max_scroll > 0:
                    scrollbar_w = 8
                    scrollbar_x = self.container_w - scrollbar_w
                    pygame.draw.rect(list_surface, (220, 225, 230), (scrollbar_x, 0, scrollbar_w, self.container_h), border_radius=4)

                    handle_h = max(30, int((self.container_h / total_content_h) * self.container_h))
                    handle_y = int((self.scroll_y / max_scroll) * (self.container_h - handle_h))
                    pygame.draw.rect(list_surface, self.DARK_GREEN, (scrollbar_x, handle_y, scrollbar_w, handle_h), border_radius=4)

            screen.blit(list_surface, (self.container_x, self.container_y))

            btn_open_map.draw(screen, font_btn)
            btn_exit.draw(screen, font_btn)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


# ================= =================
#  التشغيل الرئيسي
# ================= =================

if __name__ == "__main__":
    u_lat, u_lon = LocationService.get_current_user_location()
    manager = MachineManager()
    gui = MappingGUI(u_lat, u_lon, manager)
    gui.run()