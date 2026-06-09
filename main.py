import pygame
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from image_processor import load_and_split_image
from ui_system import Tile, Modal, BG_COLOR, PRIMARY_ACCENT, SECONDARY_ACCENT, BORDER_COLOR, get_font, draw_gradient_background
from ui_statistics import GameDashboard
from game_logic import PuzzleGame
import search_simulators
import time

# Core state variables
board_size = 3
game = PuzzleGame(size=board_size)
is_finished = False
victory_modal = None
comparison_modal = None
image_tiles = {}
current_image_name = ""
original_image_surface = None
current_image_path = ""

# AI Simulation and Animation state
current_algo = "astar_manhattan"
current_speed = "medium"
speed_delays = {"slow": 800, "medium": 300, "fast": 80, "max": 1}

sim_generator = None
sim_history = []
sim_playing = False
sim_current_step = None
sim_status = "idle"  # "idle", "searching", "success", "failed"
sim_initial_state = []

solution_path = []
solution_replay_active = False
solution_replay_idx = 0
last_sim_step_time = 0

start_play_time = 0
elapsed_play_time = 0
has_started_playing = False

# Drag and Drop state variables
dragged_tile = None
drag_start_x = 0
drag_start_y = 0
drag_allowed_dx = 0
drag_allowed_dy = 0

# Global UI components
tiles_ui = {}  # Maps value (1 to N^2-1) -> Tile object
dashboard = None

def exit_game():
    pygame.quit()
    sys.exit()

def reset_game():
    global is_finished, victory_modal, comparison_modal, has_started_playing, start_play_time, elapsed_play_time
    game.reset()
    is_finished = False
    victory_modal = None
    comparison_modal = None
    has_started_playing = False
    start_play_time = 0
    elapsed_play_time = 0
    stop_simulation()
    recreate_tiles_ui()

def close_modal():
    global victory_modal
    victory_modal = None

def undo():
    if is_finished or sim_status == "searching" or sim_playing or solution_replay_active:
        return
    game.undo()

def redo():
    if is_finished or sim_status == "searching" or sim_playing or solution_replay_active:
        return
    game.redo()

def select_algorithm(algo_name):
    global current_algo
    current_algo = algo_name
    stop_simulation()

def select_speed(speed_name):
    global current_speed
    current_speed = speed_name

def change_size(new_size):
    global board_size, game, image_tiles, current_image_name, original_image_surface
    if board_size == new_size:
        return
    board_size = new_size
    current_preset = game.goal_preset
    game = PuzzleGame(size=board_size)
    game.set_goal_preset(current_preset)
    stop_simulation()
    
    # Auto re-crop image if loaded
    if current_image_path:
        tile_size = 580 // board_size
        new_tiles, name = load_and_split_image(current_image_path, tile_size, board_size)
        if new_tiles:
            image_tiles = new_tiles
            current_image_name = name
            try:
                raw_surf = pygame.image.load(current_image_path).convert()
                original_image_surface = pygame.transform.smoothscale(raw_surf, (200, 160))
            except Exception as e:
                print(f"Error loading preview: {e}")
                original_image_surface = None
    else:
        image_tiles = {}
        current_image_name = ""
        original_image_surface = None
        
    recreate_tiles_ui()

def change_goal_preset(new_preset):
    if game.goal_preset == new_preset:
        return
    game.set_goal_preset(new_preset)
    stop_simulation()
    recreate_tiles_ui()

def recreate_tiles_ui():
    global tiles_ui, board_size, dashboard
    tiles_ui.clear()
    
    tile_size = 580 // board_size
    board_rect = dashboard.board_rect
    start_x = board_rect.x + (board_rect.width - (board_size * tile_size)) // 2
    start_y = board_rect.y + (board_rect.height - (board_size * tile_size)) // 2
    
    radius = max(2, 8 - (board_size - 3))
    font_size = max(12, 42 - (board_size - 3) * 5)
    
    for val in range(1, board_size * board_size):
        tile = Tile(None, val, 0, radius=radius)
        tile.font = get_font(font_size, bold=True)
        tiles_ui[val] = tile
        
    # Immediately position them based on current board state to avoid None coordinates on startup
    active_board_state = game.current_state
    for i, val in enumerate(active_board_state):
        if val != 0:
            row = i // board_size
            col = i % board_size
            tile_rect = (start_x + col * tile_size, start_y + row * tile_size, tile_size, tile_size)
            tile = tiles_ui.get(val)
            if tile:
                tile.index = i
                tile.set_target(tile_rect)

