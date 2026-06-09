import collections
import heapq
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

def manhattan_distance(state, goal_state, size=3):
    """Heuristic function: Manhattan Distance."""
    distance = 0
    for i in range(len(state)):
        val = state[i]
        if val != 0:
            target_idx = goal_state.index(val)
            r_curr, c_curr = i // size, i % size
            r_goal, c_goal = target_idx // size, target_idx % size
            distance += abs(r_curr - r_goal) + abs(c_goal - c_curr)
    return distance

def misplaced_tiles(state, goal_state, size=3):
    """Heuristic function: Count of misplaced tiles."""
    count = 0
    for i in range(len(state)):
        val = state[i]
        if val != 0 and val != goal_state[i]:
            count += 1
    return count

def astar_simulator(initial_state, goal_state, heuristic_name="manhattan", size=3, max_nodes=10000):
    """Solve the puzzle using A* Search algorithm yielding state for visualization."""
    start_time = time.time()
    
    def get_h(state):
        if heuristic_name == "manhattan":
            return manhattan_distance(state, goal_state, size)
        else:
            return misplaced_tiles(state, goal_state, size)
            
    h_start = get_h(initial_state)
    counter = 0
    pq = [(h_start, 0, h_start, counter, tuple(initial_state), [])]
    visited = {tuple(initial_state): 0}
    nodes_expanded = 0
    
    while pq:
        if nodes_expanded >= max_nodes:
            break
            
        f, g, h, _, current_state, path = heapq.heappop(pq)
        nodes_expanded += 1
        
        state_info = {
            "status": "searching",
            "current_state": list(current_state),
            "frontier_size": len(pq),
            "explored_size": len(visited),
            "depth": g,
            "h_score": h,
            "f_score": f,
            "nodes_expanded": nodes_expanded,
            "path_to_current": path
        }
        
        if list(current_state) == goal_state:
            duration = (time.time() - start_time) * 1000
            state_info["status"] = "success"
            state_info["path"] = path
            state_info["total_time_ms"] = duration
            yield state_info
            return
            
        yield state_info
        
        for neighbor_state, move_idx in get_neighbors(current_state, size):
            new_g = g + 1
            if neighbor_state not in visited or new_g < visited[neighbor_state]:
                visited[neighbor_state] = new_g
                new_h = get_h(neighbor_state)
                counter += 1
                heapq.heappush(pq, (new_g + new_h, new_g, new_h, counter, neighbor_state, path + [move_idx]))
                
    yield {
        "status": "failed",
        "nodes_expanded": nodes_expanded,
        "frontier_size": len(pq),
        "explored_size": len(visited),
        "depth": 0,
        "h_score": 0,
        "f_score": 0,
        "total_time_ms": (time.time() - start_time) * 1000
    }

def gbfs_simulator(initial_state, goal_state, heuristic_name="manhattan", size=3, max_nodes=10000):
    """Solve the puzzle using Greedy Best-First Search yielding state for visualization."""
    start_time = time.time()
    
    def get_h(state):
        if heuristic_name == "manhattan":
            return manhattan_distance(state, goal_state, size)
        else:
            return misplaced_tiles(state, goal_state, size)
            
    h_start = get_h(initial_state)
    counter = 0
    pq = [(h_start, h_start, counter, tuple(initial_state), [])]
    visited = {tuple(initial_state)}
    nodes_expanded = 0
    
    while pq:
        if nodes_expanded >= max_nodes:
            break
            
        h, _, _, current_state, path = heapq.heappop(pq)
        nodes_expanded += 1
        
        state_info = {
            "status": "searching",
            "current_state": list(current_state),
            "frontier_size": len(pq),
            "explored_size": len(visited),
            "depth": len(path),
            "h_score": h,
            "f_score": h,
            "nodes_expanded": nodes_expanded,
            "path_to_current": path
        }
        
        if list(current_state) == goal_state:
            duration = (time.time() - start_time) * 1000
            state_info["status"] = "success"
            state_info["path"] = path
            state_info["total_time_ms"] = duration
            yield state_info
            return
            
        yield state_info
        
        for neighbor_state, move_idx in get_neighbors(current_state, size):
            if neighbor_state not in visited:
                visited.add(neighbor_state)
                new_h = get_h(neighbor_state)
                counter += 1
                heapq.heappush(pq, (new_h, new_h, counter, neighbor_state, path + [move_idx]))
                
    yield {
        "status": "failed",
        "nodes_expanded": nodes_expanded,
        "frontier_size": len(pq),
        "explored_size": len(visited),
        "depth": 0,
        "h_score": 0,
        "f_score": 0,
        "total_time_ms": (time.time() - start_time) * 1000
    }

