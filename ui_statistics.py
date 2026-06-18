import pygame
from ui_system import (Panel, Label, Button, ToggleButton, SectionHeader, CollapsibleSection, ProgressBar,
                       t, get_font, SCREEN_W, SCREEN_H)

# ─── Layout Constants ────────────────────────────────────────────────────────

MARGIN = 20
HEADER_H = 65

# Left column
BOARD_SIZE = 480
BOARD_X = MARGIN
BOARD_Y = HEADER_H + 10
BOARD_RECT = pygame.Rect(BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE)

PREVIEW_H = 100
PREVIEW_X = BOARD_X
PREVIEW_Y = BOARD_Y + BOARD_SIZE + 5
PREVIEW_RECT = pygame.Rect(PREVIEW_X, PREVIEW_Y, BOARD_SIZE, PREVIEW_H)

STATS_H = 60
STATS_X = BOARD_X
STATS_Y = PREVIEW_Y + PREVIEW_H + 8
STATS_RECT = pygame.Rect(STATS_X, STATS_Y, BOARD_SIZE, STATS_H)

# Right column
PANEL_X = BOARD_X + BOARD_SIZE + MARGIN
PANEL_Y = BOARD_Y
PANEL_W = SCREEN_W - PANEL_X - MARGIN
PANEL_H = STATS_Y + STATS_H + MARGIN - PANEL_Y
PANEL_RECT = pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)

PX = PANEL_X + 14
PY = PANEL_Y + 10
PW = PANEL_W - 28