def start_simulation():
    global sim_generator, sim_history, sim_playing, sim_status, sim_current_step, solution_path, solution_replay_active, sim_initial_state
    stop_simulation()
    
    sim_initial_state = list(game.current_state)
    initial = list(game.current_state)
    goal = list(game.goal_state)
    
    max_nodes_limit = 10000
    
    if current_algo == "bi_astar":
        sim_generator = search_simulators.bidirectional_astar_simulator(initial, goal, size=board_size, max_nodes=max_nodes_limit)
    elif current_algo == "idastar":
        sim_generator = search_simulators.idastar_simulator(initial, goal, size=board_size, max_nodes=max_nodes_limit)
    elif current_algo == "gbfs":
        sim_generator = search_simulators.gbfs_simulator(initial, goal, "manhattan", size=board_size, max_nodes=max_nodes_limit)
    elif current_algo == "astar_manhattan":
        sim_generator = search_simulators.astar_simulator(initial, goal, "manhattan", size=board_size, max_nodes=max_nodes_limit)
    elif current_algo == "astar_misplaced":
        sim_generator = search_simulators.astar_simulator(initial, goal, "misplaced", size=board_size, max_nodes=max_nodes_limit)
        
    sim_status = "searching"
    sim_history = []
    solution_path = []
    solution_replay_active = False

def run_search_instantly():
    global sim_generator, sim_status, solution_path, sim_current_step
    if not sim_generator:
        return
        
    last_step = None
    while True:
        try:
            step = next(sim_generator)
            last_step = step
            if step["status"] in ("success", "failed"):
                break
        except StopIteration:
            break
            
    if last_step:
        sim_current_step = last_step
        if last_step["status"] == "success":
            sim_status = "success"
            solution_path = last_step["path"]
        else:
            sim_status = "failed"

def stop_simulation():
    global sim_generator, sim_history, sim_playing, sim_current_step, sim_status, solution_path, solution_replay_active
    sim_generator = None
    sim_history = []
    sim_playing = False
    sim_current_step = None
    sim_status = "idle"
    solution_path = []
    solution_replay_active = False

def play_pause_sim():
    global sim_playing, sim_status, solution_replay_active, solution_replay_idx, has_started_playing, start_play_time
    if is_finished:
        return
        
    if sim_status == "idle":
        start_simulation()
        run_search_instantly()
        
    if sim_status == "success" and solution_path:
        if not solution_replay_active:
            solution_replay_active = True
            solution_replay_idx = 0
            game.current_state = list(sim_initial_state)
            game.history.clear()
            game.redo_stack.clear()
            has_started_playing = True
            start_play_time = time.time()
        sim_playing = not sim_playing

def step_sim_forward():
    global sim_generator, sim_history, sim_current_step, sim_status, sim_playing, solution_path, solution_replay_active, solution_replay_idx, has_started_playing, start_play_time
    if is_finished:
        return
        
    if sim_status == "idle":
        start_simulation()
        run_search_instantly()
        
    if sim_status == "success" and solution_path:
        if not solution_replay_active:
            solution_replay_active = True
            solution_replay_idx = 0
            game.current_state = list(sim_initial_state)
            game.history.clear()
            game.redo_stack.clear()
            has_started_playing = True
            start_play_time = time.time()
            return
            
        if solution_replay_idx < len(solution_path):
            move_idx = solution_path[solution_replay_idx]
            game.move(move_idx)
            solution_replay_idx += 1
            if game.is_goal():
                trigger_victory()

def step_sim_backward():
    global solution_replay_active, solution_replay_idx
    if is_finished or not solution_replay_active:
        return
        
    if solution_replay_idx > 0:
        solution_replay_idx -= 1
        game.undo()

