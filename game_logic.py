import random

class PuzzleGame:
    """
    Main logic class for the N-Puzzle game.
    Manages board state, move validation, and history for undo/redo.
    """
    def __init__(self, size=3):
        self.size = size
        # Goal state: [1, 2, 3, 4, 5, 6, 7, 8, 0]
        self.goal_state = list(range(1, size * size)) + [0]
        self.current_state = list(self.goal_state)
        # Stacks for Undo and Redo operations
        self.history = []
        self.redo_stack = []
        self.shuffle() # Initial shuffle

    def is_solvable(self, state):
        """
        Checks if a board configuration is solvable.
        Uses the inversion count algorithm.
        """
        inversions = 0
        arr = [x for x in state if x != 0]
        # Count pairs where a larger number appears before a smaller number
        for i in range(len(arr)):
            for j in range(i + 1, len(arr)):
                if arr[i] > arr[j]:
                    inversions += 1
        # For a 3x3 grid, it's solvable if the inversion count is even
        return inversions % 2 == 0

    def shuffle(self):
        """Shuffles the board until a solvable state is reached."""
        state = list(self.goal_state)
        while True:
            random.shuffle(state)
            # Must be solvable and not already at goal
            if self.is_solvable(state) and state != self.goal_state:
                break
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
