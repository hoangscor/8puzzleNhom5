import collections
import time

def get_neighbors(state, size=3):
    """Find all possible neighbor states from the current state."""
    neighbors = []
    empty_idx = state.index(0)
    r, c = empty_idx // size, empty_idx % size
    
    # Empty slot move directions: Up, Down, Left, Right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < size and 0 <= nc < size:
            neighbor_idx = nr * size + nc
            new_state = list(state)
            new_state[empty_idx], new_state[neighbor_idx] = new_state[neighbor_idx], new_state[empty_idx]
            neighbors.append((tuple(new_state), neighbor_idx))
    return neighbors

def solve(initial_state, goal_state):
    """Solve the puzzle using Breadth-First Search (BFS)."""
    start_time = time.time()
    queue = collections.deque([(tuple(initial_state), [])])
    visited = {tuple(initial_state)}
    nodes_explored = 0
    
    while queue:
        current_state, path = queue.popleft()
        nodes_explored += 1
        
        if list(current_state) == goal_state:
            duration = (time.time() - start_time) * 1000
            return path, nodes_explored, duration
        
        for neighbor_state, move_idx in get_neighbors(current_state):
            if neighbor_state not in visited:
                visited.add(neighbor_state)
                queue.append((neighbor_state, path + [move_idx]))
                
    return None, nodes_explored, (time.time() - start_time) * 1000
