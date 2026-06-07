import os
import pygame
from PIL import Image

def load_and_split_image(file_path, tile_size, grid_size=3):
    """
    Loads, resizes and splits an image into tiles for the N-Puzzle game.
    Returns a dictionary mapping tile values (1-8) to Pygame surfaces.
    """
    try:
        # Load image with PIL and convert to RGB
        pil_img = Image.open(file_path).convert("RGB")
        
        # Calculate total size based on tile size and grid (3x3)
        total_width = tile_size * grid_size
        total_height = tile_size * grid_size
        
        # Resize image to fit the board exactly using LANCZOS for quality
        pil_img = pil_img.resize((total_width, total_height), Image.Resampling.LANCZOS)
        
        image_tiles = {}
        for i in range(grid_size):
            for j in range(grid_size):
                # Determine the logic value (1 to 8, last tile is 0)
                val = i * grid_size + j + 1
                if val == grid_size * grid_size: 
                    val = 0 # Last tile represents the empty slot
                
                if val != 0:
                    # Crop the piece from the main image
                    left = j * tile_size
                    top = i * tile_size
                    right = left + tile_size
                    bottom = top + tile_size
                    crop = pil_img.crop((left, top, right, bottom))
                    
                    # Convert from PIL Image to Pygame Surface
                    mode = crop.mode
                    size = crop.size
                    data = crop.tobytes()
                    py_img = pygame.image.fromstring(data, size, mode)
                    image_tiles[val] = py_img
        
        # Return the tiles dictionary and original filename
        return image_tiles, os.path.basename(file_path)
    except Exception as e:
        print(f"Error processing image: {e}")
        return None, None
