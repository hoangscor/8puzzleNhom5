import pygame

# Modern Dark Theme Colors
BG_COLOR = (18, 18, 18)           # Deep Dark Background
PANEL_BG = (30, 30, 30)           # Elevation Surface
TEXT_COLOR = (240, 240, 240)      # High Emphasis Text
SUBTEXT_COLOR = (160, 160, 160)    # Medium Emphasis Text
BORDER_COLOR = (45, 45, 45)       # Subtle Borders

# Accent Colors
PRIMARY_ACCENT = (0, 162, 232)    # Cyan Blue
SECONDARY_ACCENT = (155, 89, 182) # Amethyst Purple
DANGER_ACCENT = (231, 76, 60)     # Soft Red
SUCCESS_ACCENT = (46, 204, 113)   # Emerald Green
BTN_DEFAULT = (45, 45, 45)        # Button Surface
BTN_HOVER = (60, 60, 60)          # Button Hover

def get_font(size, bold=False):
    """Returns a system font with the given size and weight."""
    font_priority = ['segoe ui', 'tahoma', 'arial', 'sans-serif']
    return pygame.font.SysFont(font_priority, size, bold=bold)

class Panel:
    """A simple container with rounded corners and a border."""
    def __init__(self, rect, radius=15):
        self.rect = pygame.Rect(rect)
        self.radius = radius
        
    def handle_event(self, event): pass
    def update(self): pass
        
    def draw(self, screen):
        # Draw the shadow-like panel background
        pygame.draw.rect(screen, PANEL_BG, self.rect, border_radius=self.radius)
        # Draw a subtle border
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, 2, border_radius=self.radius)

class Label:
    """A text element that can be centered or topleft-aligned."""
    def __init__(self, pos, text, font_size=18, color=TEXT_COLOR, bold=False, center=False):
        self.pos = pos
        self.text = str(text)
        self.font = get_font(font_size, bold)
        self.color = color
        self.center = center
        
    def handle_event(self, event): pass
    def update(self): pass
        
    def draw(self, screen):
        text_surf = self.font.render(self.text, True, self.color)
        text_rect = text_surf.get_rect()
        if self.center:
            text_rect.center = self.pos
        else:
            text_rect.topleft = self.pos
        screen.blit(text_surf, text_rect)

class Button:
    """A clickable button with hover effects."""
    def __init__(self, rect, text, font_size=18, callback=None, color=None, radius=12):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = get_font(font_size, bold=True)
        self.callback = callback
        self.is_hovered = False
        self.base_color = color if color else BTN_DEFAULT
        self.radius = radius
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                if self.callback:
                    self.callback()
                    
    def update(self): pass
        
    def draw(self, screen):
        color = BTN_HOVER if self.is_hovered else self.base_color
        pygame.draw.rect(screen, color, self.rect, border_radius=self.radius)
        
        text_surf = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

class Tile:
    """Class to manage individual puzzle pieces."""
    def __init__(self, rect, value, index, color=None, callback=None, radius=8):
        self.rect = pygame.Rect(rect)
        self.value = value             # Tile value (1-8, or 0 for empty)
        self.index = index             # Current index on board
        self.font = get_font(42, bold=True)
        self.callback = callback
        self.image = None              # Holds the sub-image surface
        self.radius = radius
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback(self.index)
                    
    def update(self): pass
        
    def draw(self, screen):
        if self.value == 0:
            # Draw empty slot
            pygame.draw.rect(screen, (25, 25, 25), self.rect, border_radius=self.radius)
        else:
            if self.image:
                screen.blit(self.image, self.rect)
                # Subtle border for tile differentiation
                pygame.draw.rect(screen, (255,255,255,30), self.rect, 1, border_radius=self.radius)
            else:
                pygame.draw.rect(screen, BTN_DEFAULT, self.rect, border_radius=self.radius)
                text_surf = self.font.render(str(self.value), True, PRIMARY_ACCENT)
                text_rect = text_surf.get_rect(center=self.rect.center)
                screen.blit(text_surf, text_rect)
                pygame.draw.rect(screen, BORDER_COLOR, self.rect, 1, border_radius=self.radius)

class Modal:
    """A popup window for victory announcement and choices."""
    def __init__(self, message, btn1_text, btn1_cb, btn2_text, btn2_cb):
        self.overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 190)) # Dim the background
        
        self.rect = pygame.Rect(1280//2 - 250, 720//2 - 150, 500, 300)
        self.panel = Panel(self.rect, radius=20)
        self.title = Label((self.rect.centerx, self.rect.y + 70), message, font_size=28, bold=True, center=True)
        
        btn_y = self.rect.y + 190
        self.btn1 = Button((self.rect.centerx - 180, btn_y, 160, 50), btn1_text, color=SUCCESS_ACCENT, callback=btn1_cb)
        self.btn2 = Button((self.rect.centerx + 20, btn_y, 160, 50), btn2_text, color=DANGER_ACCENT, callback=btn2_cb)
        
    def handle_event(self, event):
        self.btn1.handle_event(event)
        self.btn2.handle_event(event)
        
    def draw(self, screen):
        screen.blit(self.overlay, (0, 0))
        self.panel.draw(screen)
        self.title.draw(screen)
        self.btn1.draw(screen)
        self.btn2.draw(screen)