def idastar_simulator(initial_state, goal_state, size=3, max_nodes=10000):
    """Solve the puzzle using Iterative Deepening A* (IDA*) Search yielding states."""
    start_time = time.time()
    nodes_expanded = 0
    
    def get_h(state):
        return manhattan_distance(state, goal_state, size)
        
    path_states = [tuple(initial_state)]
    path_moves = []
    
    def search(g, threshold):
        nonlocal nodes_expanded
        current = path_states[-1]
        h = get_h(current)
        f = g + h
        
        nodes_expanded += 1
        
        yield {
            "status": "searching",
            "current_state": list(current),
            "frontier_size": len(path_states),
            "explored_size": nodes_expanded,
            "depth": g,
            "h_score": h,
            "f_score": f,
            "nodes_expanded": nodes_expanded,
            "path_to_current": list(path_moves)
        }
        
        if list(current) == goal_state:
            return "FOUND", f
            
        if f > threshold:
            return "PRUNED", f
            
        if nodes_expanded >= max_nodes:
            return "LIMIT", f
            
        min_val = float('inf')
        
        for neighbor, move_idx in get_neighbors(current, size):
            if neighbor not in path_states:
                path_states.append(neighbor)
                path_moves.append(move_idx)
                
                res, val = yield from search(g + 1, threshold)
                if res in ("FOUND", "LIMIT"):
                    return res, val
                    
                if val < min_val:
                    min_val = val
                    
                path_states.pop()
                path_moves.pop()
                
        return "NOT_FOUND", min_val

    threshold = get_h(initial_state)
    while True:
        path_states = [tuple(initial_state)]
        path_moves = []
        
        res, val = yield from search(0, threshold)
        if res == "FOUND":
            duration = (time.time() - start_time) * 1000
            yield {
                "status": "success",
                "path": path_moves,
                "nodes_expanded": nodes_expanded,
                "frontier_size": len(path_states),
                "explored_size": nodes_expanded,
                "depth": len(path_moves),
                "h_score": 0,
                "f_score": len(path_moves),
                "total_time_ms": duration
            }
            return
        elif res == "LIMIT" or val == float('inf'):
            break
        threshold = val
        
    yield {
        "status": "failed",
        "nodes_expanded": nodes_expanded,
        "frontier_size": 0,
        "explored_size": nodes_expanded,
        "depth": 0,
        "h_score": 0,
        "f_score": 0,
        "total_time_ms": (time.time() - start_time) * 1000
    }

def reconstruct_path_to(state, visited_map):
    path = []
    curr = state
    while curr in visited_map:
        g, parent, move_idx = visited_map[curr]
        if parent is None:
            break
        path.append(move_idx)
        curr = parent
    path.reverse()
    return path

def reconstruct_bidirectional_path(collision_state, visited_f, visited_b):
    # Forward path: initial -> C
    path_f = reconstruct_path_to(collision_state, visited_f)
    
    # Backward path: C -> goal
    path_b = []
    curr = collision_state
    while curr in visited_b:
        g, parent, move_idx = visited_b[curr]
        if parent is None:
            break
        # To transition curr -> parent, the tile we move is at parent's empty slot index
        path_b.append(parent.index(0))
        curr = parent
        
    return path_f + path_b