def run_compare_solvers():
    global comparison_modal
    stop_simulation()
    
    initial = list(game.current_state)
    goal = list(game.goal_state)
    results = []
    
    # 1. Bi-directional A*
    bi_gen = search_simulators.bidirectional_astar_simulator(initial, goal, size=board_size, max_nodes=10000)
    bi_res = run_generator_to_end(bi_gen)
    results.append({
        "name": "Bi-directional A*",
        "nodes": f"{bi_res['nodes_expanded']:,}" if bi_res["status"] == "success" else "10,000+",
        "moves": f"{len(bi_res['path'])}" if bi_res["status"] == "success" else "N/A",
        "time": f"{bi_res['total_time_ms']:.1f}" if bi_res["status"] == "success" else "Limit"
    })
    
    # 2. IDA*
    ida_gen = search_simulators.idastar_simulator(initial, goal, size=board_size, max_nodes=10000)
    ida_res = run_generator_to_end(ida_gen)
    results.append({
        "name": "Iterative Deepening A* (IDA*)",
        "nodes": f"{ida_res['nodes_expanded']:,}" if ida_res["status"] == "success" else "10,000+",
        "moves": f"{len(ida_res['path'])}" if ida_res["status"] == "success" else "N/A",
        "time": f"{ida_res['total_time_ms']:.1f}" if ida_res["status"] == "success" else "Limit"
    })
    
    # 3. GBFS
    gbfs_gen = search_simulators.gbfs_simulator(initial, goal, "manhattan", size=board_size, max_nodes=10000)
    gbfs_res = run_generator_to_end(gbfs_gen)
    results.append({
        "name": "Greedy Best-First (GBFS)",
        "nodes": f"{gbfs_res['nodes_expanded']:,}" if gbfs_res["status"] == "success" else "10,000+",
        "moves": f"{len(gbfs_res['path'])}" if gbfs_res["status"] == "success" else "N/A",
        "time": f"{gbfs_res['total_time_ms']:.1f}" if gbfs_res["status"] == "success" else "Limit"
    })
    
    # 4. A* Manhattan
    astar_m_gen = search_simulators.astar_simulator(initial, goal, "manhattan", size=board_size, max_nodes=10000)
    astar_m_res = run_generator_to_end(astar_m_gen)
    results.append({
        "name": "A* (Manhattan Distance)",
        "nodes": f"{astar_m_res['nodes_expanded']:,}" if astar_m_res["status"] == "success" else "10,000+",
        "moves": f"{len(astar_m_res['path'])}" if astar_m_res["status"] == "success" else "N/A",
        "time": f"{astar_m_res['total_time_ms']:.1f}" if astar_m_res["status"] == "success" else "Limit"
    })
    
    # 5. A* Misplaced
    astar_mp_gen = search_simulators.astar_simulator(initial, goal, "misplaced", size=board_size, max_nodes=10000)
    astar_mp_res = run_generator_to_end(astar_mp_gen)
    results.append({
        "name": "A* (Misplaced Tiles)",
        "nodes": f"{astar_mp_res['nodes_expanded']:,}" if astar_mp_res["status"] == "success" else "10,000+",
        "moves": f"{len(astar_mp_res['path'])}" if astar_mp_res["status"] == "success" else "N/A",
        "time": f"{astar_mp_res['total_time_ms']:.1f}" if astar_mp_res["status"] == "success" else "Limit"
    })
    
    from ui_system import ComparisonModal
    comparison_modal = ComparisonModal(results, close_compare_solvers)

def run_generator_to_end(gen):
    last_step = None
    while True:
        try:
            step = next(gen)
            last_step = step
            if step["status"] in ("success", "failed"):
                break
        except StopIteration:
            break
    return last_step

def close_compare_solvers():
    global comparison_modal
    comparison_modal = None

def trigger_victory():
    global is_finished, victory_modal
    is_finished = True
    victory_modal = Modal(
        "Bạn đã giải thành công!",
        "Chơi lại", reset_game,
        "Không", close_modal
    )

