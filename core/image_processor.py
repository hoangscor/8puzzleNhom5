import os
import pygame
from PIL import Image

def load_and_split_image(file_path, tile_size, grid_size=3):
    """
    Loads, resizes and splits an image into tiles for the N-Puzzle game.
    Returns a list of Pygame surfaces indexed by flat position (0 to N*N-1).
    """
    try:
        # Load image with PIL and convert to RGB
        pil_img = Image.open(file_path).convert("RGB")
        
        # Calculate total size based on tile size and grid
        total_width = tile_size * grid_size
        total_height = tile_size * grid_size
        
        # Resize image to fit the board exactly using LANCZOS for quality
        pil_img = pil_img.resize((total_width, total_height), Image.Resampling.LANCZOS)
        
        # Generate all crops indexed by flat position (0 to N*N-1)
        crops = [None] * (grid_size * grid_size)
        for i in range(grid_size):
            for j in range(grid_size):
                pos = i * grid_size + j
                left = j * tile_size
                top = i * tile_size
                right = left + tile_size
                bottom = top + tile_size
                crop = pil_img.crop((left, top, right, bottom))
                
                # Convert from PIL Image to Pygame Surface
                mode = crop.mode
                size = crop.size
                data = crop.tobytes()
                crops[pos] = pygame.image.fromstring(data, size, mode)
        
        return crops, os.path.basename(file_path)
    except Exception as e:
        print(f"Error processing image: {e}")
        return None, None
