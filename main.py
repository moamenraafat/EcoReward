import os
import sys
import pygame

# ============================================================
# EcoReward / RVM - Main Application Hub
# Integrates the existing project modules and their GUIs.
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Import the existing project modules.
MODULES = {}
IMPORT_ERRORS = {}

_MODULE_NAMES = [
    "storage",
    "user",
    "transaction",
    "machines",
    "materials",
    "reward",
    "redemption",
    "receipt",
    "mapping",
    "analytics",
    "excel_reports",
]

for _name in _MODULE_NAMES:
    try:
        MODULES[_name] = __import__(_name)
    except Exception as exc:
        IMPORT_ERRORS[_name] = str(exc)


PALETTE = {
    "screen_bg": (15, 23, 42),
    "panel_bg": (30, 41, 59),
    "panel_border": (71, 85, 105),
    "header_bg": (2, 132, 199),
    "header_dark": (15, 23, 42),
    "text_white": (248, 250, 252),
    "text_muted": (148, 163, 184),
    "text_dark": (15, 23, 42),
    "btn_primary": (37, 99, 235),
    "btn_primary_h": (29, 78, 216),
    "btn_success": (22, 163, 74),
    "btn_success_h": (21, 128, 61),
    "btn_accent": (217, 119, 6),
    "btn_accent_h": (180, 83, 9),
    "btn_purple": (124, 58, 237),
    "btn_purple_h": (109, 40, 217),
    "danger": (220, 38, 38),
    "danger_h": (185, 28, 28),
}