def insert_image():
    if is_finished or sim_status == "searching" or sim_playing or solution_replay_active:
        return
    file_path = filedialog.askopenfilename(
        title="Chọn ảnh cho Puzzle",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.svg"), ("All files", "*.*")]
    )
    if file_path:
        tile_size = 580 // board_size
        new_tiles, name = load_and_split_image(file_path, tile_size, board_size)
        if new_tiles:
            global image_tiles, current_image_name, original_image_surface, current_image_path
            image_tiles = new_tiles
            current_image_name = name
            current_image_path = file_path
            
            # Load original image for preview
            try:
                raw_surf = pygame.image.load(file_path).convert()
                original_image_surface = pygame.transform.smoothscale(raw_surf, (200, 160))
            except Exception as e:
                print(f"Error loading preview: {e}")
                original_image_surface = None

def handle_tile_click(index):
    global is_finished, has_started_playing, start_play_time
    if is_finished or sim_status == "searching" or sim_playing or solution_replay_active:
        return
        
    if game.move(index):
        if not has_started_playing:
            has_started_playing = True
            start_play_time = time.time()
            
        if game.is_goal():
            trigger_victory()

def export_solution_log():
    if not solution_path:
        messagebox.showwarning("Cảnh báo", "Chưa có lời giải nào được tìm thấy. Hãy chạy thuật toán trước!")
        return
        
    file_path = filedialog.asksaveasfilename(
        title="Lưu log bước chạy",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        initialfile=f"log_giai_{current_algo}_{board_size}x{board_size}.txt"
    )
    if not file_path:
        return
        
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("==================================================\n")
            f.write("             N-PUZZLE SOLUTION LOG\n")
            f.write("==================================================\n\n")
            
            algo_display_names = {
                "bi_astar": "Bi-directional A* (A* hai chiều)",
                "idastar": "Iterative Deepening A* (IDA*)",
                "gbfs": "Greedy Best-First Search (GBFS)",
                "astar_manhattan": "A* (Manhattan Distance)",
                "astar_misplaced": "A* (Misplaced Tiles)"
            }
            f.write(f"Thuật toán sử dụng: {algo_display_names.get(current_algo, current_algo)}\n")
            f.write(f"Kích thước bàn cờ: {board_size}x{board_size}\n")
            f.write(f"Trạng thái bắt đầu: {sim_initial_state}\n")
            f.write(f"Trạng thái đích: {game.goal_state}\n")
            f.write(f"Tổng số bước di chuyển: {len(solution_path)}\n\n")
            
            f.write("Danh sách các bước di chuyển chi tiết:\n")
            f.write("--------------------------------------------------\n")
            
            curr_state = list(sim_initial_state)
            size = board_size
            for step_no, move_idx in enumerate(solution_path, 1):
                empty_idx = curr_state.index(0)
                r_empty, c_empty = empty_idx // size, empty_idx % size
                r_tile, c_tile = move_idx // size, move_idx % size
                
                direction = ""
                if r_tile < r_empty:
                    direction = "XUỐNG (DOWN)"
                elif r_tile > r_empty:
                    direction = "LÊN (UP)"
                elif c_tile < c_empty:
                    direction = "SANG PHẢI (RIGHT)"
                elif c_tile > c_empty:
                    direction = "SANG TRÁI (LEFT)"
                
                tile_val = curr_state[move_idx]
                f.write(f"Bước {step_no:02d}: Di chuyển ô số {tile_val} {direction} (từ vị trí {move_idx} sang ô trống {empty_idx})\n")
                
                # Perform the move
                curr_state[empty_idx], curr_state[move_idx] = curr_state[move_idx], curr_state[empty_idx]
                
            f.write("--------------------------------------------------\n")
            f.write("Trạng thái kết thúc: Đã đạt mục tiêu!\n")
            f.write("==================================================\n")
            
        messagebox.showinfo("Thành công", f"Đã xuất log bước chạy thành công ra file:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể ghi log ra file: {e}")