class GameDashboard:
    """2-column layout: Board+Preview+Stats (left) | Controls (right)."""

    def __init__(self, screen_width, screen_height, callbacks):
        self.elements = []
        self.algo_children = []
        self.settings_children = []
        self.algo_buttons = {}
        self.speed_buttons = {}
        self.size_buttons = {}
        self.goal_buttons = {}

        cx = PANEL_X + PANEL_W // 2

        # ── Header ──
        self.elements.append(Label((SCREEN_W // 2, 22), "N-PUZZLE SEARCH SIMULATOR",
                                   font_size=28, bold=True, center=True))
        self.image_label = Label((SCREEN_W // 2, 52), "Image: [Digits]",
                                 font_size=13, color=t("subtext"), center=True)
        self.elements.append(self.image_label)

        # FPS counter
        self.fps_label = Label((SCREEN_W - 80, 28), "FPS: 60", font_size=11, color=t("subtext"))
        self.elements.append(self.fps_label)

        # ── Left: Board ──
        self.board_rect = BOARD_RECT
        self.elements.append(Panel(self.board_rect, radius=10))

        # ── Left: Image Preview ──
        self.preview_rect = PREVIEW_RECT
        self.elements.append(Panel(self.preview_rect, radius=8))
        self.preview_label = Label((self.preview_rect.centerx, self.preview_rect.centery),
                                   "[No image loaded]", font_size=12, color=t("subtext"), center=True)
        self.elements.append(self.preview_label)

        # ── Left: Stats Bar ──
        self.elements.append(Panel(STATS_RECT, radius=8))

        sx = STATS_X + 10
        sy = STATS_Y + 8

        self.nodes_label = Label((sx, sy), "Explored: 0", font_size=11, color=t("subtext"))
        self.elements.append(self.nodes_label)
        self.frontier_label = Label((sx + 140, sy), "Frontier: 0", font_size=11, color=t("subtext"))
        self.elements.append(self.frontier_label)
        self.h_label = Label((sx + 300, sy), "h=0", font_size=11, color=t("subtext"))
        self.elements.append(self.h_label)

        self.f_label = Label((sx, sy + 20), "f=0", font_size=11, color=t("subtext"))
        self.elements.append(self.f_label)
        self.depth_label = Label((sx + 80, sy + 20), "g=0", font_size=11, color=t("subtext"))
        self.elements.append(self.depth_label)
        self.duration_label = Label((sx + 160, sy + 20), "0.0ms", font_size=11, color=t("subtext"))
        self.elements.append(self.duration_label)

        # Legend
        self.legend_label = Label((sx + 280, sy + 20), "", font_size=10, color=t("subtext"))
        self.elements.append(self.legend_label)

        # ══════════════════════════════════════════════════════════════════
        # RIGHT PANEL — compact layout
        # ══════════════════════════════════════════════════════════════════
        y = PY
        ROW_H = 30   # standard row gap
        SEC_GAP = 4  # gap after section header

        # ── Image buttons ──
        btn_w = (PW - 6) // 2
        self.elements.append(Button((PX, y, btn_w, 26), "Add Image", font_size=11,
                                     color=t("primary"), callback=callbacks['insert_image']))
        self.elements.append(Button((PX + btn_w + 6, y, btn_w, 26), "Play Again", font_size=11,
                                     color=t("danger"), callback=callbacks['reset_game']))
        y += ROW_H

        # ── Game Status ──
        self.elements.append(Label((PX, y), "Time:", font_size=11, color=t("subtext")))
        self.game_time_val = Label((PX + 45, y), "00:00", font_size=13, bold=True)
        self.elements.append(self.game_time_val)
        self.elements.append(Label((PX + 130, y), "Moves:", font_size=11, color=t("subtext")))
        self.game_moves_val = Label((PX + 185, y), "0", font_size=13, bold=True)
        self.elements.append(self.game_moves_val)
        self.comparison_label = Label((PX + 290, y), "", font_size=11, color=t("secondary"))
        self.elements.append(self.comparison_label)
        y += 20

        self.high_score_label = Label((PX, y), "", font_size=13, bold=True, color=t("success"))
        self.elements.append(self.high_score_label)
        y += 18

        self.progress_bar = ProgressBar((PX, y, PW, 12))
        self.elements.append(self.progress_bar)
        y += 20

        # ── ALGORITHMS (collapsible) ──
        self.algo_section = CollapsibleSection(cx, y, "ALGORITHMS", PW - 40, font_size=12)
        self.elements.append(self.algo_section)
        y += 18 + SEC_GAP

        # Algo buttons: 5 in 2 cols → 3 rows
        bw2 = (PW - 6) // 2
        algos = [
            ("Bi-A*", "bi_astar"), ("IDA*", "idastar"),
            ("A* Manhattan", "astar_manhattan"), ("A* Misplaced", "astar_misplaced"),
            ("GBFS", "gbfs"),
        ]
        algo_y = y
        for i, (text, key) in enumerate(algos):
            col = i % 2
            row = i // 2
            bx = PX + col * (bw2 + 6)
            by = algo_y + row * 28
            b = ToggleButton((bx, by, bw2, 24), text, font_size=11,
                             callback=lambda k=key: callbacks['select_algorithm'](k))
            self.algo_buttons[key] = b
            self.algo_children.append(b)

        # Speed row
        speed_y = algo_y + 86
        spd_label = Label((PX, speed_y + 1), "Speed:", font_size=10, color=t("subtext"))
        self.algo_children.append(spd_label)
        speed_w = (PW - 55) // 4
        for i, (text, key) in enumerate([("Slow", "slow"), ("Med", "medium"), ("Fast", "fast"), ("Max", "max")]):
            bx = PX + 50 + i * (speed_w + 3)
            b = ToggleButton((bx, speed_y, speed_w, 20), text, font_size=10,
                             callback=lambda k=key: callbacks['select_speed'](k))
            self.speed_buttons[key] = b
            self.algo_children.append(b)

        # Compare + Play controls row
        ctrl_y = speed_y + 26
        self.algo_children.append(
            Button((PX, ctrl_y, bw2, 24), "Compare All",
                   font_size=10, color=t("secondary"), callback=callbacks['compare_solvers'])
        )
        sim_btns = [("<", 'step_backward'), ("Play", 'play_pause'), (">", 'step_forward'), ("Stop", 'stop_simulation')]
        sim_w = (bw2 - 18) // 4
        for i, (text, key) in enumerate(sim_btns):
            bx = PX + bw2 + 6 + i * (sim_w + 6)
            color = t("danger") if key == "stop_simulation" else (t("success") if key == "play_pause" else None)
            if key == "play_pause":
                self.play_btn = Button((bx, ctrl_y, sim_w, 24), text, font_size=10, color=color, callback=callbacks[key])
                self.algo_children.append(self.play_btn)
            else:
                self.algo_children.append(Button((bx, ctrl_y, sim_w, 24), text, font_size=10, color=color, callback=callbacks[key]))

        algo_children_bottom = ctrl_y + ROW_H
        y = algo_children_bottom

        # ── SETTINGS (collapsible) ──
        self.settings_section = CollapsibleSection(cx, y, "SETTINGS", PW - 40, font_size=12)
        self.elements.append(self.settings_section)
        y += 18 + SEC_GAP

        # Goal preset row
        settings_y = y
        goal_label = Label((PX, settings_y + 1), "Goal:", font_size=10, color=t("subtext"))
        self.settings_children.append(goal_label)
        gw = (PW - 40) // 4
        for i, (text, key) in enumerate([("Default", "default"), ("Spiral", "spiral"),
                                          ("Columns", "columns"), ("Custom", "custom")]):
            gx = PX + 38 + i * (gw + 3)
            if key == "custom":
                cb = lambda: callbacks['set_custom_goal']()
            else:
                cb = lambda k=key: callbacks['change_goal_preset'](k)
            b = ToggleButton((gx, settings_y, gw, 20), text, font_size=10, callback=cb)
            self.goal_buttons[key] = b
            self.settings_children.append(b)

        # Board size row
        size_y = settings_y + 24
        size_label = Label((PX, size_y + 1), "Size:", font_size=10, color=t("subtext"))
        self.settings_children.append(size_label)
        sw = (PW - 40) // 4
        for i, (text, val) in enumerate([("3x3", 3), ("4x4", 4), ("5x5", 5), ("8x8", 8)]):
            sx_pos = PX + 38 + i * (sw + 3)
            b = ToggleButton((sx_pos, size_y, sw, 20), text, font_size=10,
                             callback=lambda v=val: callbacks['change_size'](v))
            self.size_buttons[val] = b
            self.settings_children.append(b)

        # Sound + Export row
        extra_y = size_y + 24
        opt_w = (PW - 6) // 2
        self.sound_btn = ToggleButton((PX, extra_y, opt_w, 20), "Sound: On", font_size=10,
                                       callback=callbacks['toggle_sound'])
        self.settings_children.append(self.sound_btn)
        self.settings_children.append(Button((PX + opt_w + 6, extra_y, opt_w, 20), "Export Log", font_size=10,
                                       color=t("secondary"), callback=callbacks['export_log']))

        settings_children_bottom = extra_y + ROW_H
        y = settings_children_bottom

        # ── SEARCH LOG (collapsible) ──
        self.log_section = CollapsibleSection(cx, y, "SEARCH LOG", PW - 40, font_size=12)
        self.elements.append(self.log_section)
        y += 18 + SEC_GAP

        self.log_rect = pygame.Rect(PX - 4, y, PW + 8, 120)
        self.log_font = get_font(10)
        self.log_scroll = 0
        self.log_entries = []
        self.log_line_h = 12
        self.log_visible_lines = 9
        y += 126

        # ── HISTORY (always visible) ──
        SectionHeader(cx, y, "HISTORY", PW - 40)
        y += 18

        hw = (PW - 12) // 3
        self.elements.append(Button((PX, y, hw, 22), "Undo", font_size=10,
                                     color=t("primary"), callback=callbacks['undo']))
        self.elements.append(Button((PX + hw + 6, y, hw, 22), "Redo", font_size=10,
                                     color=t("primary"), callback=callbacks['redo']))
        self.elements.append(Button((PX + 2 * (hw + 6), y, hw, 22), "Save Game", font_size=10,
                                     color=t("success"), callback=callbacks['save_game']))
        y += 26

        self.elements.append(Button((PX, y, hw, 22), "Load Game", font_size=10,
                                     color=t("primary"), callback=callbacks['load_game']))

        # ── Footer: Shortcuts (anchored to panel bottom) ──
        hint_y = PANEL_RECT.bottom - 30
        self.elements.append(Label((cx, hint_y), "Arrows: Move | Ctrl+S: Save | Ctrl+L: Load",
                                   font_size=10, color=t("subtext"), center=True))

    # ── Update Methods ──

    def update_fps(self, fps):
        self.fps_label.text = f"FPS: {int(fps)}"

    def update_image_name(self, name):
        display_name = name if len(name) < 30 else name[:27] + "..."
        self.image_label.text = f"Image: {display_name}"

    def update_game_stats(self, elapsed_time_str, moves_count):
        self.game_time_val.text = elapsed_time_str
        self.game_moves_val.text = str(moves_count)

    def update_comparison(self, player_moves, optimal_moves):
        if optimal_moves is not None and optimal_moves > 0:
            pct = int((optimal_moves / player_moves) * 100) if player_moves > 0 else 0
            self.comparison_label.text = f"Optimal: {optimal_moves} moves ({pct}%)"
        else:
            self.comparison_label.text = ""

    def update_high_score(self, high_score):
        if high_score:
            best_moves = high_score["best_moves"]
            best_time = high_score["best_time"]
            mins = int(best_time // 60)
            secs = int(best_time % 60)
            self.high_score_label.text = f"BEST: {best_moves} moves ({mins:02d}:{secs:02d})"
        else:
            self.high_score_label.text = ""

    def update_simulation_stats(self, nodes_expanded, frontier_size, depth, h_val, f_val, duration_ms):
        self.nodes_label.text = f"Explored: {nodes_expanded}"
        self.frontier_label.text = f"Frontier: {frontier_size}"
        self.h_label.text = f"h={h_val}"
        self.f_label.text = f"f={f_val}"
        self.depth_label.text = f"g={depth}"
        self.duration_label.text = f"{duration_ms:.1f}ms"

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

        tile_size = BOARD_SIZE // board_size
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
        if self.algo_section.expanded:
            for element in self.algo_children:
                element.handle_event(event)
        if self.settings_section.expanded:
            for element in self.settings_children:
                element.handle_event(event)
        # Log scrolling
        if event.type == pygame.MOUSEWHEEL:
            if self.log_rect.collidepoint(pygame.mouse.get_pos()):
                max_scroll = max(0, len(self.log_entries) - self.log_visible_lines)
                self.log_scroll = max(0, min(max_scroll, self.log_scroll - event.y * 3))

    def update(self, dt):
        for element in self.elements:
            element.update(dt)
        if self.algo_section.expanded:
            for element in self.algo_children:
                element.update(dt)
        if self.settings_section.expanded:
            for element in self.settings_children:
                element.update(dt)

    def draw(self, screen):
        for element in self.elements:
            element.draw(screen)
        if self.algo_section.expanded:
            for element in self.algo_children:
                element.draw(screen)
        if self.settings_section.expanded:
            for element in self.settings_children:
                element.draw(screen)

        # Draw log panel (only when expanded)
        if self.log_section.expanded:
            log_label = self.log_font.render("SEARCH LOG", True, t("secondary"))
            screen.blit(log_label, (PX, self.log_section.y))
            pygame.draw.line(screen, t("section_line"),
                             (PX, self.log_section.y + 12),
                             (PX + PW, self.log_section.y + 12), 1)

            log_bg = pygame.Rect(self.log_rect.x, self.log_rect.y + 16,
                                 self.log_rect.w, self.log_rect.h - 16)
            pygame.draw.rect(screen, (10, 10, 20), log_bg, border_radius=6)
            pygame.draw.rect(screen, t("border"), log_bg, 1, border_radius=6)

            old_clip = screen.get_clip()
            screen.set_clip(log_bg.inflate(-2, -2))

            if not self.log_entries:
                hint = self.log_font.render("Run an algorithm to see log", True, t("subtext"))
                screen.blit(hint, (PX + 8, log_bg.centery - 6))
            else:
                start = self.log_scroll
                end = min(start + self.log_visible_lines, len(self.log_entries))
                for i in range(start, end):
                    entry = self.log_entries[i]
                    line_y = log_bg.y + 4 + (i - start) * self.log_line_h
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
                    screen.blit(surf, (PX + 6, line_y))

            screen.set_clip(old_clip)
