import pygame

# Modern Premium Dark Theme Colors
BG_COLOR = (12, 12, 24)           # Deep cosmic indigo
PANEL_BG = (20, 20, 35)           # Dark indigo glass base
TEXT_COLOR = (240, 240, 255)      # High Emphasis Text
SUBTEXT_COLOR = (140, 140, 170)    # Muted Indigo-grey Text
BORDER_COLOR = (60, 60, 90)       # Sleek border line

# Accent Colors
PRIMARY_ACCENT = (0, 229, 255)    # Neon Cyan
SECONDARY_ACCENT = (162, 90, 255) # Electric Purple
DANGER_ACCENT = (239, 72, 120)    # Crimson Pink
SUCCESS_ACCENT = (16, 185, 129)   # Emerald Green
BTN_DEFAULT = (35, 35, 60)        # Button Surface
BTN_HOVER = (55, 55, 85)          # Button Hover

_bg_surface = None

def draw_gradient_background(screen):
    """Draws and caches a premium cosmic gradient background."""
    global _bg_surface
    width, height = screen.get_size()
    if _bg_surface is None or _bg_surface.get_size() != (width, height):
        _bg_surface = pygame.Surface((width, height))
        color1 = (10, 10, 22)  # Cosmic black
        color2 = (28, 22, 50)  # Twilight violet
        for y in range(height):
            factor = y / height
            r = int(color1[0] + (color2[0] - color1[0]) * factor)
            g = int(color1[1] + (color2[1] - color1[1]) * factor)
            b = int(color1[2] + (color2[2] - color1[2]) * factor)
            pygame.draw.line(_bg_surface, (r, g, b), (0, y), (width, y))
    screen.blit(_bg_surface, (0, 0))

def get_font(size, bold=False):
    """Returns a system font with the given size and weight."""
    font_priority = ['segoe ui', 'tahoma', 'arial', 'sans-serif']
    return pygame.font.SysFont(font_priority, size, bold=bold)

class Panel:
    """A glassmorphic container with rounded corners and a thin glow border."""
    def __init__(self, rect, radius=15):
        self.rect = pygame.Rect(rect)
        self.radius = radius
        
    def handle_event(self, event): pass
    def update(self, dt): pass
        
    def draw(self, screen):
        surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, (20, 20, 35, 195), (0, 0, self.rect.width, self.rect.height), border_radius=self.radius)
        screen.blit(surf, self.rect.topleft)
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 1, border_radius=self.radius)

class Label:
    """A text element that can be centered or topleft-aligned."""
    def __init__(self, pos, text, font_size=18, color=TEXT_COLOR, bold=False, center=False):
        self.pos = pos
        self.text = str(text)
        self.font = get_font(font_size, bold)
        self.color = color
        self.center = center
        
    def handle_event(self, event): pass
    def update(self, dt): pass
        
    def draw(self, screen):
        text_surf = self.font.render(self.text, True, self.color)
        text_rect = text_surf.get_rect()
        if self.center:
            text_rect.center = self.pos
        else:
            text_rect.topleft = self.pos
        screen.blit(text_surf, text_rect)

class Button:
    """A clickable button with smooth hover fade effects."""
    def __init__(self, rect, text, font_size=18, callback=None, color=None, radius=12):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = get_font(font_size, bold=True)
        self.callback = callback
        self.is_hovered = False
        self.base_color = color if color else BTN_DEFAULT
        self.hover_color = BTN_HOVER
        self.radius = radius
        self.current_color = list(self.base_color)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                if self.callback:
                    self.callback()
                    
    def update(self, dt):
        target = self.hover_color if self.is_hovered else self.base_color
        rate = min(1.0, 15.0 * dt)
        for i in range(3):
            self.current_color[i] += (target[i] - self.current_color[i]) * rate
        
    def draw(self, screen):
        color = (int(self.current_color[0]), int(self.current_color[1]), int(self.current_color[2]))
        pygame.draw.rect(screen, color, self.rect, border_radius=self.radius)
        
        border = PRIMARY_ACCENT if self.is_hovered else BORDER_COLOR
        pygame.draw.rect(screen, border, self.rect, 1, border_radius=self.radius)
        
        text_surf = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

