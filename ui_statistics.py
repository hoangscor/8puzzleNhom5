import pygame
from ui_system import Panel, Label, Button, BG_COLOR, SUBTEXT_COLOR, DANGER_ACCENT, SECONDARY_ACCENT, PRIMARY_ACCENT

class GameDashboard:
    """
    Manages the UI layout excluding the tiles.
    Includes Header, Board Container, Stats Dashboard, and Control Panels.
    """
    def __init__(self, screen_width, screen_height, callbacks):
        self.elements = []
        
        # --- 1. Header Section ---
        header_y = 20
        self.elements.append(Label((screen_width // 2, header_y + 20), "TRÒ CHƠI 8-PUZZLE", font_size=36, bold=True, center=True))
        
        # Image name indicator
        self.image_label = Label((screen_width // 2, header_y + 55), "Ảnh: [chưa tải]", font_size=16, color=SUBTEXT_COLOR, center=True)
        self.elements.append(self.image_label)

        # --- 2. Middle: Board Background ---
        # The main panel where tiles will reside
        self.board_rect = pygame.Rect((screen_width - 580) // 2, 110, 580, 580)
        self.elements.append(Panel(self.board_rect, radius=10))
        
        # --- 3. Left: Statistics Panel ---
        stats_rect = pygame.Rect(40, 110, 270, 580)
        self.elements.append(Panel(stats_rect))
        self.elements.append(Label((stats_rect.centerx, stats_rect.y + 40), "THÔNG SỐ", font_size=24, bold=True, center=True))
        
        stats_y = stats_rect.y + 100
        # Dynamic stat labels
        self.elements.append(Label((stats_rect.x + 30, stats_y), "Thời gian chơi", font_size=18, color=SUBTEXT_COLOR))
        self.play_time_val = Label((stats_rect.x + 30, stats_y + 30), "00:00", font_size=22, bold=True)
        self.elements.append(self.play_time_val)
        
        self.elements.append(Label((stats_rect.x + 30, stats_y + 100), "Thời gian giải", font_size=18, color=SUBTEXT_COLOR))
        self.solve_time_val = Label((stats_rect.x + 30, stats_y + 130), "0.0 ms", font_size=22, bold=True)
        self.elements.append(self.solve_time_val)
        
        self.elements.append(Label((stats_rect.x + 30, stats_y + 200), "Số bước duyệt", font_size=18, color=SUBTEXT_COLOR))
        self.nodes_val = Label((stats_rect.x + 30, stats_y + 230), "0", font_size=22, bold=True)
        self.elements.append(self.nodes_val)

        # --- 4. Right: Controls Panel ---
        ctrl_rect = pygame.Rect(screen_width - 310, 110, 270, 580)
        self.elements.append(Panel(ctrl_rect))
        self.elements.append(Label((ctrl_rect.centerx, ctrl_rect.y + 40), "ĐIỀU KHIỂN", font_size=24, bold=True, center=True))
        
        btn_w = 210
        btn_x = ctrl_rect.centerx - btn_w // 2
        
        # Management buttons
        self.elements.append(Button((btn_x, ctrl_rect.y + 80, btn_w, 45), "Chèn ảnh", callback=callbacks['insert_image']))
        self.elements.append(Button((btn_x, ctrl_rect.y + 140, btn_w, 45), "Chơi lại", color=DANGER_ACCENT, callback=callbacks['reset_game']))
        
        # AI Solutions
        self.elements.append(Label((ctrl_rect.centerx, ctrl_rect.y + 220), "GIẢI THUẬT AI", font_size=20, bold=True, center=True))
        self.elements.append(Button((btn_x, ctrl_rect.y + 250, btn_w, 70), "Tìm kiếm BFS", color=SECONDARY_ACCENT, callback=callbacks['solve_bfs']))
        self.elements.append(Button((btn_x, ctrl_rect.y + 330, btn_w, 70), "Giải thuật A*", color=SECONDARY_ACCENT, callback=callbacks['solve_astar']))
        
        # History
        self.elements.append(Label((ctrl_rect.centerx, ctrl_rect.y + 430), "LỊCH SỬ", font_size=20, bold=True, center=True))
        self.elements.append(Button((btn_x, ctrl_rect.y + 460, btn_w, 45), "<< Đi lui", color=PRIMARY_ACCENT, callback=callbacks['undo']))
        self.elements.append(Button((btn_x, ctrl_rect.y + 515, btn_w, 45), "Đi tới >>", color=PRIMARY_ACCENT, callback=callbacks['redo']))

    def update_image_name(self, name):
        display_name = name if len(name) < 25 else name[:22] + "..."
        self.image_label.text = f"Ảnh: {display_name}"

    def update_stats(self, play_time="00:00", solve_time="0.0 ms", nodes="0"):
        self.play_time_val.text = play_time
        self.solve_time_val.text = solve_time
        self.nodes_val.text = nodes

    def handle_event(self, event):
        for element in self.elements:
            element.handle_event(event)

    def draw(self, screen):
        for element in self.elements:
            element.draw(screen)