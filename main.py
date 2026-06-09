import pygame
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from image_processor import load_and_split_image
from ui_system import Tile, Modal, BG_COLOR, PRIMARY_ACCENT, SECONDARY_ACCENT, BORDER_COLOR, get_font, draw_gradient_background
from ui_statistics import GameDashboard
from game_logic import PuzzleGame
from game_controller import GameController
import search_simulators
import time

def main():
    controller = GameController(board_size=3)
    
    pygame.init()
    SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("N-Puzzle Search Algorithm Simulator")
    
    root = tk.Tk()
    root.withdraw()
    
    clock = pygame.time.Clock()
    
    controller.dashboard = GameDashboard(SCREEN_WIDTH, SCREEN_HEIGHT, controller.get_callbacks())
    controller.recreate_tiles_ui()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Modal Event Dispatching
            if controller.is_finished and controller.victory_modal:
                controller.victory_modal.handle_event(event)
            elif controller.comparison_modal:
                controller.comparison_modal.handle_event(event)
            else:
                controller.dashboard.handle_event(event)
                
                # Input Controls (Drag & Drop + Keyboard Arrow Moves)
                if not (controller.sim_playing or controller.solution_replay_active):
                    # 1. Keyboard Controls
                    if event.type == pygame.KEYDOWN:
                        empty_idx = controller.game.current_state.index(0)
                        row, col = empty_idx // controller.board_size, empty_idx % controller.board_size
                        target_idx = None
                        if event.key == pygame.K_UP:
                            if row + 1 < controller.board_size:
                                target_idx = (row + 1) * controller.board_size + col
                        elif event.key == pygame.K_DOWN:
                            if row - 1 >= 0:
                                target_idx = (row - 1) * controller.board_size + col
                        elif event.key == pygame.K_LEFT:
                            if col + 1 < controller.board_size:
                                target_idx = row * controller.board_size + (col + 1)
                        elif event.key == pygame.K_RIGHT:
                            if col - 1 >= 0:
                                target_idx = row * controller.board_size + (col - 1)
                    
                        if target_idx is not None:
                            handle_tile_click(controller, target_idx)
                            
                    # 2. Drag & Drop Event Handlers
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        clicked = None
                        for t in controller.tiles_ui.values():
                            if t.curr_x is None or t.curr_y is None:
                                continue
                            t_rect = pygame.Rect(t.curr_x, t.curr_y, t.width, t.height)
                            if t_rect.collidepoint(mx, my):
                                clicked = t
                                break
                        
                        if clicked:
                            empty_idx = controller.game.current_state.index(0)
                            tile_idx = clicked.index
                            r_empty, c_empty = empty_idx // controller.board_size, empty_idx % controller.board_size
                            r_tile, c_tile = tile_idx // controller.board_size, tile_idx % controller.board_size
                            
                            if abs(r_empty - r_tile) + abs(c_empty - c_tile) == 1:
                                controller.dragged_tile = clicked
                                controller.dragged_tile.is_dragging = True
                                controller.drag_start_x, controller.drag_start_y = mx, my
                                controller.drag_allowed_dx = c_empty - c_tile
                                controller.drag_allowed_dy = r_empty - r_tile
                                
                    elif event.type == pygame.MOUSEMOTION:
                        if controller.dragged_tile:
                            mx, my = event.pos
                            dx = mx - controller.drag_start_x
                            dy = my - controller.drag_start_y
                            tile_size = 580 // controller.board_size
                            
                            if controller.drag_allowed_dx != 0:
                                offset = dx * controller.drag_allowed_dx
                                offset = max(0, min(tile_size, offset))
                                controller.dragged_tile.drag_offset_x = offset * controller.drag_allowed_dx
                                controller.dragged_tile.drag_offset_y = 0
                            elif controller.drag_allowed_dy != 0:
                                offset = dy * controller.drag_allowed_dy
                                offset = max(0, min(tile_size, offset))
                                controller.dragged_tile.drag_offset_y = offset * controller.drag_allowed_dy
                                controller.dragged_tile.drag_offset_x = 0
                                
                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        if controller.dragged_tile:
                            tile_size = 580 // controller.board_size
                            offset = max(abs(controller.dragged_tile.drag_offset_x), abs(controller.dragged_tile.drag_offset_y))
                            
                            if offset > tile_size * 0.45:
                                handle_tile_click(controller, controller.dragged_tile.index)
                                
                            controller.dragged_tile.drag_offset_x = 0
                            controller.dragged_tile.drag_offset_y = 0
                            controller.dragged_tile.is_dragging = False
                            controller.dragged_tile = None
        
        # --- Update simulation auto-playback ---
        if controller.sim_playing and controller.solution_replay_active:
            delay = controller.speed_delays.get(controller.current_speed, 300)
            if current_time - controller.last_sim_step_time > delay:
                controller.step_sim_forward()
                if controller.solution_replay_idx >= len(controller.solution_path):
                    controller.sim_playing = False
                controller.last_sim_step_time = current_time

        # Update play time
        if controller.has_started_playing and not controller.is_finished:
            controller.elapsed_play_time = time.time() - controller.start_play_time
        
        mins = int(controller.elapsed_play_time // 60)
        secs = int(controller.elapsed_play_time % 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        # Dashboard updates
        controller.dashboard.update_image_name(controller.current_image_name)
        controller.dashboard.update_game_stats(elapsed_time_str=time_str, moves_count=len(controller.game.history))
        
        # Progress Calculation & Update
        pct, correct, total = controller.game.get_progress()
        controller.dashboard.progress_bar.update_pct(pct, correct, total)
        
        controller.dashboard.set_active_algorithm(controller.current_algo)
        controller.dashboard.set_active_speed(controller.current_speed)
        controller.dashboard.set_active_size(controller.board_size)
        controller.dashboard.set_active_goal_preset(controller.game.goal_preset)
        controller.dashboard.set_play_state(controller.sim_playing)
        controller.dashboard.update(dt)
        
        if controller.comparison_modal:
            controller.comparison_modal.update(dt)
        if controller.victory_modal:
            controller.victory_modal.update(dt)
        
        # Extract simulation stats
        if controller.sim_current_step is not None:
            nodes_val = controller.sim_current_step.get("nodes_expanded", 0)
            frontier_val = controller.sim_current_step.get("frontier_size", 0)
            depth_val = controller.sim_current_step.get("depth", 0)
            h_val = controller.sim_current_step.get("h_score", 0)
            f_val = controller.sim_current_step.get("f_score", 0)
            dur_val = controller.sim_current_step.get("total_time_ms", 0.0)
            
            controller.dashboard.update_simulation_stats(
                nodes_expanded=nodes_val,
                frontier_size=frontier_val,
                depth=depth_val,
                h_val=h_val,
                f_val=f_val,
                duration_ms=dur_val
            )
        else:
            controller.dashboard.update_simulation_stats(0, 0, 0, 0, 0, 0.0)

        # Update tile target pixel rects
        active_board_state = controller.game.current_state
        tile_size = 580 // controller.board_size
        board_rect = controller.dashboard.board_rect
        start_x = board_rect.x + (board_rect.width - (controller.board_size * tile_size)) // 2
        start_y = board_rect.y + (board_rect.height - (controller.board_size * tile_size)) // 2

        for i, val in enumerate(active_board_state):
            if val != 0:
                row = i // controller.board_size
                col = i % controller.board_size
                tile_rect = (start_x + col * tile_size, start_y + row * tile_size, tile_size, tile_size)
                tile = controller.tiles_ui.get(val)
                if tile:
                    tile.index = i
                    tile.set_target(tile_rect)
                    tile.image = controller.image_tiles.get(val)
                    
        # Lerp update
        for tile in controller.tiles_ui.values():
            tile.update(dt)

        # --- Render ---
        draw_gradient_background(screen)
        
        controller.dashboard.draw(screen)
        
        # Draw Original Image Preview if loaded
        if controller.original_image_surface:
            screen.blit(controller.original_image_surface, controller.dashboard.preview_rect.topleft)
            pygame.draw.rect(screen, BORDER_COLOR, controller.dashboard.preview_rect, 1, border_radius=8)
            
        for tile in controller.tiles_ui.values():
            tile.draw(screen)
            
        if controller.solution_replay_active:
            pygame.draw.rect(screen, PRIMARY_ACCENT, controller.dashboard.board_rect.inflate(10, 10), 2, border_radius=12)
            pygame.draw.rect(screen, SECONDARY_ACCENT, controller.dashboard.board_rect.inflate(14, 14), 1, border_radius=14)
            
        if controller.comparison_modal:
            controller.comparison_modal.draw(screen)
        elif controller.is_finished and controller.victory_modal:
            controller.victory_modal.draw(screen)
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

def handle_tile_click(controller, index):
    if controller.is_finished or controller.sim_status == "searching" or controller.sim_playing or controller.solution_replay_active:
        return
        
    if controller.game.move(index):
        if not controller.has_started_playing:
            controller.has_started_playing = True
            controller.start_play_time = time.time()
            
        if controller.game.is_goal():
            controller.trigger_victory()

if __name__ == "__main__":
    main()