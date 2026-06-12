"""
GameController class to manage game state and callbacks.
Encapsulates global state from main.py for better maintainability.
"""
import time
from typing import Dict, List, Optional, Callable
import pygame
from game_logic import PuzzleGame
import search_simulators
from image_processor import load_and_split_image
from ui_system import Tile, get_font


class GameController:
    """Manages game state, simulation, and callbacks."""
    
    def __init__(self, board_size=3):
        # Core game state
        self.board_size = board_size
        self.game = PuzzleGame(size=board_size)
        self.is_finished = False
        self.victory_modal = None
        self.comparison_modal = None
        self.image_crops = []
        self.current_image_name = ""
        self.original_image_surface = None
        self.current_image_path = ""
        
        # AI Simulation state
        self.current_algo = "astar_manhattan"
        self.current_speed = "medium"
        self.speed_delays = {"slow": 800, "medium": 300, "fast": 80, "max": 1}
        
        self.sim_generator = None
        self.sim_history = []
        self.sim_playing = False
        self.sim_current_step = None
        self.sim_status = "idle"
        self.sim_initial_state = []
        
        self.solution_path = []
        self.solution_replay_active = False
        self.solution_replay_idx = 0
        self.last_sim_step_time = 0
        
        self.start_play_time = 0
        self.elapsed_play_time = 0
        self.has_started_playing = False
        
        # Drag and Drop state
        self.dragged_tile = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_allowed_dx = 0
        self.drag_allowed_dy = 0
        
        # UI components
        self.tiles_ui = {}
        self.dashboard = None
    
    def reset_game(self):
        """Reset the game to initial state."""
        self.game.reset()
        self.is_finished = False
        self.victory_modal = None
        self.comparison_modal = None
        self.has_started_playing = False
        self.start_play_time = 0
        self.elapsed_play_time = 0
        self.stop_simulation()
        self.recreate_tiles_ui()
    
    def get_tile_image(self, val):
        """Get the correct image crop for a tile value based on the current goal state."""
        if not self.image_crops or val == 0:
            return None
        # Find the position of val in the goal state
        try:
            pos = self.game.goal_state.index(val)
            return self.image_crops[pos]
        except (ValueError, IndexError):
            return None
    
    def stop_simulation(self):
        """Stop any running simulation."""
        self.sim_generator = None
        self.sim_history = []
        self.sim_playing = False
        self.sim_current_step = None
        self.sim_status = "idle"
        self.solution_path = []
        self.solution_replay_active = False
    
    def start_simulation(self):
        """Start a new simulation."""
        self.stop_simulation()
        
        self.sim_initial_state = list(self.game.current_state)
        initial = list(self.game.current_state)
        goal = list(self.game.goal_state)
        # Increase node limit for larger boards
        max_nodes_limit = 50000 if self.board_size > 5 else 10000
        
        if self.current_algo == "bi_astar":
            self.sim_generator = search_simulators.bidirectional_astar_simulator(
                initial, goal, size=self.board_size, max_nodes=max_nodes_limit)
        elif self.current_algo == "idastar":
            self.sim_generator = search_simulators.idastar_simulator(
                initial, goal, size=self.board_size, max_nodes=max_nodes_limit)
        elif self.current_algo == "gbfs":
            self.sim_generator = search_simulators.gbfs_simulator(
                initial, goal, "manhattan", size=self.board_size, max_nodes=max_nodes_limit)
        elif self.current_algo == "astar_manhattan":
            self.sim_generator = search_simulators.astar_simulator(
                initial, goal, "manhattan", size=self.board_size, max_nodes=max_nodes_limit)
        elif self.current_algo == "astar_misplaced":
            self.sim_generator = search_simulators.astar_simulator(
                initial, goal, "misplaced", size=self.board_size, max_nodes=max_nodes_limit)
            
        self.sim_status = "searching"
        self.sim_history = []
        self.solution_path = []
        self.solution_replay_active = False
    
    def run_search_instantly(self):
        """Run search to completion."""
        if not self.sim_generator:
            return
            
        last_step = None
        while True:
            try:
                step = next(self.sim_generator)
                last_step = step
                if step["status"] in ("success", "failed"):
                    break
            except StopIteration:
                break
                
        if last_step:
            self.sim_current_step = last_step
            if last_step["status"] == "success":
                self.sim_status = "success"
                self.solution_path = last_step["path"]
            else:
                self.sim_status = "failed"
    
    def play_pause_sim(self):
        """Play or pause simulation."""
        if self.is_finished:
            return
            
        if self.sim_status == "idle":
            self.start_simulation()
            self.run_search_instantly()
            
        if self.sim_status == "success" and self.solution_path:
            if not self.solution_replay_active:
                self.solution_replay_active = True
                self.solution_replay_idx = 0
                self.game.current_state = list(self.sim_initial_state)
                self.game.history.clear()
                self.game.redo_stack.clear()
                self.has_started_playing = True
                self.start_play_time = time.time()
            self.sim_playing = not self.sim_playing
    
    def step_sim_forward(self):
        """Step simulation forward."""
        if self.is_finished:
            return
            
        if self.sim_status == "idle":
            self.start_simulation()
            self.run_search_instantly()
            
        if self.sim_status == "success" and self.solution_path:
            if not self.solution_replay_active:
                self.solution_replay_active = True
                self.solution_replay_idx = 0
                self.game.current_state = list(self.sim_initial_state)
                self.game.history.clear()
                self.game.redo_stack.clear()
                self.has_started_playing = True
                self.start_play_time = time.time()
                return
                
            if self.solution_replay_idx < len(self.solution_path):
                move_idx = self.solution_path[self.solution_replay_idx]
                self.game.move(move_idx)
                self.solution_replay_idx += 1
                if self.game.is_goal():
                    self.trigger_victory()
    
    def step_sim_backward(self):
        """Step simulation backward."""
        if self.is_finished or not self.solution_replay_active:
            return
            
        if self.solution_replay_idx > 0:
            self.solution_replay_idx -= 1
            self.game.undo()
    
    def trigger_victory(self):
        """Trigger victory modal."""
        from ui_system import Modal
        self.is_finished = True
        self.victory_modal = Modal(
            "Bạn đã giải thành công!",
            "Chơi lại", self.reset_game,
            "Không", self.close_modal
        )
    
    def close_modal(self):
        """Close victory modal."""
        self.victory_modal = None
    
    def undo(self):
        """Undo last move."""
        if self.is_finished or self.sim_status == "searching" or self.sim_playing or self.solution_replay_active:
            return
        self.game.undo()
    
    def redo(self):
        """Redo last move."""
        if self.is_finished or self.sim_status == "searching" or self.sim_playing or self.solution_replay_active:
            return
        self.game.redo()
    
    def change_size(self, new_size):
        """Change board size."""
        if self.board_size == new_size:
            return
        self.board_size = new_size
        current_preset = self.game.goal_preset
        self.game = PuzzleGame(size=self.board_size)
        self.game.set_goal_preset(current_preset)
        self.stop_simulation()
        
        if self.current_image_path:
            tile_size = 580 // self.board_size
            new_crops, name = load_and_split_image(self.current_image_path, tile_size, self.board_size)
            if new_crops:
                self.image_crops = new_crops
                self.current_image_name = name
        else:
            self.image_crops = []
            self.current_image_name = ""
            
        self.recreate_tiles_ui()
    
    def recreate_tiles_ui(self):
        """Recreate tile UI elements."""
        from ui_system import Tile, get_font
        
        self.tiles_ui.clear()
        
        if not self.dashboard:
            return
            
        tile_size = 580 // self.board_size
        board_rect = self.dashboard.board_rect
        start_x = board_rect.x + (board_rect.width - (self.board_size * tile_size)) // 2
        start_y = board_rect.y + (board_rect.height - (self.board_size * tile_size)) // 2
        
        radius = max(2, 8 - (self.board_size - 3))
        font_size = max(12, 42 - (self.board_size - 3) * 5)
        
        for val in range(1, self.board_size * self.board_size):
            tile = Tile(None, val, 0, radius=radius)
            tile.font = get_font(font_size, bold=True)
            self.tiles_ui[val] = tile
            
        active_board_state = self.game.current_state
        for i, val in enumerate(active_board_state):
            if val != 0:
                row = i // self.board_size
                col = i % self.board_size
                tile_rect = (start_x + col * tile_size, start_y + row * tile_size, tile_size, tile_size)
                tile = self.tiles_ui.get(val)
                if tile:
                    tile.index = i
                    tile.set_target(tile_rect)
    
    def get_callbacks(self):
        """Get callback dictionary for UI."""
        return {
            'insert_image': lambda: self._insert_image(),
            'reset_game': lambda: self.reset_game(),
            'select_algorithm': lambda a: self._select_algorithm(a),
            'select_speed': lambda s: self._select_speed(s),
            'play_pause': lambda: self.play_pause_sim(),
            'step_forward': lambda: self.step_sim_forward(),
            'step_backward': lambda: self.step_sim_backward(),
            'stop_simulation': lambda: self.stop_simulation(),
            'change_size': lambda s: self.change_size(s),
            'compare_solvers': lambda: self._run_compare_solvers(),
            'undo': lambda: self.undo(),
            'redo': lambda: self.redo(),
            'export_log': lambda: self._export_solution_log(),
            'change_goal_preset': lambda p: self._change_goal_preset(p)
        }
    
    def _select_algorithm(self, algo_name):
        self.current_algo = algo_name
        self.stop_simulation()
    
    def _select_speed(self, speed_name):
        self.current_speed = speed_name
    
    def _change_goal_preset(self, new_preset):
        if self.game.goal_preset == new_preset:
            return
        self.game.set_goal_preset(new_preset)
        self.is_finished = False
        self.victory_modal = None
        self.comparison_modal = None
        self.has_started_playing = False
        self.start_play_time = 0
        self.elapsed_play_time = 0
        self.stop_simulation()
        self.recreate_tiles_ui()
    
    def _insert_image(self):
        import tkinter as tk
        from tkinter import filedialog, messagebox
        
        if self.is_finished or self.sim_status == "searching" or self.sim_playing or self.solution_replay_active:
            return
        file_path = filedialog.askopenfilename(
            title="Chọn ảnh cho Puzzle",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.svg"), ("All files", "*.*")]
        )
        if file_path:
            tile_size = 580 // self.board_size
            new_crops, name = load_and_split_image(file_path, tile_size, self.board_size)
            if new_crops:
                self.image_crops = new_crops
                self.current_image_name = name
                self.current_image_path = file_path
                
                try:
                    raw_surf = pygame.image.load(file_path).convert()
                    self.original_image_surface = pygame.transform.smoothscale(raw_surf, (200, 160))
                except Exception as e:
                    print(f"Error loading preview: {e}")
                    self.original_image_surface = None
    
    def _run_compare_solvers(self):
        from tkinter import messagebox
        
        # Warn for large boards
        if self.board_size >= 8:
            if not messagebox.askyesno("Cảnh báo", "Bảng 8x8 có thể mất nhiều thời gian để so sánh. Tiếp tục?"):
                return
        
        self.stop_simulation()
        
        initial = list(self.game.current_state)
        goal = list(self.game.goal_state)
        results = []
        max_nodes = 50000 if self.board_size > 5 else 10000
        
        solvers = [
            ("bidirectional_astar_simulator", "Bi-directional A*"),
            ("idastar_simulator", "Iterative Deepening A* (IDA*)"),
            ("gbfs_simulator", "Greedy Best-First (GBFS)"),
            ("astar_simulator", "A* (Manhattan Distance)", "manhattan"),
            ("astar_simulator", "A* (Misplaced Tiles)", "misplaced")
        ]
        
        for solver_info in solvers:
            if len(solver_info) == 3:
                algo_key, algo_name, heuristic = solver_info
                try:
                    gen = getattr(search_simulators, algo_key)(initial, goal, heuristic, size=self.board_size, max_nodes=max_nodes)
                except Exception as e:
                    print(f"Error in {algo_name}: {e}")
                    results.append({"name": algo_name, "nodes": "Error", "moves": "N/A", "time": "N/A"})
                    continue
            else:
                algo_key, algo_name = solver_info
                try:
                    gen = getattr(search_simulators, algo_key)(initial, goal, size=self.board_size, max_nodes=max_nodes)
                except Exception as e:
                    print(f"Error in {algo_name}: {e}")
                    results.append({"name": algo_name, "nodes": "Error", "moves": "N/A", "time": "N/A"})
                    continue
                    
            try:
                res = self._run_generator_to_end(gen)
                if res is None:
                    status = "failed"
                    nodes = 0
                    path = []
                    time_ms = 0.0
                else:
                    status = res.get("status", "failed")
                    nodes = res.get("nodes_expanded", 0)
                    path = res.get("path", [])
                    time_ms = res.get("total_time_ms", 0.0)
                    
                results.append({
                    "name": algo_name,
                    "nodes": f"{nodes:,}" if status == "success" else "10,000+",
                    "moves": f"{len(path)}" if status == "success" else "N/A",
                    "time": f"{time_ms:.1f}" if status == "success" else "Limit"
                })
            except Exception as e:
                print(f"Error processing {algo_name}: {e}")
                results.append({"name": algo_name, "nodes": "Error", "moves": "N/A", "time": "N/A"})
        
        from ui_system import ComparisonModal
        self.comparison_modal = ComparisonModal(results, self._close_compare_solvers)
    
    def _run_generator_to_end(self, gen):
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
    
    def _close_compare_solvers(self):
        self.comparison_modal = None
    
    def _export_solution_log(self):
        from tkinter import messagebox, filedialog
        
        if not self.solution_path:
            messagebox.showwarning("Cảnh báo", "Chưa có lời giải nào được tìm thấy. Hãy chạy thuật toán trước!")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Lưu log bước chạy",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"log_giai_{self.current_algo}_{self.board_size}x{self.board_size}.txt"
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
                f.write(f"Thuật toán sử dụng: {algo_display_names.get(self.current_algo, self.current_algo)}\n")
                f.write(f"Kích thước bàn cờ: {self.board_size}x{self.board_size}\n")
                f.write(f"Trạng thái bắt đầu: {self.sim_initial_state}\n")
                f.write(f"Trạng thái đích: {self.game.goal_state}\n")
                f.write(f"Tổng số bước di chuyển: {len(self.solution_path)}\n\n")
                
                f.write("Danh sách các bước di chuyển chi tiết:\n")
                f.write("--------------------------------------------------\n")
                
                curr_state = list(self.sim_initial_state)
                size = self.board_size
                for step_no, move_idx in enumerate(self.solution_path, 1):
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
                    
                    curr_state[empty_idx], curr_state[move_idx] = curr_state[move_idx], curr_state[empty_idx]
                    
                f.write("--------------------------------------------------\n")
                f.write("Trạng thái kết thúc: Đã đạt mục tiêu!\n")
                f.write("==================================================\n")
                
            messagebox.showinfo("Thành công", f"Đã xuất log bước chạy thành công ra file:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể ghi log ra file: {e}")