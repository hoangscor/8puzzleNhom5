import pygame
import sys
import os
import tkinter as tk
from tkinter import filedialog
from image_processor import load_and_split_image
from ui_system import Tile, Modal, BG_COLOR
from ui_statistics import GameDashboard
from game_logic import PuzzleGame
import bfs_solver
import astar_solver
import time

# Core state variables
game = PuzzleGame()
is_finished = False
victory_modal = None
image_tiles = {}
current_image_name = ""

# AI and Animation state
solve_path = []
auto_moving = False
last_move_time = 0
solve_stats = {"nodes": "-", "time": "-"}
start_play_time = 0
elapsed_play_time = 0
has_started_playing = False
last_action_time = time.time()
hint_tile_index = None
hint_blink = False
last_blink_time = 0
hint_start_time = 0

def exit_game():
    pygame.quit()
    sys.exit()

def reset_game():
    global is_finished, victory_modal, auto_moving, solve_path, start_play_time, elapsed_play_time, solve_stats, has_started_playing
    global last_action_time, hint_tile_index, hint_blink, last_blink_time
    game.reset()
    is_finished = False
    victory_modal = None
    auto_moving = False
    solve_path = []
    has_started_playing = False
    start_play_time = 0
    elapsed_play_time = 0
    solve_stats = {"nodes": "-", "time": "-"}

    last_action_time = time.time()
    hint_tile_index = None
    hint_blink = False
    last_blink_time = 0
    hint_start_time = 0

def close_modal():
    global victory_modal
    victory_modal = None

def undo():
    global last_action_time, hint_tile_index
    if not is_finished and game.undo():
        last_action_time = time.time()
        hint_tile_index = None
        pass

def redo():
    global last_action_time, hint_tile_index
    if not is_finished and game.redo():
        last_action_time = time.time()
        hint_tile_index = None
        pass

def solve_bfs():
    global solve_path, auto_moving, solve_stats, has_started_playing, start_play_time
    global hint_tile_index
    if not is_finished and not auto_moving:
        hint_tile_index = None
        path, nodes, duration = bfs_solver.solve(game.current_state, game.goal_state)
        if path:
            if not has_started_playing:
                has_started_playing = True
                start_play_time = time.time()
            solve_path = path
            auto_moving = True
            solve_stats = {"nodes": str(nodes), "time": f"{duration:.1f} ms"}

def solve_astar():
    global solve_path, auto_moving, solve_stats, has_started_playing, start_play_time
    global hint_tile_index
    if not is_finished and not auto_moving:
        hint_tile_index = None
        path, nodes, duration = astar_solver.solve(game.current_state, game.goal_state)
        if path:
            if not has_started_playing:
                has_started_playing = True
                start_play_time = time.time()
            solve_path = path
            auto_moving = True
            solve_stats = {"nodes": str(nodes), "time": f"{duration:.1f} ms"}

def insert_image():
    if is_finished: return
    # File picker for choosing a puzzle image
    file_path = filedialog.askopenfilename(
        title="Chọn ảnh cho Puzzle",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.svg"), ("All files", "*.*")]
    )
    if file_path:
        new_tiles, name = load_and_split_image(file_path, 190)
        if new_tiles:
            global image_tiles, current_image_name
            image_tiles = new_tiles
            current_image_name = name

def handle_tile_click(index):
    global is_finished, victory_modal, has_started_playing, start_play_time, solve_stats
    global last_action_time, hint_tile_index
    if not is_finished and game.move(index):
        last_action_time = time.time()
        hint_tile_index = None

        if not has_started_playing:
            has_started_playing = True
            start_play_time = time.time()
            
        if not auto_moving:
            # Clear AI stats since the user is playing manually
            solve_stats = {"nodes": "-", "time": "-"}

        if game.is_goal():
            is_finished = True
            victory_modal = Modal(
                "Bạn đã giải thành công!",
                "Chơi lại", reset_game,
                "Không", close_modal
            )

def main():
    global auto_moving, last_move_time, solve_path, is_finished, elapsed_play_time, start_play_time, has_started_playing
    global hint_blink, hint_tile_index, last_blink_time, last_action_time, hint_start_time
    pygame.init()
    SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("8-Puzzle Game")
    
    # Tkinter root for dialogs
    root = tk.Tk()
    root.withdraw()
    
    clock = pygame.time.Clock()

    # Define callbacks for the UI
    callbacks = {
        'insert_image': insert_image,
        'reset_game': reset_game,
        'solve_bfs': solve_bfs,
        'solve_astar': solve_astar,
        'undo': undo,
        'redo': redo
    }
    
    # Initialize UI Dashboard (Header, Panels, Buttons)
    dashboard = GameDashboard(SCREEN_WIDTH, SCREEN_HEIGHT, callbacks)
    
    # Initialize Tiles (Logic handled in main loop)
    tile_size = 190
    board_rect = dashboard.board_rect
    start_x = board_rect.x + (board_rect.width - (3 * tile_size)) // 2
    start_y = board_rect.y + (board_rect.height - (3 * tile_size)) // 2
    
    tiles_ui = []
    for i in range(3):
        for j in range(3):
            idx = i * 3 + j
            tile_rect = (start_x + j * tile_size, start_y + i * tile_size, tile_size, tile_size)
            tile = Tile(tile_rect, 0, idx, callback=handle_tile_click)
            tiles_ui.append(tile)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if is_finished and victory_modal:
                victory_modal.handle_event(event)
            else:
                dashboard.handle_event(event)
                if not auto_moving: # Disable manual moves during AI playback
                    for tile in tiles_ui:
                        tile.handle_event(event)
        
        # --- Update ---
        current_time = pygame.time.get_ticks()

        
        # Handle auto playback
        if auto_moving and solve_path:
            if current_time - last_move_time > 300: # 300ms delay between moves
                move_idx = solve_path.pop(0)
                handle_tile_click(move_idx)
                last_move_time = current_time
                if not solve_path:
                    auto_moving = False
        
        # Update play time
        if has_started_playing and not is_finished:
            elapsed_play_time = time.time() - start_play_time
        
        mins = int(elapsed_play_time // 60)
        secs = int(elapsed_play_time % 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        dashboard.update_image_name(current_image_name)
        dashboard.update_stats(play_time=time_str, solve_time=solve_stats["time"], nodes=solve_stats["nodes"])
        
        for i, tile in enumerate(tiles_ui):
            val = game.current_state[i]
            tile.value = val
            tile.image = image_tiles.get(val)

        # --- Hint after 2.5 seconds ---
        if not is_finished and not auto_moving and hint_tile_index is None:
            if time.time() - last_action_time > 2.5:
                path, _, _ = astar_solver.solve(game.current_state, game.goal_state)
                if path:
                    hint_tile_index = path[0]  # Suggest the next move
                    hint_blink = True
                    last_blink_time = current_time
 
        # Blink effect
        if hint_tile_index is not None:
            if current_time - last_blink_time > 300:
                hint_blink = not hint_blink
                last_blink_time = current_time

        # --- Render ---
        screen.fill(BG_COLOR)
        
        dashboard.draw(screen)
        for tile in tiles_ui:
            tile.draw(screen)

        # DRAW HINT
        if hint_tile_index is not None and hint_blink:
            hint_tile = tiles_ui[hint_tile_index]
            pygame.draw.rect(screen, (255, 255, 0), hint_tile.rect, 8)
            
        if is_finished and victory_modal:
            victory_modal.draw(screen)
            
        pygame.display.flip()
        clock.tick(60)

       


    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