class ToggleButton(Button):
    """A button that supports an active/selected state with smooth transitions."""
    def __init__(self, rect, text, font_size=16, callback=None, color=None, radius=10, active=False):
        super().__init__(rect, text, font_size, callback, color, radius)
        self.active = active
        self.active_color = PRIMARY_ACCENT
        
    def update(self, dt):
        target = self.active_color if self.active else (self.hover_color if self.is_hovered else self.base_color)
        rate = min(1.0, 15.0 * dt)
        for i in range(3):
            self.current_color[i] += (target[i] - self.current_color[i]) * rate
        
    def draw(self, screen):
        color = (int(self.current_color[0]), int(self.current_color[1]), int(self.current_color[2]))
        pygame.draw.rect(screen, color, self.rect, border_radius=self.radius)
        
        border = PRIMARY_ACCENT if (self.active or self.is_hovered) else BORDER_COLOR
        pygame.draw.rect(screen, border, self.rect, 1, border_radius=self.radius)
        
        text_color = (10, 10, 20) if self.active else TEXT_COLOR
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

class Tile:
    """Class to manage individual puzzle pieces with sliding transitions."""
    def __init__(self, rect, value, index, color=None, callback=None, radius=8):
        self.value = value             # Tile value (1-N)
        self.index = index             # Current grid index
        self.font = get_font(32, bold=True)
        self.callback = callback
        self.image = None              # Holds the sub-image surface
        self.radius = radius
        
        # Slide animation positions
        self.curr_x = None
        self.curr_y = None
        self.target_x = None
        self.target_y = None
        self.width = 0
        self.height = 0
        
        # Drag offset
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.is_dragging = False
        
    def set_target(self, rect):
        """Set the target pixel coordinates for the tile."""
        self.target_x, self.target_y, self.width, self.height = rect
        if self.curr_x is None:
            self.curr_x = self.target_x
            self.curr_y = self.target_y
            
    def handle_event(self, event): pass
                    
    def update(self, dt):
        """Smoothly lerp current positions towards targets."""
        if not self.is_dragging and self.curr_x is not None and self.target_x is not None:
            lerp_factor = min(1.0, 18.0 * dt)
            self.curr_x += (self.target_x - self.curr_x) * lerp_factor
            self.curr_y += (self.target_y - self.curr_y) * lerp_factor
            
            if abs(self.target_x - self.curr_x) < 0.5:
                self.curr_x = self.target_x
            if abs(self.target_y - self.curr_y) < 0.5:
                self.curr_y = self.target_y
        
    def draw(self, screen):
        if self.curr_x is None:
            return
        draw_rect = pygame.Rect(self.curr_x + self.drag_offset_x, self.curr_y + self.drag_offset_y, self.width, self.height)
        
        if self.image:
            scaled_img = pygame.transform.smoothscale(self.image, (self.width, self.height))
            screen.blit(scaled_img, draw_rect)
            pygame.draw.rect(screen, (255, 255, 255, 25), draw_rect, 1, border_radius=self.radius)
        else:
            pygame.draw.rect(screen, (32, 32, 55), draw_rect, border_radius=self.radius)
            pygame.draw.rect(screen, BORDER_COLOR, draw_rect, 1, border_radius=self.radius)
            
            text_surf = self.font.render(str(self.value), True, PRIMARY_ACCENT)
            text_rect = text_surf.get_rect(center=draw_rect.center)
            screen.blit(text_surf, text_rect)

class ProgressBar:
    """A premium progress bar showing matching tiles percentage."""
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.pct = 0
        self.correct_str = "0/0"
        
    def handle_event(self, event): pass
    def update(self, dt): pass
        
    def update_pct(self, pct, correct, total):
        self.pct = pct
        self.correct_str = f"{correct}/{total} ô đúng"
        
    def draw(self, screen):
        # Background track
        pygame.draw.rect(screen, (25, 25, 45), self.rect, border_radius=5)
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 1, border_radius=5)
        
        # Glowing fill
        fill_width = int(self.rect.width * (self.pct / 100.0))
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(screen, SUCCESS_ACCENT, fill_rect, border_radius=5)
            
        # Draw text overlay
        font = get_font(12, bold=True)
        txt = f"Tiến trình: {self.pct}% ({self.correct_str})"
        surf = font.render(txt, True, TEXT_COLOR)
        rect = surf.get_rect(center=self.rect.center)
        screen.blit(surf, rect)

