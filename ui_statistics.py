import pygame
from ui_system import (Panel, Label, Button, ToggleButton, SectionHeader, ProgressBar,
                       t, get_font, SCREEN_W, SCREEN_H)

# ─── Layout Constants ────────────────────────────────────────────────────────

MARGIN = 24
HEADER_H = 58

# Left workspace
PUZZLE_SIZE = 480
BOARD_SIZE = 512
BOARD_X = 36
BOARD_Y = HEADER_H + 20
BOARD_RECT = pygame.Rect(BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE)

PREVIEW_H = 56
PREVIEW_X = BOARD_X
PREVIEW_Y = BOARD_Y + BOARD_SIZE + 10
PREVIEW_RECT = pygame.Rect(PREVIEW_X, PREVIEW_Y, BOARD_SIZE, PREVIEW_H)

STATS_H = 58
STATS_X = BOARD_X
STATS_Y = PREVIEW_Y + PREVIEW_H + 8
STATS_RECT = pygame.Rect(STATS_X, STATS_Y, BOARD_SIZE, STATS_H)

# Right command surface
PANEL_X = BOARD_X + BOARD_SIZE + 28
PANEL_Y = BOARD_Y
PANEL_W = SCREEN_W - PANEL_X - MARGIN
PANEL_H = STATS_Y + STATS_H + MARGIN - PANEL_Y
PANEL_RECT = pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)

PX = PANEL_X + 20
PY = PANEL_Y + 18
PW = PANEL_W - 40


