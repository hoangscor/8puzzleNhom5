"""
A* solver for N-Puzzle - optimized using shared utilities.
"""
import heapq
import time
from core.search_utils import get_neighbors, manhattan_distance, build_goal_position_map


def solve(initial_state, goal_state, size=3):
    """
    Solve the puzzle using A* Search algorithm.
    
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
    goal_pos_map = build_goal_position_map(goal_state)
    
    h_start = manhattan_distance(tuple(initial_state), goal_pos_map, size)
    # (f_score, g_score, state_tuple, path)
    pq = [(h_start, 0, tuple(initial_state), [])]
    visited = {tuple(initial_state): 0}
    nodes_explored = 0
    
    while pq:
        f, g, current_state, path = heapq.heappop(pq)
        nodes_explored += 1
        
        if current_state == goal_state:
            duration = (time.time() - start_time) * 1000
            return path, nodes_explored, duration
            
        for neighbor_state, move_idx in get_neighbors(current_state, size):
            new_g = g + 1
            if neighbor_state not in visited or new_g < visited[neighbor_state]:
                visited[neighbor_state] = new_g
                h = manhattan_distance(neighbor_state, goal_pos_map, size)
                heapq.heappush(pq, (new_g + h, new_g, neighbor_state, path + [move_idx]))
                
    return None, nodes_explored, (time.time() - start_time) * 1000