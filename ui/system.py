import pygame

# ─── Theme System ────────────────────────────────────────────────────────────

DARK_COLORS = {
    "bg": (9, 11, 13),
    "panel_bg": (18, 21, 24),
    "text": (238, 241, 236),
    "subtext": (142, 151, 148),
    "border": (49, 56, 58),
    "primary": (86, 230, 185),
    "secondary": (255, 184, 108),
    "danger": (246, 97, 97),
    "success": (91, 214, 132),
    "warning": (255, 211, 112),
    "btn_default": (29, 34, 37),
    "btn_hover": (42, 49, 52),
    "grad1": (7, 9, 10),
    "grad2": (22, 25, 26),
    "panel_alpha": (18, 21, 24, 238),
    "tile_bg": (31, 37, 40),
    "section_line": (61, 69, 68),
}

LIGHT_COLORS = {
    "bg": (243, 244, 240),
    "panel_bg": (255, 255, 250),
    "text": (29, 34, 35),
    "subtext": (102, 111, 108),
    "border": (204, 210, 205),
    "primary": (0, 143, 111),
    "secondary": (196, 109, 40),
    "danger": (211, 63, 73),
    "success": (37, 151, 82),
    "warning": (205, 142, 34),
    "btn_default": (232, 235, 228),
    "btn_hover": (218, 224, 216),
    "grad1": (248, 249, 245),
    "grad2": (230, 234, 227),
    "panel_alpha": (255, 255, 250, 242),
    "tile_bg": (222, 228, 221),
    "section_line": (186, 196, 188),
}

_current_theme = "dark"
_theme_colors = DARK_COLORS

def get_theme():
    return _current_theme

def set_theme(name):
    global _current_theme, _theme_colors, _bg_surface
    _current_theme = name
    _theme_colors = DARK_COLORS if name == "dark" else LIGHT_COLORS
    _bg_surface = None

def t(key):
    return _theme_colors[key]

# Legacy constants
BG_COLOR = t("bg")
PANEL_BG = t("panel_bg")
TEXT_COLOR = t("text")
SUBTEXT_COLOR = t("subtext")
BORDER_COLOR = t("border")
PRIMARY_ACCENT = t("primary")
SECONDARY_ACCENT = t("secondary")
DANGER_ACCENT = t("danger")
SUCCESS_ACCENT = t("success")
BTN_DEFAULT = t("btn_default")
BTN_HOVER = t("btn_hover")

_bg_surface = None

# ─── Screen Helpers ──────────────────────────────────────────────────────────

SCREEN_W, SCREEN_H = 1366, 768

def draw_gradient_background(screen):
    global _bg_surface
    width, height = screen.get_size()
    if _bg_surface is None or _bg_surface.get_size() != (width, height):
        _bg_surface = pygame.Surface((width, height))
        c1, c2 = t("grad1"), t("grad2")
        for y in range(height):
            f = y / height
            r = int(c1[0] + (c2[0] - c1[0]) * f)
            g = int(c1[1] + (c2[1] - c1[1]) * f)
            b = int(c1[2] + (c2[2] - c1[2]) * f)
            pygame.draw.line(_bg_surface, (r, g, b), (0, y), (width, y))
        grid_color = (255, 255, 255, 9) if get_theme() == "dark" else (0, 0, 0, 8)
        for x in range(0, width, 40):
            pygame.draw.line(_bg_surface, grid_color, (x, 0), (x, height))
        for y in range(0, height, 40):
            pygame.draw.line(_bg_surface, grid_color, (0, y), (width, y))
    screen.blit(_bg_surface, (0, 0))

def get_font(size, bold=False):
    return pygame.font.SysFont(['segoe ui', 'tahoma', 'arial', 'sans-serif'], size, bold=bold)

def readable_text_color(color):
    luminance = (0.299 * color[0]) + (0.587 * color[1]) + (0.114 * color[2])
    return (8, 12, 13) if luminance > 145 else t("text")

# ─── Widgets ─────────────────────────────────────────────────────────────────