class TerminalButton:
    def __init__(self, rect, text, font, bg_color, hover_color, text_color, action):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.action = action

    def draw(self, surface, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, PALETTE["panel_border"], self.rect, 1, border_radius=8)

        text_surface = self.font.render(self.text, True, self.text_color)
        surface.blit(text_surface, text_surface.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            if self.action:
                self.action()


def _launch_gui(module_name, gui_factory, status_callback):
    """Run one of the existing module GUIs, then restore the main hub."""
    module = MODULES.get(module_name)
    if module is None:
        status_callback(f"{module_name}: module could not be loaded.")
        return None

    try:
        gui = gui_factory(module)
        if gui is not None:
            gui.run()
        return gui
    except Exception as exc:
        print(f"[Main Hub] {module_name} GUI error: {exc}")
        status_callback(f"{module_name}: {exc}")
        return None
    finally:
        # Some child GUIs change the display surface. Re-create our surface.
        pygame.display.set_mode((1024, 768))
        pygame.display.set_caption("EcoReward - RVM Main Hub")


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("EcoReward - RVM Main Hub")
    clock = pygame.time.Clock()

    f_title = pygame.font.SysFont("Arial", 30, bold=True)
    f_subtitle = pygame.font.SysFont("Arial", 17)
    f_btn = pygame.font.SysFont("Arial", 16, bold=True)
    f_small = pygame.font.SysFont("Arial", 14)
    f_metric = pygame.font.SysFont("Arial", 22, bold=True)

    state = {
        "current_screen": "home",
        "status": "System ready.",
        "user": None,
    }

    def status(message):
        state["status"] = str(message)

    def home():
        state["current_screen"] = "home"

    # -------------------------
    # Existing project GUIs
    # -------------------------
    def open_auth():
        result = _launch_gui(
            "user",
            lambda m: type("AuthRunner", (), {"run": staticmethod(m.run_gui)})(),
            status,
        )
        # user.run_gui() returns the logged-in User object when the window closes.
        if result is not None:
            pass

    def open_materials():
        _launch_gui(
            "materials",
            lambda m: m.MaterialManagerGUI(m.materialmanager()),
            status,
        )

    def open_machines():
        _launch_gui(
            "machines",
            lambda m: m.MachineManagerGUI(m.machinemanager()),
            status,
        )

    def open_rewards():
        _launch_gui(
            "reward",
            lambda m: m.RewardManagerGUI(m.RewardManager()),
            status,
        )

    def open_transactions():
        _launch_gui(
            "transaction",
            lambda m: m.TransactionGUI(),
            status,
        )

    def open_analytics():
        _launch_gui(
            "analytics",
            lambda m: m.AnalyticsGUI(m.AnalyticsManager()),
            status,
        )

    def open_mapping():
        try:
            mapping = MODULES.get("mapping")
            if mapping is None:
                raise RuntimeError("mapping module could not be loaded.")

            lat, lon = mapping.LocationService.get_current_user_location()
            _launch_gui(
                "mapping",
                lambda m: m.MappingGUI(
                    lat,
                    lon,
                    m.MachineManager(),
                ),
                status,
            )
        except Exception as exc:
            status(f"Map error: {exc}")

    def open_redemption():
        # Redemption needs a user id and current point balance.
        # If the user is not authenticated in this hub, use the existing
        # authentication GUI first.
        user = state.get("user")
        if not user:
            status("Please sign in first to use Reward Redemption.")
            open_auth()
            return

        try:
            user_id = getattr(user, "user_id", getattr(user, "id", None))
            points = getattr(user, "points", 0)
            _launch_gui(
                "redemption",
                lambda m: m.RedemptionGUI(m.Redemption(), user_id, points),
                status,
            )
        except Exception as exc:
            status(f"Redemption error: {exc}")

    def open_receipt():
        _launch_gui(
            "receipt",
            lambda m: type(
                "ReceiptRunner",
                (),
                {"run": staticmethod(m.generate_receipt)}
            )(),
            status,
        )

    def open_storage():
        _launch_gui(
            "storage",
            lambda m: m.StorageGUI(m.JSONStorageManager()),
            status,
        )

    def open_reports():
        _launch_gui(
            "excel_reports",
            lambda m: m.ExcelReportGUI(m.ExcelReportExporter(REPORTS_DIR)),
            status,
        )

    # -------------------------
    # Simple hub-only auth bridge
    # -------------------------
    def open_auth_and_capture():
        module = MODULES.get("user")
        if module is None:
            status("User module could not be loaded.")
            return

        try:
            # The original user.py GUI owns its own loop and returns its
            # authenticated User object when its window closes.
            logged_user = module.run_gui()
            if logged_user is not None:
                state["user"] = logged_user
                name = getattr(logged_user, "name", "User")
                status(f"Signed in as {name}.")
            else:
                status("Authentication window closed.")
        except Exception as exc:
            print(f"[Main Hub] Authentication error: {exc}")
            status(f"Authentication error: {exc}")
        finally:
            pygame.display.set_mode((1024, 768))
            pygame.display.set_caption("EcoReward - RVM Main Hub")

    # Replace the helper with the version that captures the returned user.
    open_auth = open_auth_and_capture

    def open_redemption_safe():
        user = state.get("user")
        if not user:
            status("No logged-in user. Open User Account / Auth first.")
            return

        try:
            module = MODULES.get("redemption")
            if module is None:
                raise RuntimeError("redemption module could not be loaded.")

            user_id = getattr(user, "user_id", getattr(user, "id", None))
            points = getattr(user, "points", 0)

            module.RedemptionGUI(module.Redemption(), user_id, points).run()
            pygame.display.set_mode((1024, 768))
            pygame.display.set_caption("EcoReward - RVM Main Hub")
            status("Returned from Reward Redemption.")
        except Exception as exc:
            print(f"[Main Hub] Redemption error: {exc}")
            status(f"Redemption error: {exc}")
            pygame.display.set_mode((1024, 768))
            pygame.display.set_caption("EcoReward - RVM Main Hub")

    open_redemption = open_redemption_safe

    # -------------------------
    # Home buttons
    # -------------------------
    buttons = [
        TerminalButton(
            (70, 245, 270, 54), "User Account / Auth", f_btn,
            PALETTE["btn_primary"], PALETTE["btn_primary_h"],
            PALETTE["text_white"], open_auth
        ),
        TerminalButton(
            (377, 245, 270, 54), "Start Recycling", f_btn,
            PALETTE["btn_success"], PALETTE["btn_success_h"],
            PALETTE["text_white"], open_transactions
        ),
        TerminalButton(
            (684, 245, 270, 54), "Materials Manager", f_btn,
            PALETTE["btn_accent"], PALETTE["btn_accent_h"],
            PALETTE["text_white"], open_materials
        ),
        TerminalButton(
            (70, 320, 270, 54), "Machine Manager", f_btn,
            PALETTE["btn_primary"], PALETTE["btn_primary_h"],
            PALETTE["text_white"], open_machines
        ),
        TerminalButton(
            (377, 320, 270, 54), "Rewards Catalog", f_btn,
            PALETTE["btn_purple"], PALETTE["btn_purple_h"],
            PALETTE["text_white"], open_rewards
        ),
        TerminalButton(
            (684, 320, 270, 54), "Redeem Reward", f_btn,
            PALETTE["btn_success"], PALETTE["btn_success_h"],
            PALETTE["text_white"], open_redemption
        ),
        TerminalButton(
            (70, 395, 270, 54), "Find a Machine / Map", f_btn,
            PALETTE["btn_primary"], PALETTE["btn_primary_h"],
            PALETTE["text_white"], open_mapping
        ),
        TerminalButton(
            (377, 395, 270, 54), "Analytics Dashboard", f_btn,
            PALETTE["btn_accent"], PALETTE["btn_accent_h"],
            PALETTE["text_white"], open_analytics
        ),
        TerminalButton(
            (684, 395, 270, 54), "Digital Receipt", f_btn,
            PALETTE["btn_purple"], PALETTE["btn_purple_h"],
            PALETTE["text_white"], open_receipt
        ),
        TerminalButton(
            (70, 470, 270, 54), "JSON Storage", f_btn,
            PALETTE["panel_bg"], PALETTE["btn_primary"],
            PALETTE["text_white"], open_storage
        ),
        TerminalButton(
            (377, 470, 270, 54), "Excel Reports", f_btn,
            PALETTE["btn_success"], PALETTE["btn_success_h"],
            PALETTE["text_white"], open_reports
        ),
        TerminalButton(
            (684, 470, 270, 54), "Exit Hub", f_btn,
            PALETTE["danger"], PALETTE["danger_h"],
            PALETTE["text_white"], lambda: state.update({"current_screen": "quit"})
        ),
    ]

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif state["current_screen"] == "home":
                for button in buttons:
                    button.handle_event(event)

        if state["current_screen"] == "quit":
            running = False

        screen.fill(PALETTE["screen_bg"])

        # Header
        pygame.draw.rect(screen, PALETTE["header_dark"], (0, 0, 1024, 115))
        pygame.draw.rect(screen, PALETTE["header_bg"], (0, 108, 1024, 7))

        title = f_title.render("EcoReward", True, PALETTE["text_white"])
        subtitle = f_subtitle.render(
            "RVM Main Hub • Recycling • Rewards • Analytics • Management",
            True,
            PALETTE["text_muted"],
        )
        screen.blit(title, (50, 30))
        screen.blit(subtitle, (50, 70))

        # Login indicator
        if state["user"]:
            user_name = getattr(state["user"], "name", "User")
            user_points = getattr(state["user"], "points", 0)
            user_text = f"User: {user_name}  |  Points: {user_points}"
            user_color = PALETTE["btn_success"]
        else:
            user_text = "User: Guest"
            user_color = PALETTE["text_muted"]

        user_surface = f_small.render(user_text, True, user_color)
        screen.blit(user_surface, (700, 48))

        # Status panel
        status_rect = pygame.Rect(50, 140, 924, 70)
        pygame.draw.rect(screen, PALETTE["panel_bg"], status_rect, border_radius=10)
        pygame.draw.rect(screen, PALETTE["panel_border"], status_rect, 1, border_radius=10)
        screen.blit(
            f_small.render(f"System Status: {state['status']}", True, PALETTE["text_muted"]),
            (70, 166),
        )

        # Buttons
        for button in buttons:
            button.draw(screen, mouse_pos)

        # Footer / module health
        loaded = len(MODULES)
        failed = len(IMPORT_ERRORS)
        health = f"Modules loaded: {loaded}/{len(_MODULE_NAMES)}"
        if failed:
            health += f"  |  Import issues: {failed}"

        screen.blit(
            f_small.render(health, True, PALETTE["text_muted"]),
            (50, 555),
        )

        if failed:
            # Keep the warning compact; detailed errors stay in the terminal.
            screen.blit(
                f_small.render(
                    "Some optional modules failed to import. Check the terminal for details.",
                    True,
                    PALETTE["btn_accent"],
                ),
                (50, 580),
            )
        else:
            screen.blit(
                f_small.render(
                    "All core project modules loaded successfully.",
                    True,
                    PALETTE["btn_success"],
                ),
                (50, 580),
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