class GameDashboard:
    """Primary playfield on the left, command surface on the right."""

    def __init__(self, screen_width, screen_height, callbacks):
        self.elements = []
        self.algo_children = []
        self.settings_children = []
        self.algo_buttons = {}
        self.speed_buttons = {}
        self.size_buttons = {}
        self.goal_buttons = {}
        self.notification_text = ""
        self.notification_kind = "info"
        self.notification_timer = 0.0

        cx = PANEL_X + PANEL_W // 2

        # ── Header ──
        self.elements.append(Label((BOARD_X, 20), "N-PUZZLE", font_size=31, bold=True))
        self.elements.append(Label((BOARD_X + 178, 31), "Search Lab", font_size=14, color=t("secondary"), bold=True))
        self.image_label = Label((PANEL_X, 28), "Image: Digits",font_size=12, bold=True, color=t("secondary"))
        self.elements.append(self.image_label)

        # FPS counter
        self.fps_label = Label((SCREEN_W - 92, 28), "FPS: 60", font_size=12, bold=True, color=t("secondary"))
        self.elements.append(self.fps_label)

        # ── Left: Board ──
        self.board_rect = BOARD_RECT
        self.elements.append(Panel(self.board_rect, radius=14))

        # ── Left: Image Preview ──
        self.preview_rect = PREVIEW_RECT
        self.elements.append(Panel(self.preview_rect, radius=8))
        self.preview_label = Label((self.preview_rect.centerx, self.preview_rect.centery),
                                   "Digits board", font_size=12, color=t("subtext"), center=True)
        self.elements.append(self.preview_label)

        # ── Left: Stats Bar ──
        self.elements.append(Panel(STATS_RECT, radius=8))

        sx = STATS_X + 18
        sy = STATS_Y + 11

        self.nodes_label = Label((sx, sy), "Explored 0", font_size=12, color=t("subtext"))
        self.elements.append(self.nodes_label)
        self.frontier_label = Label((sx + 145, sy), "Frontier 0", font_size=12, color=t("subtext"))
        self.elements.append(self.frontier_label)
        self.h_label = Label((sx + 302, sy), "h 0", font_size=12, color=t("subtext"))
        self.elements.append(self.h_label)

        self.f_label = Label((sx, sy + 26), "f 0", font_size=12, color=t("subtext"))
        self.elements.append(self.f_label)
        self.depth_label = Label((sx + 82, sy + 26), "g 0", font_size=12, color=t("subtext"))
        self.elements.append(self.depth_label)
        self.duration_label = Label((sx + 164, sy + 26), "0.0 ms", font_size=12, color=t("subtext"))
        self.elements.append(self.duration_label)

        # Legend
        self.legend_label = Label((sx + 286, sy + 26), "", font_size=10, color=t("subtext"))
        self.elements.append(self.legend_label)

        # ── Right command surface ──
        self.elements.append(Panel(PANEL_RECT, radius=14))

        y = PY
        section_gap = 20

        self.elements.append(Label((PX, y), "SESSION", font_size=12, bold=True, color=t("secondary")))
        btn_w = (PW - 10) // 2
        self.elements.append(Button((PX, y + 24, btn_w, 30), "Add Image", font_size=12,
                                     color=t("primary"), callback=callbacks['insert_image']))
        self.elements.append(Button((PX + btn_w + 10, y + 24, btn_w, 30), "New Game", font_size=12,
                                     color=t("danger"), callback=callbacks['reset_game']))
        y += 66

        # ── Game Status ──
        status_w = (PW - 24) // 4
        self.elements.append(Label((PX, y), "TIME", font_size=10, color=t("subtext"), bold=True))
        self.game_time_val = Label((PX, y + 17), "00:00", font_size=22, bold=True)
        self.elements.append(self.game_time_val)

        self.elements.append(Label((PX + status_w, y), "MOVES", font_size=10, color=t("subtext"), bold=True))
        self.game_moves_val = Label((PX + status_w, y + 17), "0", font_size=22, bold=True)
        self.elements.append(self.game_moves_val)

        self.elements.append(Label((PX + status_w * 2, y), "BEST", font_size=10, color=t("subtext"), bold=True))
        self.high_score_label = Label((PX + status_w * 2, y + 20), "-", font_size=13, bold=True, color=t("success"))
        self.elements.append(self.high_score_label)

        self.elements.append(Label((PX + status_w * 3, y), "OPTIMAL", font_size=10, color=t("subtext"), bold=True))
        self.comparison_label = Label((PX + status_w * 3, y + 20), "-", font_size=13, bold=True, color=t("secondary"))
        self.elements.append(self.comparison_label)
        y += 52

        self.progress_bar = ProgressBar((PX, y, PW, 14))
        self.elements.append(self.progress_bar)
        y += 32

        # ── Solver controls ──
        self.elements.append(SectionHeader(cx, y, "SOLVER", PW - 30, font_size=12))
        y += section_gap

        bw2 = (PW - 10) // 2
        algos = [
            ("Bi-A*", "bi_astar"), ("IDA*", "idastar"),
            ("A* Manhattan", "astar_manhattan"), ("A* Misplaced", "astar_misplaced"),
            ("GBFS", "gbfs"),
        ]
        algo_y = y
        for i, (text, key) in enumerate(algos):
            col = i % 2
            row = i // 2
            bx = PX + col * (bw2 + 10)
            by = algo_y + row * 28
            b = ToggleButton((bx, by, bw2, 24), text, font_size=11,
                             callback=lambda k=key: callbacks['select_algorithm'](k))
            self.algo_buttons[key] = b
            self.elements.append(b)

        # Speed row
        speed_y = algo_y + 86
        spd_label = Label((PX, speed_y + 2), "Speed", font_size=10, color=t("subtext"), bold=True)
        self.elements.append(spd_label)
        speed_w = (PW - 58) // 4
        for i, (text, key) in enumerate([("Slow", "slow"), ("Med", "medium"), ("Fast", "fast"), ("Max", "max")]):
            bx = PX + 56 + i * (speed_w + 3)
            b = ToggleButton((bx, speed_y, speed_w, 20), text, font_size=10,
                             callback=lambda k=key: callbacks['select_speed'](k))
            self.speed_buttons[key] = b
            self.elements.append(b)

        # Compare + Play controls row
        ctrl_y = speed_y + 26
        self.algo_children.append(
            Button((PX, ctrl_y, bw2, 26), "Compare",
                   font_size=10, color=t("secondary"), callback=callbacks['compare_solvers'])
        )
        self.elements.append(self.algo_children[-1])
        sim_btns = [("<", 'step_backward'), ("Run", 'play_pause'), (">", 'step_forward'), ("Stop", 'stop_simulation')]
        sim_w = (bw2 - 18) // 4
        for i, (text, key) in enumerate(sim_btns):
            bx = PX + bw2 + 10 + i * (sim_w + 6)
            color = t("danger") if key == "stop_simulation" else (t("success") if key == "play_pause" else None)
            if key == "play_pause":
                self.play_btn = Button((bx, ctrl_y, sim_w, 26), text, font_size=10, color=color, callback=callbacks[key])
                self.elements.append(self.play_btn)
            else:
                self.elements.append(Button((bx, ctrl_y, sim_w, 26), text, font_size=10, color=color, callback=callbacks[key]))

        y = ctrl_y + 42

        # ── Settings ──
        self.elements.append(SectionHeader(cx, y, "BOARD", PW - 30, font_size=12))
        y += section_gap

        # Goal preset row
        settings_y = y
        goal_label = Label((PX, settings_y + 2), "Goal", font_size=10, color=t("subtext"), bold=True)
        self.elements.append(goal_label)
        gw = (PW - 56) // 4
        for i, (text, key) in enumerate([("Default", "default"), ("Spiral", "spiral"),
                                          ("Columns", "columns"), ("Custom", "custom")]):
            gx = PX + 52 + i * (gw + 3)
            if key == "custom":
                cb = lambda: callbacks['set_custom_goal']()
            else:
                cb = lambda k=key: callbacks['change_goal_preset'](k)
            b = ToggleButton((gx, settings_y, gw, 20), text, font_size=10, callback=cb)
            self.goal_buttons[key] = b
            self.elements.append(b)

        # Board size row
        size_y = settings_y + 25
        size_label = Label((PX, size_y + 2), "Size", font_size=10, color=t("subtext"), bold=True)
        self.elements.append(size_label)
        sw = (PW - 56) // 4
        for i, (text, val) in enumerate([("3x3", 3), ("4x4", 4), ("5x5", 5), ("8x8", 8)]):
            sx_pos = PX + 52 + i * (sw + 3)
            b = ToggleButton((sx_pos, size_y, sw, 20), text, font_size=10,
                             callback=lambda v=val: callbacks['change_size'](v))
            self.size_buttons[val] = b
            self.elements.append(b)

        # Sound + Export row
        extra_y = size_y + 27
        opt_w = (PW - 10) // 2
        self.sound_btn = ToggleButton((PX, extra_y, opt_w, 20), "Sound: On", font_size=10,
                                       callback=callbacks['toggle_sound'])
        self.elements.append(self.sound_btn)
        self.elements.append(Button((PX + opt_w + 10, extra_y, opt_w, 20), "Export Log", font_size=10,
                                       color=t("secondary"), callback=callbacks['export_log']))

        y = extra_y + 38

        # ── HISTORY (always visible) ──
        self.elements.append(SectionHeader(cx, y, "HISTORY", PW - 30, font_size=12))
        y += section_gap

        hw = (PW - 18) // 4
        self.elements.append(Button((PX, y, hw, 22), "Undo", font_size=10,
                                     color=t("primary"), callback=callbacks['undo']))
        self.elements.append(Button((PX + hw + 6, y, hw, 22), "Redo", font_size=10,
                                     color=t("primary"), callback=callbacks['redo']))
        self.elements.append(Button((PX + 2 * (hw + 6), y, hw, 22), "Save Game", font_size=10,
                                     color=t("success"), callback=callbacks['save_game']))
        self.elements.append(Button((PX + 3 * (hw + 6), y, hw, 22), "Load Game", font_size=10,
                                     color=t("primary"), callback=callbacks['load_game']))
        y += 42

        # ── Search log ──
        self.elements.append(SectionHeader(cx, y, "SEARCH LOG", PW - 30, font_size=12))
        y += section_gap

        self.log_rect = pygame.Rect(PX, y, PW, PANEL_RECT.bottom - y - 18)
        self.log_font = get_font(10)
        self.log_scroll = 0
        self.log_entries = []
        self.log_line_h = 13
        self.log_visible_lines = max(3, (self.log_rect.height - 12) // self.log_line_h)

    # ── Update Methods ──

    def update_fps(self, fps):
        self.fps_label.text = f"FPS: {int(fps)}"

    def show_notification(self, message, kind="info", duration=2.2):
        self.notification_text = str(message)
        self.notification_kind = kind
        self.notification_timer = duration

    def update_image_name(self, name):
        if name:
            display_name = name if len(name) < 38 else name[:35] + "..."
        else:
            display_name = "Digits"
        self.image_label.text = f"Image: {display_name}"

    def update_game_stats(self, elapsed_time_str, moves_count):
        self.game_time_val.text = elapsed_time_str
        self.game_moves_val.text = str(moves_count)

    def update_comparison(self, player_moves, optimal_moves):
        if optimal_moves is not None and optimal_moves > 0:
            pct = int((optimal_moves / player_moves) * 100) if player_moves > 0 else 0
            self.comparison_label.text = f"{optimal_moves} / {pct}%"
        else:
            self.comparison_label.text = "-"

    def update_high_score(self, high_score):
        if high_score:
            best_moves = high_score["best_moves"]
            best_time = high_score["best_time"]
            mins = int(best_time // 60)
            secs = int(best_time % 60)
            self.high_score_label.text = f"{best_moves} / {mins:02d}:{secs:02d}"
        else:
            self.high_score_label.text = "-"

    def update_simulation_stats(self, nodes_expanded, frontier_size, depth, h_val, f_val, duration_ms):
        self.nodes_label.text = f"Explored {nodes_expanded}"
        self.frontier_label.text = f"Frontier {frontier_size}"
        self.h_label.text = f"h {h_val}"
        self.f_label.text = f"f {f_val}"
        self.depth_label.text = f"g {depth}"
        self.duration_label.text = f"{duration_ms:.1f} ms"

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
        self.play_btn.base_color = t("danger") if is_playing else t("success")

    def update_sound_button(self, enabled):
        self.sound_btn.text = "Sound: On" if enabled else "Sound: Off"
        self.sound_btn.active = enabled

    def set_search_log(self, entries):
        self.log_entries = list(entries)
        max_scroll = max(0, len(self.log_entries) - self.log_visible_lines)
        self.log_scroll = max_scroll

    def draw_search_overlay(self, screen, explored_positions, frontier_positions, board_size):
        if not explored_positions and not frontier_positions:
            return

        tile_size = PUZZLE_SIZE // board_size
        overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)

        bw = board_size * tile_size
        start_x = (BOARD_SIZE - bw) // 2
        start_y = (BOARD_SIZE - bw) // 2

        for r in range(board_size):
            for c in range(board_size):
                rect = pygame.Rect(start_x + c * tile_size, start_y + r * tile_size, tile_size, tile_size)
                if (r, c) in explored_positions:
                    pygame.draw.rect(overlay, (255, 140, 50, 40), rect)
                elif (r, c) in frontier_positions:
                    pygame.draw.rect(overlay, (0, 200, 255, 55), rect)

        screen.blit(overlay, BOARD_RECT.topleft)
        self.legend_label.text = f"Explored: {len(explored_positions)}  Frontier: {len(frontier_positions)}"

    def handle_event(self, event):
        for element in self.elements:
            element.handle_event(event)
        # Log scrolling
        if event.type == pygame.MOUSEWHEEL:
            if self.log_rect.collidepoint(pygame.mouse.get_pos()):
                max_scroll = max(0, len(self.log_entries) - self.log_visible_lines)
                self.log_scroll = max(0, min(max_scroll, self.log_scroll - event.y * 3))

    def update(self, dt):
        for element in self.elements:
            element.update(dt)
        if self.notification_timer > 0:
            self.notification_timer = max(0.0, self.notification_timer - dt)

    def draw(self, screen):
        for element in self.elements:
            element.draw(screen)

        pygame.draw.rect(screen, (10, 12, 13), self.log_rect, border_radius=7)
        pygame.draw.rect(screen, t("border"), self.log_rect, 1, border_radius=7)

        old_clip = screen.get_clip()
        screen.set_clip(self.log_rect.inflate(-4, -4))

        if not self.log_entries:
            hint = self.log_font.render("Run a solver to stream search output", True, t("subtext"))
            screen.blit(hint, (self.log_rect.x + 10, self.log_rect.y + 10))
        else:
            start = self.log_scroll
            end = min(start + self.log_visible_lines, len(self.log_entries))
            for i in range(start, end):
                entry = self.log_entries[i]
                line_y = self.log_rect.y + 8 + (i - start) * self.log_line_h
                if "SOLVED" in entry:
                    color = t("success")
                elif "FAILED" in entry:
                    color = t("danger")
                elif entry.startswith("---"):
                    color = t("section_line")
                elif entry.startswith("["):
                    color = t("text")
                else:
                    color = t("subtext")
                surf = self.log_font.render(entry, True, color)
                screen.blit(surf, (self.log_rect.x + 10, line_y))

        screen.set_clip(old_clip)

        if self.notification_timer > 0 and self.notification_text:
            if self.notification_kind == "success":
                accent = t("success")
            elif self.notification_kind == "warning":
                accent = t("warning")
            elif self.notification_kind == "error":
                accent = t("danger")
            else:
                accent = t("primary")

            font = get_font(14, bold=True)
            text_surf = font.render(self.notification_text, True, t("text"))
            toast_w = min(PW, max(280, text_surf.get_width() + 44))
            toast_h = 42
            toast_rect = pygame.Rect(PANEL_RECT.right - toast_w - 20, PANEL_RECT.y + 16, toast_w, toast_h)

            pygame.draw.rect(screen, (8, 10, 11), toast_rect.move(0, 2), border_radius=8)
            pygame.draw.rect(screen, (24, 29, 30), toast_rect, border_radius=8)
            pygame.draw.rect(screen, accent, toast_rect, 1, border_radius=8)
            pygame.draw.rect(screen, accent, (toast_rect.x, toast_rect.y, 5, toast_rect.height), border_radius=4)
            screen.blit(text_surf, text_surf.get_rect(midleft=(toast_rect.x + 18, toast_rect.centery)))
