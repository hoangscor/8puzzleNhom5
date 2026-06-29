"""
BFS solver for N-Puzzle - optimized using shared utilities.
"""
import collections
import time
from core.search_utils import get_neighbors


def solve(initial_state, goal_state, size=3):
    """
    Solve the puzzle using Breadth-First Search (BFS).
    
    Args:
        initial_state: Starting board state (list)
        goal_state: Target board state (list)
        size: Board dimension
    
    Returns:
        Tuple of (path, nodes_explored, duration_ms) where path is list of move indices
        or None if no solution found.
    """
    start_time = time.time()
    goal_state = tuple(goal_state)
    queue = collections.deque([(tuple(initial_state), [])])
    visited = {tuple(initial_state)}
    nodes_explored = 0
    
    while queue:
        current_state, path = queue.popleft()
        nodes_explored += 1
        
        if current_state == goal_state:
            duration = (time.time() - start_time) * 1000
            return path, nodes_explored, duration
            
        for neighbor_state, move_idx in get_neighbors(current_state, size):
            if neighbor_state not in visited:
                visited.add(neighbor_state)
                queue.append((neighbor_state, path + [move_idx]))
                
    return None, nodes_explored, (time.time() - start_time) * 1000