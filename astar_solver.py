import heapq
import time

def get_neighbors(state, size=3):
    """Find all possible neighbor states from the current state."""
    neighbors = []
    empty_idx = state.index(0)
    r, c = empty_idx // size, empty_idx % size
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < size and 0 <= nc < size:
            neighbor_idx = nr * size + nc
            new_state = list(state)
            new_state[empty_idx], new_state[neighbor_idx] = new_state[neighbor_idx], new_state[empty_idx]
            neighbors.append((tuple(new_state), neighbor_idx))
    return neighbors

def manhattan_distance(state, goal_state, size=3):
    """Heuristic function: Manhattan Distance."""
    distance = 0
    for i in range(len(state)):
        val = state[i]
        if val != 0:
            target_idx = goal_state.index(val)
            r_curr, c_curr = i // size, i % size
            r_goal, c_goal = target_idx // size, target_idx % size
            distance += abs(r_curr - r_goal) + abs(c_curr - c_goal)
    return distance

def solve(initial_state, goal_state):
    """Solve the puzzle using A* Search algorithm."""
    start_time = time.time()
    h_start = manhattan_distance(initial_state, goal_state)
    # (f_score, g_score, state_tuple, path)
    pq = [(h_start, 0, tuple(initial_state), [])]
    visited = {tuple(initial_state): 0}
    nodes_explored = 0
    
    while pq:
        f, g, current_state, path = heapq.heappop(pq)
        nodes_explored += 1
        
        if list(current_state) == goal_state:
            duration = (time.time() - start_time) * 1000
            return path, nodes_explored, duration
            
        for neighbor_state, move_idx in get_neighbors(current_state):
            new_g = g + 1
            if neighbor_state not in visited or new_g < visited[neighbor_state]:
                visited[neighbor_state] = new_g
                h = manhattan_distance(neighbor_state, goal_state)
                heapq.heappush(pq, (new_g + h, new_g, neighbor_state, path + [move_idx]))
                
    return None, nodes_explored, (time.time() - start_time) * 1000