class Modal:
    """A popup window for victory announcement and choices."""
    def __init__(self, message, btn1_text, btn1_cb, btn2_text, btn2_cb):
        self.overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        self.overlay.fill((5, 5, 12, 210))
        
        self.rect = pygame.Rect(1280//2 - 250, 720//2 - 150, 500, 300)
        self.panel = Panel(self.rect, radius=20)
        self.title = Label((self.rect.centerx, self.rect.y + 70), message, font_size=28, bold=True, center=True)
        
        btn_y = self.rect.y + 190
        self.btn1 = Button((self.rect.centerx - 180, btn_y, 160, 50), btn1_text, color=SUCCESS_ACCENT, callback=btn1_cb)
        self.btn2 = Button((self.rect.centerx + 20, btn_y, 160, 50), btn2_text, color=DANGER_ACCENT, callback=btn2_cb)
        
    def handle_event(self, event):
        self.btn1.handle_event(event)
        self.btn2.handle_event(event)
        
    def update(self, dt):
        self.btn1.update(dt)
        self.btn2.update(dt)
        
    def draw(self, screen):
        screen.blit(self.overlay, (0, 0))
        self.panel.draw(screen)
        self.title.draw(screen)
        self.btn1.draw(screen)
        self.btn2.draw(screen)

class ComparisonModal:
    """A premium window that executes all solvers and prints stats side-by-side."""
    def __init__(self, results, close_cb):
        self.overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        self.overlay.fill((5, 5, 12, 220))
        
        self.rect = pygame.Rect(1280//2 - 400, 720//2 - 220, 800, 440)
        self.panel = Panel(self.rect, radius=20)
        self.title = Label((self.rect.centerx, self.rect.y + 35), "BẢNG SO SÁNH HIỆU SUẤT THUẬT TOÁN AI", font_size=24, bold=True, center=True)
        self.results = results
        self.close_btn = Button((self.rect.centerx - 70, self.rect.bottom - 60, 140, 40), "Đóng bảng", font_size=15, color=DANGER_ACCENT, callback=close_cb)
        
    def handle_event(self, event):
        self.close_btn.handle_event(event)
        
    def update(self, dt):
        self.close_btn.update(dt)
        
    def draw(self, screen):
        screen.blit(self.overlay, (0, 0))
        self.panel.draw(screen)
        self.title.draw(screen)
        self.close_btn.draw(screen)
        
        # Draw Table Headers
        headers = ["Thuật toán", "Nút đã duyệt", "Số nước giải", "Thời gian (ms)"]
        col_x = [self.rect.x + 50, self.rect.x + 300, self.rect.x + 470, self.rect.x + 640]
        y_start = self.rect.y + 90
        
        font_header = get_font(16, bold=True)
        for h, x in zip(headers, col_x):
            surf = font_header.render(h, True, SECONDARY_ACCENT)
            screen.blit(surf, (x, y_start))
            
        pygame.draw.line(screen, (70, 70, 100), (self.rect.x + 40, y_start + 30), (self.rect.right - 40, y_start + 30), 1)
        
        # Draw rows
        y_row = y_start + 45
        font_row = get_font(15, bold=False)
        for res in self.results:
            name = res["name"]
            nodes = res["nodes"]
            moves = res["moves"]
            time_ms = res["time"]
            
            # Highlight optimal/best results or status
            color = TEXT_COLOR
            if moves == "N/A" or nodes == "10,000+":
                color = SUBTEXT_COLOR
                
            screen.blit(font_row.render(name, True, color), (col_x[0], y_row))
            screen.blit(font_row.render(nodes, True, color), (col_x[1], y_row))
            screen.blit(font_row.render(moves, True, color), (col_x[2], y_row))
            screen.blit(font_row.render(time_ms, True, color), (col_x[3], y_row))
            
            y_row += 45