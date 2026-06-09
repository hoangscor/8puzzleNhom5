import random

class PuzzleGame:
    """
    Main logic class for the N-Puzzle game.
    Manages board state, move validation, and history for undo/redo.
    """
    def __init__(self, size=3):
        self.size = size
        # Goal state configurations
        self.goal_preset = "default"
        self.goal_state = list(range(1, size * size)) + [0]
        self.current_state = list(self.goal_state)
        # Stacks for Undo and Redo operations
        self.history = []
        self.redo_stack = []
        self.shuffle() # Initial shuffle

    def set_goal_preset(self, preset_name):
        self.goal_preset = preset_name
        if preset_name == "default":
            self.goal_state = list(range(1, self.size * self.size)) + [0]
        elif preset_name == "spiral":
            self.goal_state = self.generate_spiral_goal()
        elif preset_name == "columns":
            self.goal_state = self.generate_columns_goal()
        self.shuffle()

    def generate_spiral_goal(self):
        size = self.size
        grid = [[0] * size for _ in range(size)]
        dr = [0, 1, 0, -1]
        dc = [1, 0, -1, 0]
        r, c, di = 0, 0, 0
        
        for val in range(1, size * size):
            grid[r][c] = val
            nr, nc = r + dr[di], c + dc[di]
            if 0 <= nr < size and 0 <= nc < size and grid[nr][nc] == 0:
                r, c = nr, nc
            else:
                di = (di + 1) % 4
                r, c = r + dr[di], c + dc[di]
                
        flat = []
        for row in grid:
            flat.extend(row)
        return flat

    def generate_columns_goal(self):
        size = self.size
        flat = [0] * (size * size)
        val = 1
        for col in range(size):
            for row in range(size):
                if col == size - 1 and row == size - 1:
                    flat[row * size + col] = 0
                else:
                    flat[row * size + col] = val
                    val += 1
        return flat

    def is_solvable_standard(self, state):
        """Checks if a board configuration is solvable relative to standard [1..N, 0] goal."""
        inversions = 0
        arr = [x for x in state if x != 0]
        for i in range(len(arr)):
            for j in range(i + 1, len(arr)):
                if arr[i] > arr[j]:
                    inversions += 1
                    
        if self.size % 2 == 1:
            return inversions % 2 == 0
        else:
            empty_idx = state.index(0)
            empty_row = empty_idx // self.size
            row_from_bottom = self.size - empty_row
            
            if row_from_bottom % 2 == 0:
                return inversions % 2 == 1
            else:
                return inversions % 2 == 0

    def is_solvable(self, state):
        """Checks if a board state is solvable relative to the current goal state."""
        return self.is_solvable_standard(state) == self.is_solvable_standard(self.goal_state)

    def shuffle(self):
        """Shuffles the board until a solvable state is reached."""
        if self.size == 3:
            state = list(self.goal_state)
            while True:
                random.shuffle(state)
                # Must be solvable and not already at goal
                if self.is_solvable(state) and state != self.goal_state:
                    break
            self.current_state = state
        else:
            # For 4x4 and 5x5, we shuffle by making a limited number of random moves
            # from the goal state. This guarantees it's solvable and can be solved
            # by A*, Bi-A*, and IDA* within the node limits (10,000 nodes).
            state = list(self.goal_state)
            steps = 30 if self.size == 4 else 25
            
            def get_neighbors_state(s):
                neighbors = []
                empty_idx = s.index(0)
                r, c = empty_idx // self.size, empty_idx % self.size
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size:
                        n_idx = nr * self.size + nc
                        new_s = list(s)
                        new_s[empty_idx], new_s[n_idx] = new_s[n_idx], new_s[empty_idx]
                        neighbors.append(new_s)
                return neighbors
                
            last_state = list(state)
            for _ in range(steps):
                nb = get_neighbors_state(state)
                # Avoid immediately moving back to the last state if possible
                choices = [n for n in nb if n != last_state]
                if not choices:
                    choices = nb
                last_state = list(state)
                state = random.choice(choices)
                
            self.current_state = state
            
        self.history = []
        self.redo_stack = []

    def get_empty_pos(self):
        """Returns the row and column of the empty tile (0)."""
        idx = self.current_state.index(0)
        return idx // self.size, idx % self.size

    def move(self, tile_index, record_history=True):
        """Attempts to move a tile if it's adjacent to the empty slot."""
        empty_idx = self.current_state.index(0)
        
        # Convert 1D index to 2D coordinates (row, col)
        r_empty, c_empty = empty_idx // self.size, empty_idx % self.size
        r_tile, c_tile = tile_index // self.size, tile_index % self.size
        
        # Move condition: Manhattan distance must be exactly 1
        if abs(r_empty - r_tile) + abs(c_empty - c_tile) == 1:
            if record_history:
                # Save current state to history before moving
                self.history.append(list(self.current_state))
                # Clear redo stack when a new move is made
                self.redo_stack.clear()

            # Swap empty slot with selected tile
            self.current_state[empty_idx], self.current_state[tile_index] = \
                self.current_state[tile_index], self.current_state[empty_idx]
            return True
        return False

    def undo(self):
        """Reverts to the previous state."""
        if self.history:
            self.redo_stack.append(list(self.current_state))
            self.current_state = self.history.pop()
            return True
        return False

    def redo(self):
        """Re-applies a previously undone move."""
        if self.redo_stack:
            self.history.append(list(self.current_state))
            self.current_state = self.redo_stack.pop()
            return True
        return False

    def is_goal(self):
        """Checks if the board current state matches the goal state."""
        return self.current_state == self.goal_state

    def reset(self):
        """Resets the game by reshuffling the board."""
        self.shuffle()

    def get_progress(self):
        """Returns the progress percentage and number of correct tiles."""
        correct = 0
        total = self.size * self.size - 1  # Excluding the empty slot (0)
        for i in range(len(self.current_state)):
            val = self.current_state[i]
            if val != 0 and val == self.goal_state[i]:
                correct += 1
        pct = int((correct / total) * 100) if total > 0 else 0
        return pct, correct, total