class Panel:
    """Cached flat panel with a restrained shadow."""
    def __init__(self, rect, radius=12):
        self.rect = pygame.Rect(rect)
        self.radius = radius
        self._cache = None
        self._cache_size = None

    def handle_event(self, event): pass
    def update(self, dt): pass

    def draw(self, screen):
        size = (self.rect.width, self.rect.height)
        if self._cache is None or self._cache_size != size:
            self._cache = pygame.Surface(size, pygame.SRCALPHA)
            shadow = pygame.Rect(2, 3, size[0] - 4, size[1] - 4)
            pygame.draw.rect(self._cache, (0, 0, 0, 70), shadow, border_radius=self.radius)
            body = pygame.Rect(0, 0, size[0] - 2, size[1] - 2)
            pygame.draw.rect(self._cache, t("panel_alpha"), body, border_radius=self.radius)
            pygame.draw.rect(self._cache, t("border"), body, 1, border_radius=self.radius)
            pygame.draw.line(self._cache, (255, 255, 255, 20), (10, 1), (size[0] - 12, 1), 1)
            self._cache_size = size
        screen.blit(self._cache, self.rect.topleft)


class Label:
    def __init__(self, pos, text, font_size=14, color=None, bold=False, center=False):
        self.pos = pos
        self.text = str(text)
        self.font = get_font(font_size, bold)
        self.color = color if color else t("text")
        self.center = center

    def handle_event(self, event): pass
    def update(self, dt): pass

    def set_text(self, text):
        self.text = str(text)

    def draw(self, screen):
        surf = self.font.render(self.text, True, self.color)
        rect = surf.get_rect(center=self.pos) if self.center else surf.get_rect(topleft=self.pos)
        screen.blit(surf, rect)