def bidirectional_astar_simulator(initial_state, goal_state, size=3, max_nodes=10000):
    """Solve the puzzle using Bi-directional A* Search algorithm yielding states."""
    start_time = time.time()
    
    def get_h_forward(state):
        return manhattan_distance(state, goal_state, size)
    def get_h_backward(state):
        return manhattan_distance(state, initial_state, size)
        
    counter = 0
    pq_f = [(get_h_forward(initial_state), 0, get_h_forward(initial_state), counter, tuple(initial_state), None, None)]
    pq_b = [(get_h_backward(goal_state), 0, get_h_backward(goal_state), counter, tuple(goal_state), None, None)]
    
    visited_f = {tuple(initial_state): (0, None, None)}
    visited_b = {tuple(goal_state): (0, None, None)}
    
    nodes_expanded = 0
    
    while pq_f and pq_b:
        if nodes_expanded >= max_nodes:
            break
            
        if pq_f[0][0] <= pq_b[0][0]:
            f, g, h, _, curr, parent, move = heapq.heappop(pq_f)
            
            if curr in visited_b:
                path = reconstruct_bidirectional_path(curr, visited_f, visited_b)
                duration = (time.time() - start_time) * 1000
                yield {
                    "status": "success",
                    "path": path,
                    "nodes_expanded": nodes_expanded,
                    "frontier_size": len(pq_f) + len(pq_b),
                    "explored_size": len(visited_f) + len(visited_b),
                    "depth": len(path),
                    "h_score": h,
                    "f_score": f,
                    "total_time_ms": duration
                }
                return
                
            nodes_expanded += 1
            yield {
                "status": "searching",
                "current_state": list(curr),
                "frontier_size": len(pq_f) + len(pq_b),
                "explored_size": len(visited_f) + len(visited_b),
                "depth": g,
                "h_score": h,
                "f_score": f,
                "nodes_expanded": nodes_expanded,
                "path_to_current": reconstruct_path_to(curr, visited_f)
            }
            
            for neighbor, move_idx in get_neighbors(curr, size):
                new_g = g + 1
                if neighbor not in visited_f or new_g < visited_f[neighbor][0]:
                    visited_f[neighbor] = (new_g, curr, move_idx)
                    new_h = get_h_forward(neighbor)
                    counter += 1
                    heapq.heappush(pq_f, (new_g + new_h, new_g, new_h, counter, neighbor, curr, move_idx))
        else:
            f, g, h, _, curr, parent, move = heapq.heappop(pq_b)
            
            if curr in visited_f:
                path = reconstruct_bidirectional_path(curr, visited_f, visited_b)
                duration = (time.time() - start_time) * 1000
                yield {
                    "status": "success",
                    "path": path,
                    "nodes_expanded": nodes_expanded,
                    "frontier_size": len(pq_f) + len(pq_b),
                    "explored_size": len(visited_f) + len(visited_b),
                    "depth": len(path),
                    "h_score": h,
                    "f_score": f,
                    "total_time_ms": duration
                }
                return
                
            nodes_expanded += 1
            yield {
                "status": "searching",
                "current_state": list(curr),
                "frontier_size": len(pq_f) + len(pq_b),
                "explored_size": len(visited_f) + len(visited_b),
                "depth": g,
                "h_score": h,
                "f_score": f,
                "nodes_expanded": nodes_expanded,
                "path_to_current": reconstruct_path_to(curr, visited_f)
            }
            
            for neighbor, move_idx in get_neighbors(curr, size):
                new_g = g + 1
                if neighbor not in visited_b or new_g < visited_b[neighbor][0]:
                    visited_b[neighbor] = (new_g, curr, move_idx)
                    new_h = get_h_backward(neighbor)
                    counter += 1
                    heapq.heappush(pq_b, (new_g + new_h, new_g, new_h, counter, neighbor, curr, move_idx))
                    
    yield {
        "status": "failed",
        "nodes_expanded": nodes_expanded,
        "frontier_size": len(pq_f) + len(pq_b),
        "explored_size": len(visited_f) + len(visited_b),
        "depth": 0,
        "h_score": 0,
        "f_score": 0,
        "total_time_ms": (time.time() - start_time) * 1000
    }
