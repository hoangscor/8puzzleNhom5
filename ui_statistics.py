import pygame
from ui_system import Panel, Label, Button, ToggleButton, BG_COLOR, SUBTEXT_COLOR, DANGER_ACCENT, SECONDARY_ACCENT, PRIMARY_ACCENT, SUCCESS_ACCENT

class GameDashboard:
    """
    Manages the UI layout excluding the tiles.
    Uses a premium 2-column layout: Left (Board) and Right (Unified Dashboard panel).
    """
    def __init__(self, screen_width, screen_height, callbacks):
        self.elements = []
        self.algo_buttons = {}
        self.speed_buttons = {}
        self.size_buttons = {}
        self.goal_buttons = {}
        
        # --- 1. Header Section ---
        header_y = 15
        self.elements.append(Label((screen_width // 2, header_y + 15), "TRỰC QUAN HÓA THUẬT TOÁN N-PUZZLE", font_size=30, bold=True, center=True))
        
        # Image name indicator
        self.image_label = Label((screen_width // 2, header_y + 50), "Ảnh: [Chữ số]", font_size=15, color=SUBTEXT_COLOR, center=True)
        self.elements.append(self.image_label)

        # --- 2. Left Side: Board Container ---
        # Positioned at x=50, y=100. Fits 580x580 board perfectly.
        self.board_rect = pygame.Rect(50, 100, 580, 580)
        self.elements.append(Panel(self.board_rect, radius=12))
        
        # --- 3. Right Side: Unified Dashboard Panel ---
        # Positioned at x=660, y=100. Fits 570x580 control and stats center.
        dash_rect = pygame.Rect(660, 100, 570, 580)
        self.elements.append(Panel(dash_rect, radius=12))
        
        # --- SUB-SECTION 3A: Dashboard Left Column (Stats & Preview) ---
        sub_x = dash_rect.x + 25
        
        # Game Stats
        self.elements.append(Label((sub_x + 105, dash_rect.y + 15), "TRẠNG THÁI GAME", font_size=16, bold=True, center=True))
        
        self.elements.append(Label((sub_x, dash_rect.y + 45), "Thời gian chơi:", font_size=13, color=SUBTEXT_COLOR))
        self.game_time_val = Label((sub_x + 140, dash_rect.y + 45), "00:00", font_size=14, bold=True)
        self.elements.append(self.game_time_val)
        
        self.elements.append(Label((sub_x, dash_rect.y + 68), "Số bước đi:", font_size=13, color=SUBTEXT_COLOR))
        self.game_moves_val = Label((sub_x + 140, dash_rect.y + 68), "0", font_size=14, bold=True)
        self.elements.append(self.game_moves_val)
        
        # Progress Bar (Centered in Section 3A, increased height to 24px)
        from ui_system import ProgressBar
        self.progress_bar = ProgressBar((sub_x, dash_rect.y + 98, 215, 22))
        self.elements.append(self.progress_bar)
        
        # Separator line
        self.stats_sep_y = dash_rect.y + 130
        
        # Simulation Stats
        self.elements.append(Label((sub_x + 105, dash_rect.y + 140), "THÔNG SỐ DUYỆT", font_size=16, bold=True, color=SECONDARY_ACCENT, center=True))
        
        sim_stats_start_y = dash_rect.y + 168
        sim_labels = [
            ("Đã duyệt (Explored):", "nodes_expanded_val", "0"),
            ("Hàng đợi (Frontier):", "frontier_val", "0"),
            ("Độ sâu g(n):", "depth_val", "0"),
            ("Ước lượng h(n):", "h_val", "0"),
            ("Tổng f(n):", "f_val", "0"),
            ("Thời gian chạy:", "duration_val", "0.0 ms")
        ]
        
        for i, (label_text, attr_name, default_val) in enumerate(sim_labels):
            y_pos = sim_stats_start_y + i * 36
            self.elements.append(Label((sub_x, y_pos), label_text, font_size=12, color=SUBTEXT_COLOR))
            val_label = Label((sub_x, y_pos + 15), default_val, font_size=13, bold=True)
            setattr(self, attr_name, val_label)
            self.elements.append(val_label)

        # Original Image Preview Box (Centered at bottom of Left Column)
        self.preview_rect = pygame.Rect(sub_x + 7, dash_rect.y + 400, 200, 160)
        self.elements.append(Panel(self.preview_rect, radius=8))
        self.elements.append(Label((self.preview_rect.centerx, self.preview_rect.centery - 10), "Xem trước ảnh", font_size=13, color=SUBTEXT_COLOR, center=True))
        self.elements.append(Label((self.preview_rect.centerx, self.preview_rect.centery + 10), "[Chưa tải]", font_size=11, color=SUBTEXT_COLOR, center=True))

        # --- SUB-SECTION 3B: Dashboard Right Column (Controls & AI) ---
        sub_x2 = dash_rect.x + 285
        
        # General Controls
        self.elements.append(Label((sub_x2 + 110, dash_rect.y + 15), "ĐIỀU KHIỂN CHUNG", font_size=16, bold=True, center=True))
        self.elements.append(Button((sub_x2, dash_rect.y + 42, 105, 30), "Chèn ảnh", font_size=13, callback=callbacks['insert_image']))
        self.elements.append(Button((sub_x2 + 115, dash_rect.y + 42, 105, 30), "Chơi lại", font_size=13, color=DANGER_ACCENT, callback=callbacks['reset_game']))
        
        # Size Selector Section
        self.elements.append(Label((sub_x2 + 110, dash_rect.y + 85), "KÍCH THƯỚC BÀN CỜ", font_size=15, bold=True, center=True))
        sizes = [
            ("3x3", 3, sub_x2, 65),
            ("4x4", 4, sub_x2 + 77, 65),
            ("5x5", 5, sub_x2 + 155, 65),
            ("8x8", 8, sub_x2 + 230, 65)
        ]
        for text, val, x, w in sizes:
            cb = lambda v=val: callbacks['change_size'](v)
            btn = ToggleButton((x, dash_rect.y + 110, w, 28), text, font_size=13, callback=cb)
            self.size_buttons[val] = btn
            self.elements.append(btn)
        
        # AI Algorithms Section (Compact grid layout)
        self.elements.append(Label((sub_x2 + 110, dash_rect.y + 150), "THUẬT TOÁN AI", font_size=15, bold=True, color=SECONDARY_ACCENT, center=True))
        algos = [
            ("Bi-A*", "bi_astar", sub_x2, dash_rect.y + 172, 105),
            ("IDA*", "idastar", sub_x2 + 115, dash_rect.y + 172, 105),
            ("A* Manhattan", "astar_manhattan", sub_x2, dash_rect.y + 208, 105),
            ("A* Misplaced", "astar_misplaced", sub_x2 + 115, dash_rect.y + 208, 105),
            ("GBFS Manhattan", "gbfs", sub_x2, dash_rect.y + 244, 105)
        ]
        for text, key, x, y, w in algos:
            cb = lambda k=key: callbacks['select_algorithm'](k)
            btn = ToggleButton((x, y, w, 30), text, font_size=12, callback=cb)
            self.algo_buttons[key] = btn
            self.elements.append(btn)
            
        # Compare Algorithms Button next to GBFS
        self.elements.append(Button((sub_x2 + 115, dash_rect.y + 244, 105, 30), "So sánh", font_size=12, color=SECONDARY_ACCENT, callback=callbacks['compare_solvers']))
            
        # Goal State Preset Section
        self.elements.append(Label((sub_x2 + 110, dash_rect.y + 284), "KIỂU ĐÍCH ĐẾN", font_size=15, bold=True, center=True))
        goals = [
            ("Mặc định", "default", sub_x2),
            ("Xoắn ốc", "spiral", sub_x2 + 76),
            ("Theo cột", "columns", sub_x2 + 152)
        ]
        for text, key, x in goals:
            cb = lambda k=key: callbacks['change_goal_preset'](k)
            btn = ToggleButton((x, dash_rect.y + 306, 68, 28), text, font_size=11, callback=cb)
            self.goal_buttons[key] = btn
            self.elements.append(btn)
            
        # Simulation Playback Controls
        self.elements.append(Label((sub_x2 + 110, dash_rect.y + 360), "ĐIỀU KHIỂN MÔ PHỎNG", font_size=15, bold=True, center=True))
        sim_y = dash_rect.y + 382
        self.elements.append(Button((sub_x2, sim_y, 45, 30), "<<", font_size=14, callback=callbacks['step_backward']))
        self.play_btn = Button((sub_x2 + 55, sim_y, 65, 30), "Play", font_size=13, color=SUCCESS_ACCENT, callback=callbacks['play_pause'])
        self.elements.append(self.play_btn)
        self.elements.append(Button((sub_x2 + 130, sim_y, 45, 30), ">>", font_size=14, callback=callbacks['step_forward']))
        self.elements.append(Button((sub_x2 + 185, sim_y, 35, 30), "Stop", font_size=11, color=DANGER_ACCENT, callback=callbacks['stop_simulation']))
        
        # Simulation Speed Selector
        self.elements.append(Label((sub_x2 + 110, dash_rect.y + 426), "TỐC ĐỘ MÔ PHỎNG", font_size=15, bold=True, center=True))
        speeds = [
            ("Chậm", "slow", sub_x2),
            ("Vừa", "medium", sub_x2 + 55),
            ("Nhanh", "fast", sub_x2 + 110),
            ("Max", "max", sub_x2 + 165)
        ]
        for text, key, x in speeds:
            cb = lambda k=key: callbacks['select_speed'](k)
            btn = ToggleButton((x, dash_rect.y + 448, 50, 28), text, font_size=12, callback=cb)
            self.speed_buttons[key] = btn
            self.elements.append(btn)
            
        # Undo / Redo / Export Section
        self.elements.append(Label((sub_x2 + 110, dash_rect.y + 492), "LỊCH SỬ & XUẤT LOG", font_size=15, bold=True, center=True))
        self.elements.append(Button((sub_x2, dash_rect.y + 514, 68, 30), "Đi lui", font_size=12, color=PRIMARY_ACCENT, callback=callbacks['undo']))
        self.elements.append(Button((sub_x2 + 76, dash_rect.y + 514, 68, 30), "Đi tới", font_size=12, color=PRIMARY_ACCENT, callback=callbacks['redo']))
        self.elements.append(Button((sub_x2 + 152, dash_rect.y + 514, 68, 30), "Xuất log", font_size=12, color=SECONDARY_ACCENT, callback=callbacks['export_log']))

    def update_image_name(self, name):
        display_name = name if len(name) < 25 else name[:22] + "..."
        self.image_label.text = f"Ảnh: {display_name}"

    def update_game_stats(self, elapsed_time_str, moves_count):
        self.game_time_val.text = elapsed_time_str
        self.game_moves_val.text = str(moves_count)

    def update_simulation_stats(self, nodes_expanded, frontier_size, depth, h_val, f_val, duration_ms):
        self.nodes_expanded_val.text = str(nodes_expanded)
        self.frontier_val.text = str(frontier_size)
        self.depth_val.text = str(depth)
        self.h_val.text = str(h_val)
        self.f_val.text = str(f_val)
        self.duration_val.text = f"{duration_ms:.1f} ms"

    def set_active_algorithm(self, algo_name):
        for name, btn in self.algo_buttons.items():
            btn.active = (name == algo_name)
            
    def set_active_speed(self, speed_name):
        for name, btn in self.speed_buttons.items():
            btn.active = (name == speed_name)
            
    def set_active_size(self, size_val):
        for val, btn in self.size_buttons.items():
            btn.active = (val == size_val)
            
    def set_active_goal_preset(self, preset_name):
        for name, btn in self.goal_buttons.items():
            btn.active = (name == preset_name)
            
    def set_play_state(self, is_playing):
        self.play_btn.text = "Pause" if is_playing else "Play"
        self.play_btn.base_color = DANGER_ACCENT if is_playing else SUCCESS_ACCENT

    def handle_event(self, event):
        for element in self.elements:
            element.handle_event(event)

    def update(self, dt):
        for element in self.elements:
            element.update(dt)

    def draw(self, screen):
        for element in self.elements:
            element.draw(screen)
            
        # Draw separators
        pygame.draw.line(screen, (45, 45, 65), (self.board_rect.right + 25, self.stats_sep_y), (self.board_rect.right + 25 + 215, self.stats_sep_y), 1)