def main():
    global sim_playing, last_sim_step_time, sim_status, elapsed_play_time, start_play_time, has_started_playing, is_finished, dashboard
    global dragged_tile, drag_start_x, drag_start_y, drag_allowed_dx, drag_allowed_dy, comparison_modal, victory_modal
    
    pygame.init()
    SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("N-Puzzle Search Algorithm Simulator")
    
    root = tk.Tk()
    root.withdraw()
    
    clock = pygame.time.Clock()

    callbacks = {
        'insert_image': insert_image,
        'reset_game': reset_game,
        'select_algorithm': select_algorithm,
        'select_speed': select_speed,
        'play_pause': play_pause_sim,
        'step_forward': step_sim_forward,
        'step_backward': step_sim_backward,
        'stop_simulation': stop_simulation,
        'change_size': change_size,
        'compare_solvers': run_compare_solvers,
        'undo': undo,
        'redo': redo,
        'export_log': export_solution_log,
        'change_goal_preset': change_goal_preset
    }
    
    dashboard = GameDashboard(SCREEN_WIDTH, SCREEN_HEIGHT, callbacks)
    recreate_tiles_ui()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Modal Event Dispatching
            if is_finished and victory_modal:
                victory_modal.handle_event(event)
            elif comparison_modal:
                comparison_modal.handle_event(event)
            else:
                dashboard.handle_event(event)
                
                # Input Controls (Drag & Drop + Keyboard Arrow Moves)
                if not (sim_playing or solution_replay_active):
                    # 1. Keyboard Controls
                    if event.type == pygame.KEYDOWN:
                        empty_idx = game.current_state.index(0)
                        row, col = empty_idx // board_size, empty_idx % board_size
                        target_idx = None
                        if event.key == pygame.K_UP:
                            if row + 1 < board_size:
                                target_idx = (row + 1) * board_size + col
                        elif event.key == pygame.K_DOWN:
                            if row - 1 >= 0:
                                target_idx = (row - 1) * board_size + col
                        elif event.key == pygame.K_LEFT:
                            if col + 1 < board_size:
                                target_idx = row * board_size + (col + 1)
                        elif event.key == pygame.K_RIGHT:
                            if col - 1 >= 0:
                                target_idx = row * board_size + (col - 1)
                        
                        if target_idx is not None:
                            handle_tile_click(target_idx)
                            
                    # 2. Drag & Drop Event Handlers
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        # Find clicked Tile
                        clicked = None
                        for t in tiles_ui.values():
                            if t.curr_x is None or t.curr_y is None:
                                continue
                            t_rect = pygame.Rect(t.curr_x, t.curr_y, t.width, t.height)
                            if t_rect.collidepoint(mx, my):
                                clicked = t
                                break
                        
                        if clicked:
                            # Verify if adjacent to the empty cell
                            empty_idx = game.current_state.index(0)
                            tile_idx = clicked.index
                            r_empty, c_empty = empty_idx // board_size, empty_idx % board_size
                            r_tile, c_tile = tile_idx // board_size, tile_idx % board_size
                            
                            if abs(r_empty - r_tile) + abs(c_empty - c_tile) == 1:
                                dragged_tile = clicked
                                dragged_tile.is_dragging = True
                                drag_start_x, drag_start_y = mx, my
                                drag_allowed_dx = c_empty - c_tile
                                drag_allowed_dy = r_empty - r_tile
                                
                    elif event.type == pygame.MOUSEMOTION:
                        if dragged_tile:
                            mx, my = event.pos
                            dx = mx - drag_start_x
                            dy = my - drag_start_y
                            tile_size = 580 // board_size
                            
                            if drag_allowed_dx != 0:
                                offset = dx * drag_allowed_dx
                                offset = max(0, min(tile_size, offset))
                                dragged_tile.drag_offset_x = offset * drag_allowed_dx
                                dragged_tile.drag_offset_y = 0
                            elif drag_allowed_dy != 0:
                                offset = dy * drag_allowed_dy
                                offset = max(0, min(tile_size, offset))
                                dragged_tile.drag_offset_y = offset * drag_allowed_dy
                                dragged_tile.drag_offset_x = 0
                                
                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        if dragged_tile:
                            tile_size = 580 // board_size
                            offset = max(abs(dragged_tile.drag_offset_x), abs(dragged_tile.drag_offset_y))
                            
                            # Perform move if dragged more than 45% of the size
                            if offset > tile_size * 0.45:
                                handle_tile_click(dragged_tile.index)
                                
                            dragged_tile.drag_offset_x = 0
                            dragged_tile.drag_offset_y = 0
                            dragged_tile.is_dragging = False
                            dragged_tile = None
        
        # --- Update simulation auto-playback ---
        if sim_playing and solution_replay_active:
            delay = speed_delays.get(current_speed, 300)
            if current_time - last_sim_step_time > delay:
                step_sim_forward()
                if solution_replay_idx >= len(solution_path):
                    sim_playing = False
                last_sim_step_time = current_time

        # Update play time
        if has_started_playing and not is_finished:
            elapsed_play_time = time.time() - start_play_time
        
        mins = int(elapsed_play_time // 60)
        secs = int(elapsed_play_time % 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        # Dashboard updates
        dashboard.update_image_name(current_image_name)
        dashboard.update_game_stats(elapsed_time_str=time_str, moves_count=len(game.history))
        
        # Progress Calculation & Update
        pct, correct, total = game.get_progress()
        dashboard.progress_bar.update_pct(pct, correct, total)
        
        dashboard.set_active_algorithm(current_algo)
        dashboard.set_active_speed(current_speed)
        dashboard.set_active_size(board_size)
        dashboard.set_active_goal_preset(game.goal_preset)
        dashboard.set_play_state(sim_playing)
        dashboard.update(dt)
        
        if comparison_modal:
            comparison_modal.update(dt)
        if victory_modal:
            victory_modal.update(dt)
        
        # Extract simulation stats
        if sim_current_step is not None:
            nodes_val = sim_current_step.get("nodes_expanded", 0)
            frontier_val = sim_current_step.get("frontier_size", 0)
            depth_val = sim_current_step.get("depth", 0)
            h_val = sim_current_step.get("h_score", 0)
            f_val = sim_current_step.get("f_score", 0)
            dur_val = sim_current_step.get("total_time_ms", 0.0)
            
            dashboard.update_simulation_stats(
                nodes_expanded=nodes_val,
                frontier_size=frontier_val,
                depth=depth_val,
                h_val=h_val,
                f_val=f_val,
                duration_ms=dur_val
            )
        else:
            dashboard.update_simulation_stats(0, 0, 0, 0, 0, 0.0)

        # Update tile target pixel rects
        active_board_state = game.current_state
        tile_size = 580 // board_size
        board_rect = dashboard.board_rect
        start_x = board_rect.x + (board_rect.width - (board_size * tile_size)) // 2
        start_y = board_rect.y + (board_rect.height - (board_size * tile_size)) // 2

        for i, val in enumerate(active_board_state):
            if val != 0:
                row = i // board_size
                col = i % board_size
                tile_rect = (start_x + col * tile_size, start_y + row * tile_size, tile_size, tile_size)
                tile = tiles_ui.get(val)
                if tile:
                    tile.index = i
                    tile.set_target(tile_rect)
                    tile.image = image_tiles.get(val)
                    
        # Lerp update
        for tile in tiles_ui.values():
            tile.update(dt)

        # --- Render ---
        draw_gradient_background(screen)
        
        dashboard.draw(screen)
        
        # Draw Original Image Preview if loaded
        if original_image_surface:
            screen.blit(original_image_surface, dashboard.preview_rect.topleft)
            # Outline
            pygame.draw.rect(screen, BORDER_COLOR, dashboard.preview_rect, 1, border_radius=8)
            
        for tile in tiles_ui.values():
            tile.draw(screen)
            
        if solution_replay_active:
            pygame.draw.rect(screen, PRIMARY_ACCENT, dashboard.board_rect.inflate(10, 10), 2, border_radius=12)
            pygame.draw.rect(screen, SECONDARY_ACCENT, dashboard.board_rect.inflate(14, 14), 1, border_radius=14)
            
        if comparison_modal:
            comparison_modal.draw(screen)
        elif is_finished and victory_modal:
            victory_modal.draw(screen)
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
