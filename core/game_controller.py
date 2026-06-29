"""
GameController class to manage game state and callbacks.
Encapsulates global state from main.py for better maintainability.
"""
import time
import json
import os
from typing import Dict, List, Optional, Callable
import pygame
from core.game_logic import PuzzleGame
import solvers.search_simulators
from core.image_processor import load_and_split_image
from ui.system import Tile, get_font


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
        self.initial_game_state = list(self.game.current_state)
        
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
        
        # Optimal moves comparison
        self.optimal_move_count = None
        
        # Drag and Drop state
        self.dragged_tile = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_allowed_dx = 0
        self.drag_allowed_dy = 0
        
        # UI components
        self.tiles_ui = {}
        self.dashboard = None
        self.search_log = []

    def _notify(self, message, kind="info"):
        """Show a short UI notification if the dashboard is available."""
        if self.dashboard and hasattr(self.dashboard, "show_notification"):
            self.dashboard.show_notification(message, kind)

    def _is_system_running(self):
        """Return True while solver/search replay is in an active or locked state."""
        return (
            self.sim_status == "searching"
            or self.sim_playing
            or self.solution_replay_active
            or getattr(self, "_compare_running", False)
        )

    def _warn_system_running(self):
        self._notify("System is running. Stop it before changing settings.", "warning")
    
    def reset_game(self):
        """Reset the game to initial state."""
        self.game.reset()
        self.is_finished = False
        self.victory_modal = None
        self.comparison_modal = None
        self.has_started_playing = False
        self.start_play_time = 0
        self.elapsed_play_time = 0
        self.optimal_move_count = None
        self.initial_game_state = list(self.game.current_state)
        self.stop_simulation()
        self.recreate_tiles_ui()
    
    def save_game(self, slot=0):
        """Save game state to a slot (0-4)."""
        try:
            saves_dir = os.path.join(os.path.dirname(__file__), 'saves')
            os.makedirs(saves_dir, exist_ok=True)
            
            save_data = {
                'board_size': self.board_size,
                'current_state': list(self.game.current_state),
                'goal_state': list(self.game.goal_state),
                'current_algo': self.current_algo,
                'current_speed': self.current_speed,
                'moves_count': len(self.game.history),
                'elapsed_time': self.elapsed_play_time,
                'has_started_playing': self.has_started_playing,
                'initial_game_state': list(self.initial_game_state),
                'image_name': self.current_image_name,
                'image_path': self.current_image_path,
            }
            
            save_path = os.path.join(saves_dir, f'save_slot_{slot}.json')
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def load_game(self, slot=0):
        """Load game state from a slot (0-4)."""
        try:
            saves_dir = os.path.join(os.path.dirname(__file__), 'saves')
            save_path = os.path.join(saves_dir, f'save_slot_{slot}.json')
            
            if not os.path.exists(save_path):
                return False
            
            with open(save_path, 'r') as f:
                save_data = json.load(f)
            
            # Restore game state
            self.board_size = save_data['board_size']
            self.game = PuzzleGame(size=self.board_size)
            self.game.current_state = list(save_data['current_state'])
            self.game.goal_state = list(save_data['goal_state'])
            self.game.history.clear()
            self.game.redo_stack.clear()
            
            self.current_algo = save_data['current_algo']
            self.current_speed = save_data['current_speed']
            self.elapsed_play_time = save_data.get('elapsed_time', 0)
            self.has_started_playing = save_data.get('has_started_playing', False)
            self.initial_game_state = list(save_data.get('initial_game_state', self.game.current_state))
            
            self.current_image_name = save_data.get('image_name', '')
            self.current_image_path = save_data.get('image_path', '')
            
            self.is_finished = False
            self.victory_modal = None
            self.comparison_modal = None
            self.optimal_move_count = None
            self.stop_simulation()
            
            # Reload image if path exists
            if self.current_image_path and os.path.exists(self.current_image_path):
                tile_size = 480 // self.board_size
                self.image_crops, _ = load_and_split_image(
                    self.current_image_path,
                    tile_size,
                    self.board_size
                )
                if self.image_crops:
                    try:
                        raw_surf = pygame.image.load(self.current_image_path).convert()
                        self.original_image_surface = pygame.transform.smoothscale(raw_surf, (200, 160))
                    except Exception:
                        self.original_image_surface = None
                else:
                    self.image_crops = []
                    self.original_image_surface = None
            else:
                self.image_crops = []
            
            self.recreate_tiles_ui()
            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False
    
    def get_save_slots(self):
        """Get list of available save slots with metadata."""
        saves_dir = os.path.join(os.path.dirname(__file__), 'saves')
        slots = []
        
        for i in range(5):
            save_path = os.path.join(saves_dir, f'save_slot_{i}.json')
            if os.path.exists(save_path):
                try:
                    with open(save_path, 'r') as f:
                        data = json.load(f)
                    slots.append({
                        'slot': i,
                        'board_size': data.get('board_size', '?'),
                        'moves': data.get('moves_count', 0),
                        'time': data.get('elapsed_time', 0),
                        'image': data.get('image_name', 'Unknown')
                    })
                except:
                    slots.append({'slot': i, 'empty': True})
            else:
                slots.append({'slot': i, 'empty': True})
        
        return slots
    
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
        elif self.current_algo == "compare":
            pass
            
        self.sim_status = "searching"
        self.sim_history = []
        self.solution_path = []
        self.solution_replay_active = False
    
    def run_search_instantly(self):
        """Run search to completion."""
        if not self.sim_generator:
            return
            
        self.search_log = []
        algo_names = {
            "bi_astar": "Bi-A*", "idastar": "IDA*", "gbfs": "GBFS",
            "astar_manhattan": "A* Manhattan", "astar_misplaced": "A* Misplaced"
        }
        algo_display = algo_names.get(self.current_algo, self.current_algo)
        self.search_log.append(f"Starting {algo_display} search ({self.board_size}x{self.board_size})")
        self.search_log.append(f"Initial: {self.sim_initial_state}")
        self.search_log.append(f"Goal:    {self.game.goal_state}")
        self.search_log.append("---")
        
        last_step = None
        step_count = 0
        while True:
            try:
                step = next(self.sim_generator)
                last_step = step
                if step["status"] == "searching":
                    step_count += 1
                    nodes = step.get("nodes_expanded", 0)
                    frontier = step.get("frontier_size", 0)
                    depth = step.get("depth", 0)
                    h = step.get("h_score", 0)
                    f = step.get("f_score", 0)
                    self.search_log.append(
                        f"[{nodes:>5}] d={depth} h={h} f={f} frontier={frontier}"
                    )
                elif step["status"] == "success":
                    path_len = len(step.get("path", []))
                    nodes = step.get("nodes_expanded", 0)
                    dur = step.get("total_time_ms", 0)
                    self.search_log.append("---")
                    self.search_log.append(f"SOLVED in {dur:.1f}ms")
                    self.search_log.append(f"Nodes explored: {nodes:,}")
                    self.search_log.append(f"Solution length: {path_len} moves")
                elif step["status"] == "failed":
                    nodes = step.get("nodes_expanded", 0)
                    self.search_log.append("---")
                    self.search_log.append(f"FAILED (explored {nodes:,} nodes)")
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
                if hasattr(self, 'sound_manager'):
                    self.sound_manager.play("move")
                if self.game.is_goal():
                    if hasattr(self, 'sound_manager'):
                        self.sound_manager.play("victory")
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
        from ui.system import Modal
        self.is_finished = True
        self._compute_optimal_moves()
        self._save_high_score()
        self.victory_modal = Modal(
            "Puzzle solved successfully!",
            "Play Again", self.reset_game,
            "No", self.close_modal
        )
    
    def _get_high_score_key(self):
        return f"{self.board_size}x{self.board_size}_{self.game.goal_preset}"
    
    def _load_high_scores(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "high_scores.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_high_score(self):
        if not self.has_started_playing or len(self.game.history) == 0:
            return
        scores = self._load_high_scores()
        key = self._get_high_score_key()
        player_moves = len(self.game.history)
        player_time = self.elapsed_play_time
        
        if key not in scores:
            scores[key] = {"best_moves": player_moves, "best_time": player_time}
        else:
            if player_moves < scores[key]["best_moves"]:
                scores[key] = {"best_moves": player_moves, "best_time": player_time}
        
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "high_scores.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(scores, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def get_high_score(self):
        scores = self._load_high_scores()
        key = self._get_high_score_key()
        return scores.get(key, None)
    
    def _compute_optimal_moves(self):
        """Compute optimal move count using A* solver."""
        import solvers.astar_solver
        initial = self.initial_game_state if self.initial_game_state else self.sim_initial_state
        if not initial:
            return
        try:
            path, _, _ = astar_solver.solve(initial, self.game.goal_state, self.board_size)
            self.optimal_move_count = len(path) if path else None
        except Exception:
            self.optimal_move_count = None
    
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
        if self._is_system_running():
            self._warn_system_running()
            return
        if self.board_size == new_size:
            return
        self.board_size = new_size
        current_preset = self.game.goal_preset
        self.game = PuzzleGame(size=self.board_size)
        self.game.set_goal_preset(current_preset)
        self.stop_simulation()
        
        if self.current_image_path:
            tile_size = 480 // self.board_size
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
        from ui.system import Tile, get_font
        
        self.tiles_ui.clear()
        
        if not self.dashboard:
            return
            
        tile_size = 480 // self.board_size
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
            'change_goal_preset': lambda p: self._change_goal_preset(p),
            'toggle_sound': lambda: self._toggle_sound(),
            'set_custom_goal': lambda: self._open_custom_goal_dialog(),
            'save_game': lambda: self._open_save_dialog(),
            'load_game': lambda: self._open_load_dialog()
        }
    
    def _toggle_sound(self):
        if hasattr(self, 'sound_manager'):
            return self.sound_manager.toggle()
        return True
    
    def _open_save_dialog(self):
        """Save game directly to slot 0."""
        if self.save_game(slot=0):
            self._notify("Game saved successfully.", "success")
        else:
            self._notify("Save failed.", "error")
    
    def _open_load_dialog(self):
        """Load game directly from slot 0."""
        if self._is_system_running():
            self._warn_system_running()
            return
        if self.load_game(slot=0):
            self._notify("Game loaded successfully.", "success")
        else:
            self._notify("No saved game found.", "warning")
    
    def _open_custom_goal_dialog(self):
        """Custom goal: cycle through preset goals instead."""
        if self._is_system_running():
            self._warn_system_running()
            return
        presets = ["default", "spiral", "columns"]
        current_idx = presets.index(self.game.goal_preset) if self.game.goal_preset in presets else 0
        next_idx = (current_idx + 1) % len(presets)
        self._change_goal_preset(presets[next_idx])
    
    def _select_algorithm(self, algo_name):
        if self._is_system_running():
            self._warn_system_running()
            return
        algo_map = {"Bi-A*": "bi_astar", "IDA*": "idastar", "A* Manhattan": "astar_manhattan",
                    "A* misplaced": "astar_misplaced", "GBFS": "gbfs", "Compare all": "compare"}
        self.current_algo = algo_map.get(algo_name, algo_name)
        self.stop_simulation()
    
    def _select_speed(self, speed_name):
        if self._is_system_running():
            self._warn_system_running()
            return
        self.current_speed = speed_name
    
    def _change_goal_preset(self, new_preset):
        if self._is_system_running():
            self._warn_system_running()
            return
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
        from tkinter import filedialog
        import threading
        
        if self.is_finished or self.sim_status == "searching" or self.sim_playing or self.solution_replay_active:
            return
        
        def open_file_dialog():
            temp_root = tk.Tk()
            temp_root.withdraw()
            temp_root.attributes('-topmost', True)
            path = filedialog.askopenfilename(
                parent=temp_root,
                title="Choose Puzzle Image",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")]
            )
            temp_root.destroy()
            if path:
                self._apply_image(path)
        
        threading.Thread(target=open_file_dialog, daemon=True).start()
    
    def _apply_image(self, file_path):
        tile_size = 480 // self.board_size
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
        import threading
        
        self.stop_simulation()
        self.comparison_modal = None
        self._compare_running = True
        
        initial = list(self.game.current_state)
        goal = list(self.game.goal_state)
        board_size = self.board_size
        max_nodes = 50000 if board_size > 5 else 10000
        
        solvers = [
            ("bidirectional_astar_simulator", "Bi-directional A*"),
            ("idastar_simulator", "Iterative Deepening A* (IDA*)"),
            ("gbfs_simulator", "Greedy Best-First (GBFS)"),
            ("astar_simulator", "A* (Manhattan Distance)", "manhattan"),
            ("astar_simulator", "A* (Misplaced Tiles)", "misplaced")
        ]
        
        def run_in_background():
            results = []
            for solver_info in solvers:
                if not self._compare_running:
                    return
                if len(solver_info) == 3:
                    algo_key, algo_name, heuristic = solver_info
                    try:
                        gen = getattr(search_simulators, algo_key)(initial, goal, heuristic, size=board_size, max_nodes=max_nodes, for_compare=True)
                    except Exception as e:
                        results.append({"name": algo_name, "nodes": "Error", "moves": "N/A", "time": "N/A"})
                        continue
                else:
                    algo_key, algo_name = solver_info
                    try:
                        gen = getattr(search_simulators, algo_key)(initial, goal, size=board_size, max_nodes=max_nodes, for_compare=True)
                    except Exception as e:
                        results.append({"name": algo_name, "nodes": "Error", "moves": "N/A", "time": "N/A"})
                        continue
                
                try:
                    res = self._run_generator_to_end(gen)
                    if res is None:
                        results.append({"name": algo_name, "nodes": "10,000+", "moves": "N/A", "time": "Limit"})
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
                    results.append({"name": algo_name, "nodes": "Error", "moves": "N/A", "time": "N/A"})
            
            self._compare_results = results
            self._compare_running = False
        
        self._compare_results = None
        self._compare_thread = threading.Thread(target=run_in_background, daemon=True)
        self._compare_thread.start()
    
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
    
    def _run_solver_fast(self, solver_func, initial, goal, size, max_nodes):
        """Run a solver generator to completion, skipping expensive intermediate state."""
        last_step = None
        try:
            for step in solver_func:
                last_step = step
                if step["status"] in ("success", "failed"):
                    break
        except Exception:
            pass
        return last_step
    
    def _close_compare_solvers(self):
        self._compare_running = False
        self.comparison_modal = None
    
    def _export_solution_log(self):
        import threading
        
        if not self.solution_path:
            return
        
        def generate_log_content():
            algo_display_names = {
                "bi_astar": "Bi-directional A* (A* hai chieu)",
                "idastar": "Iterative Deepening A* (IDA*)",
                "gbfs": "Greedy Best-First Search (GBFS)",
                "astar_manhattan": "A* (Manhattan Distance)",
                "astar_misplaced": "A* (Misplaced Tiles)"
            }
            lines = []
            lines.append("==================================================")
            lines.append("             N-PUZZLE SOLUTION LOG")
            lines.append("==================================================\n")
            lines.append(f"Thuat toan: {algo_display_names.get(self.current_algo, self.current_algo)}")
            lines.append(f"Kich thuoc ban co: {self.board_size}x{self.board_size}")
            lines.append(f"Trang thai bat dau: {self.sim_initial_state}")
            lines.append(f"Trang thai dich: {self.game.goal_state}")
            lines.append(f"Tong so buoc di chuyen: {len(self.solution_path)}\n")
            lines.append("Danh sach cac buoc di chuyen chi tiet:")
            lines.append("--------------------------------------------------")
            
            curr_state = list(self.sim_initial_state)
            size = self.board_size
            for step_no, move_idx in enumerate(self.solution_path, 1):
                empty_idx = curr_state.index(0)
                r_empty, c_empty = empty_idx // size, empty_idx % size
                r_tile, c_tile = move_idx // size, move_idx % size
                
                direction = ""
                if r_tile < r_empty: direction = "XUONG (DOWN)"
                elif r_tile > r_empty: direction = "LEN (UP)"
                elif c_tile < c_empty: direction = "SANG PHAI (RIGHT)"
                elif c_tile > c_empty: direction = "SANG TRAI (LEFT)"
                
                tile_val = curr_state[move_idx]
                lines.append(f"Buoc {step_no:02d}: Di chuyen o so {tile_val} {direction} (tu vi tri {move_idx} sang o trong {empty_idx})")
                
                curr_state[empty_idx], curr_state[move_idx] = curr_state[move_idx], curr_state[empty_idx]
            
            lines.append("--------------------------------------------------")
            lines.append("Trang thai ket thuc: Da dat muc tieu!")
            lines.append("==================================================")
            return "\n".join(lines)
        
        content = generate_log_content()
        default_name = f"log_giai_{self.current_algo}_{self.board_size}x{self.board_size}.txt"
        
        def open_save_dialog():
            import tkinter as tk
            from tkinter import filedialog
            temp_root = tk.Tk()
            temp_root.withdraw()
            temp_root.attributes('-topmost', True)
            path = filedialog.asksaveasfilename(
                parent=temp_root,
                title="Save Solution Log",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=default_name
            )
            temp_root.destroy()
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
        
        threading.Thread(target=open_save_dialog, daemon=True).start()