class Button:
    """Button with scale-on-hover animation."""
    def __init__(self, rect, text, font_size=14, callback=None, color=None, radius=8):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = get_font(font_size, bold=True)
        self.callback = callback
        self.is_hovered = False
        self.is_pressed = False
        self.base_color = color if color else t("btn_default")
        self.hover_color = t("btn_hover")
        self.radius = radius
        self.current_color = list(self.base_color)
        self.scale = 1.0
        self.target_scale = 1.0

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.is_pressed = True
                if self.callback:
                    self.callback()
        elif event.type == pygame.MOUSEBUTTONUP:
            self.is_pressed = False

    def update(self, dt):
        target = self.hover_color if self.is_hovered else self.base_color
        rate = min(1.0, 12.0 * dt)
        for i in range(3):
            self.current_color[i] += (target[i] - self.current_color[i]) * rate
        self.target_scale = 0.98 if self.is_pressed else (1.02 if self.is_hovered else 1.0)
        self.scale += (self.target_scale - self.scale) * min(1.0, 18.0 * dt)

    def draw(self, screen):
        color = (int(self.current_color[0]), int(self.current_color[1]), int(self.current_color[2]))
        w, h = int(self.rect.width * self.scale), int(self.rect.height * self.scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2
        draw_rect = pygame.Rect(x, y, w, h)

        shadow_rect = draw_rect.move(0, 2)
        pygame.draw.rect(screen, (0, 0, 0, 45), shadow_rect, border_radius=self.radius)
        pygame.draw.rect(screen, color, draw_rect, border_radius=self.radius)
        border = t("primary") if self.is_hovered else t("border")
        pygame.draw.rect(screen, border, draw_rect, 1, border_radius=self.radius)

        text_color = readable_text_color(color)
        surf = self.font.render(self.text, True, text_color)
        screen.blit(surf, surf.get_rect(center=draw_rect.center))


class ToggleButton(Button):
    def __init__(self, rect, text, font_size=12, callback=None, color=None, radius=8, active=False):
        super().__init__(rect, text, font_size, callback, color, radius)
        self.active = active
        self.active_color = t("primary")

    def update(self, dt):
        if self.active:
            target = self.active_color
        elif self.is_hovered:
            target = self.hover_color
        else:
            target = self.base_color
        rate = min(1.0, 12.0 * dt)
        for i in range(3):
            self.current_color[i] += (target[i] - self.current_color[i]) * rate
        self.target_scale = 0.98 if self.is_pressed else (1.02 if self.is_hovered else 1.0)
        self.scale += (self.target_scale - self.scale) * min(1.0, 18.0 * dt)

    def draw(self, screen):
        color = (int(self.current_color[0]), int(self.current_color[1]), int(self.current_color[2]))
        w, h = int(self.rect.width * self.scale), int(self.rect.height * self.scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2
        draw_rect = pygame.Rect(x, y, w, h)

        shadow_rect = draw_rect.move(0, 2)
        pygame.draw.rect(screen, (0, 0, 0, 45), shadow_rect, border_radius=self.radius)
        pygame.draw.rect(screen, color, draw_rect, border_radius=self.radius)
        border = t("primary") if (self.active or self.is_hovered) else t("border")
        pygame.draw.rect(screen, border, draw_rect, 1, border_radius=self.radius)

        text_color = readable_text_color(color)
        surf = self.font.render(self.text, True, text_color)
        screen.blit(surf, surf.get_rect(center=draw_rect.center))


class SectionHeader:
    """Section title with decorative underline."""
    def __init__(self, center_x, y, text, width=120, font_size=12):
        self.center_x = center_x
        self.y = y
        self.text = text
        self.width = width
        self.font = get_font(font_size, bold=True)

    def handle_event(self, event): pass
    def update(self, dt): pass

    def draw(self, screen):
        surf = self.font.render(self.text, True, t("secondary"))
        rect = surf.get_rect(center=(self.center_x, self.y))
        screen.blit(surf, rect)

        line_y = self.y + 12
        half = self.width // 2
        color = t("section_line")
        pygame.draw.line(screen, color, (self.center_x - half, line_y), (self.center_x + half, line_y), 1)


class CollapsibleSection:
    """Clickable header that toggles visibility of child elements."""
    def __init__(self, center_x, y, text, width=120, font_size=12):
        self.center_x = center_x
        self.y = y
        self.text = text
        self.width = width
        self.font = get_font(font_size, bold=True)
        self.expanded = False
        self.hit_rect = pygame.Rect(center_x - width // 2, y - 10, width, 26)

    def toggle(self):
        self.expanded = not self.expanded

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hit_rect.collidepoint(event.pos):
                self.toggle()

    def update(self, dt): pass

    def draw(self, screen):
        arrow = "v" if self.expanded else ">"
        label = f"{self.text} {arrow}"
        surf = self.font.render(label, True, t("primary") if self.expanded else t("secondary"))
        rect = surf.get_rect(center=(self.center_x, self.y))
        screen.blit(surf, rect)

        line_y = self.y + 12
        half = self.width // 2
        color = t("section_line")
        pygame.draw.line(screen, color, (self.center_x - half, line_y), (self.center_x + half, line_y), 1)


class Tile:
    def __init__(self, rect, value, index, color=None, callback=None, radius=8):
        self.value = value
        self.index = index
        self.font = get_font(28, bold=True)
        self.callback = callback
        self.image = None
        self.radius = radius
        self.curr_x = None
        self.curr_y = None
        self.target_x = None
        self.target_y = None
        self.width = 0
        self.height = 0
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.is_dragging = False

    def set_target(self, rect):
        self.target_x, self.target_y, self.width, self.height = rect
        if self.curr_x is None:
            self.curr_x = self.target_x
            self.curr_y = self.target_y

    def handle_event(self, event): pass

    def update(self, dt):
        if not self.is_dragging and self.curr_x is not None and self.target_x is not None:
            rate = min(1.0, 18.0 * dt)
            self.curr_x += (self.target_x - self.curr_x) * rate
            self.curr_y += (self.target_y - self.curr_y) * rate
            if abs(self.target_x - self.curr_x) < 0.5:
                self.curr_x = self.target_x
            if abs(self.target_y - self.curr_y) < 0.5:
                self.curr_y = self.target_y

    def draw(self, screen):
        if self.curr_x is None:
            return
        draw_rect = pygame.Rect(self.curr_x + self.drag_offset_x, self.curr_y + self.drag_offset_y, self.width, self.height)

        if self.image:
            scaled = pygame.transform.smoothscale(self.image, (self.width, self.height))
            screen.blit(scaled, draw_rect)
            pygame.draw.rect(screen, (0, 0, 0, 55), draw_rect.move(0, 2), 1, border_radius=self.radius)
            pygame.draw.rect(screen, (255, 255, 255, 46), draw_rect, 1, border_radius=self.radius)
        else:
            pygame.draw.rect(screen, (0, 0, 0, 85), draw_rect.move(0, 3), border_radius=self.radius)
            pygame.draw.rect(screen, t("tile_bg"), draw_rect, border_radius=self.radius)
            inner = draw_rect.inflate(-8, -8)
            pygame.draw.rect(screen, (255, 255, 255, 8), inner, border_radius=max(2, self.radius - 3))
            pygame.draw.rect(screen, t("border"), draw_rect, 1, border_radius=self.radius)
            surf = self.font.render(str(self.value), True, t("primary"))
            screen.blit(surf, surf.get_rect(center=draw_rect.center))


class ProgressBar:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.pct = 0
        self.correct_str = "0/0"

    def handle_event(self, event): pass
    def update(self, dt): pass

    def update_pct(self, pct, correct, total):
        self.pct = pct
        self.correct_str = f"{correct}/{total}"

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 0, 0, 60), self.rect.move(0, 1), border_radius=5)
        pygame.draw.rect(screen, t("btn_default"), self.rect, border_radius=5)
        pygame.draw.rect(screen, t("border"), self.rect, 1, border_radius=5)

        fill_w = int(self.rect.width * (self.pct / 100.0))
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            pygame.draw.rect(screen, t("success"), fill_rect, border_radius=5)

        font = get_font(10, bold=True)
        txt = f"{self.pct}%  ({self.correct_str})"
        surf = font.render(txt, True, t("text"))
        screen.blit(surf, surf.get_rect(center=self.rect.center))


class Modal:
    def __init__(self, message, btn1_text, btn1_cb, btn2_text, btn2_cb):
        self.overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.overlay.fill((4, 6, 7, 222))
        self.rect = pygame.Rect(SCREEN_W // 2 - 260, SCREEN_H // 2 - 140, 520, 280)
        self.panel = Panel(self.rect, radius=14)
        self.kicker = Label((self.rect.centerx, self.rect.y + 54), "SESSION COMPLETE", font_size=12,
                            color=t("secondary"), bold=True, center=True)
        self.title = Label((self.rect.centerx, self.rect.y + 96), message, font_size=24, bold=True, center=True)
        btn_y = self.rect.y + 184
        self.btn1 = Button((self.rect.centerx - 178, btn_y, 166, 42), btn1_text, font_size=13,
                           color=t("success"), callback=btn1_cb)
        self.btn2 = Button((self.rect.centerx + 12, btn_y, 166, 42), btn2_text, font_size=13,
                           color=t("danger"), callback=btn2_cb)

    def handle_event(self, event):
        self.btn1.handle_event(event)
        self.btn2.handle_event(event)

    def update(self, dt):
        self.btn1.update(dt)
        self.btn2.update(dt)

    def draw(self, screen):
        screen.blit(self.overlay, (0, 0))
        self.panel.draw(screen)
        self.kicker.draw(screen)
        self.title.draw(screen)
        self.btn1.draw(screen)
        self.btn2.draw(screen)


class ComparisonModal:
    def __init__(self, results, close_cb):
        self.overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.overlay.fill((4, 6, 7, 226))
        self.rect = pygame.Rect(SCREEN_W // 2 - 410, SCREEN_H // 2 - 220, 820, 440)
        self.panel = Panel(self.rect, radius=14)
        self.title = Label((self.rect.centerx, self.rect.y + 36), "ALGORITHM COMPARISON", font_size=22, bold=True, center=True)
        self.results = results
        self.close_btn = Button((self.rect.centerx - 70, self.rect.bottom - 58, 140, 38), "Close", font_size=14, color=t("danger"), callback=close_cb)

    def handle_event(self, event):
        self.close_btn.handle_event(event)

    def update(self, dt):
        self.close_btn.update(dt)

    def draw(self, screen):
        screen.blit(self.overlay, (0, 0))
        self.panel.draw(screen)
        self.title.draw(screen)
        self.close_btn.draw(screen)

        headers = ["Algorithm", "Nodes", "Moves", "Time (ms)"]
        col_x = [self.rect.x + 54, self.rect.x + 360, self.rect.x + 535, self.rect.x + 670]
        y_start = self.rect.y + 85

        font_h = get_font(15, bold=True)
        for h, x in zip(headers, col_x):
            screen.blit(font_h.render(h, True, t("secondary")), (x, y_start))
        pygame.draw.line(screen, t("border"), (self.rect.x + 40, y_start + 28), (self.rect.right - 40, y_start + 28), 1)

        y_row = y_start + 42
        font_r = get_font(14)
        for res in self.results:
            color = (78, 91, 88) if res["moves"] == "N/A" or res["nodes"] == "10,000+" else (18, 24, 24)
            row_rect = pygame.Rect(self.rect.x + 40, y_row - 8, self.rect.width - 80, 31)
            pygame.draw.rect(screen, (226, 239, 232), row_rect, border_radius=6)
            pygame.draw.rect(screen, t("border"), row_rect, 1, border_radius=6)
            screen.blit(font_r.render(res["name"], True, color), (col_x[0], y_row))
            screen.blit(font_r.render(res["nodes"], True, color), (col_x[1], y_row))
            screen.blit(font_r.render(res["moves"], True, color), (col_x[2], y_row))
            screen.blit(font_r.render(res["time"], True, color), (col_x[3], y_row))
            y_row += 42
