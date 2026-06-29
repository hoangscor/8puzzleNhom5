"""
Common search utilities for N-Puzzle algorithms.
Shared functions to avoid code duplication.
"""
from typing import List, Tuple, Dict, Optional


def get_neighbors(state: Tuple[int, ...], size: int = 3) -> List[Tuple[Tuple[int, ...], int]]:
    """
    Find all possible neighbor states from the current state.
    
    Args:
        state: Tuple representing current board state
        size: Board dimension (3 for 3x3, 4 for 4x4, etc.)
    
    Returns:
        List of (neighbor_state, move_index) tuples where move_index is the tile
        position that was swapped with the empty slot (0).
    """
    neighbors: List[Tuple[Tuple[int, ...], int]] = []
    empty_idx = state.index(0)
    r, c = empty_idx // size, empty_idx % size
    
    # Empty slot move directions: Up, Down, Left, Right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < size and 0 <= nc < size:
            neighbor_idx = nr * size + nc
            state_list = list(state)
            state_list[empty_idx], state_list[neighbor_idx] = state_list[neighbor_idx], state_list[empty_idx]
            neighbors.append((tuple(state_list), neighbor_idx))
    return neighbors


def build_goal_position_map(goal_state: Tuple[int, ...]) -> Dict[int, int]:
    """
    Build a map from tile value to its goal position for O(1) lookup.
    
    Args:
        goal_state: Tuple representing goal state
    
    Returns:
        Dictionary mapping tile value -> goal index
    """
    return {val: idx for idx, val in enumerate(goal_state) if val != 0}


def manhattan_distance(state: Tuple[int, ...], goal_pos_map: Dict[int, int], size: int = 3) -> int:
    """
    Heuristic function: Manhattan Distance.
    Optimized with O(1) lookup using pre-computed position map.
    
    Args:
        state: Tuple representing current board state
        goal_pos_map: Pre-computed map of tile value -> goal position
        size: Board dimension
    
    Returns:
        Sum of Manhattan distances for all tiles from their goal positions
    """
    distance = 0
    for i, val in enumerate(state):
        if val != 0:
            target_idx = goal_pos_map[val]
            r_curr, c_curr = i // size, i % size
            r_goal, c_goal = target_idx // size, target_idx % size
            distance += abs(r_curr - r_goal) + abs(c_curr - c_goal)
    return distance


def misplaced_tiles(state: Tuple[int, ...], goal_state: Tuple[int, ...], size: int = 3) -> int:
    """
    Heuristic function: Count of misplaced tiles.
    
    Args:
        state: Tuple representing current board state
        goal_state: Tuple representing goal state
        size: Board dimension
    
    Returns:
        Number of tiles not in their goal position (excluding empty tile)
    """
    count = 0
    for i, val in enumerate(state):
        if val != 0 and val != goal_state[i]:
            count += 1
    return count