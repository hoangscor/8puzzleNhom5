"""
Sound Manager for N-Puzzle Game.
Handles loading and playing sound effects using pygame.mixer.
"""
import pygame
import os


class SoundManager:
    """Manages sound effects for the puzzle game."""
    
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        self._init_sounds()
    
    def _init_sounds(self):
        """Load sound files from assets directory."""
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        sound_files = {
            "move": "move.wav",
            "victory": "victory.wav",
            "error": "error.wav",
        }
        for key, filename in sound_files.items():
            path = os.path.join(assets_dir, filename)
            if os.path.exists(path):
                try:
                    self.sounds[key] = pygame.mixer.Sound(path)
                    self.sounds[key].set_volume(0.5)
                except Exception:
                    pass
    
    def play(self, name):
        """Play a sound by name."""
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass
    
    def toggle(self):
        """Toggle sound on/off."""
        self.enabled = not self.enabled
        return self.enabled
