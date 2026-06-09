"""
Search algorithm simulators for N-Puzzle game.
Provides visualization-friendly generators for A*, GBFS, IDA*, and Bi-directional A*.
"""
import heapq
import time
from search_utils import get_neighbors, manhattan_distance, misplaced_tiles, build_goal_position_map


def astar_simulator(initial_state, goal_state, heuristic_name="manhattan", size=3, max_nodes=10000):
    """
    Solve the puzzle using A* Search algorithm yielding state for visualization.
    
    Args:
        initial_state: Starting board state (list or tuple)
        goal_state: Target board state (list or tuple)
        heuristic_name: "manhattan" or "misplaced"
        size: Board dimension (3, 4, 5)
        max_nodes: Maximum nodes to explore before giving up
    
    Yields:
        Dict with status, current_state, and search metrics at each step
    """
    start_time = time.time()
    goal_state = tuple(goal_state)
    goal_pos_map = build_goal_position_map(goal_state)
    
    def get_h(state):
        state_tuple = tuple(state) if isinstance(state, list) else state
        if heuristic_name == "manhattan":
            return manhattan_distance(state_tuple, goal_pos_map, size)
        else:
            return misplaced_tiles(state_tuple, goal_state, size)
            
    h_start = get_h(tuple(initial_state))
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
        
        if list(current_state) == list(goal_state):
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
    """
    Solve the puzzle using Greedy Best-First Search yielding state for visualization.
    
    Args:
        initial_state: Starting board state (list or tuple)
        goal_state: Target board state (list or tuple)
        heuristic_name: "manhattan" or "misplaced"
        size: Board dimension (3, 4, 5)
        max_nodes: Maximum nodes to explore before giving up
    
    Yields:
        Dict with status, current_state, and search metrics at each step
    """
    start_time = time.time()
    goal_state = tuple(goal_state)
    goal_pos_map = build_goal_position_map(goal_state)
    
    def get_h(state):
        state_tuple = tuple(state) if isinstance(state, list) else state
        if heuristic_name == "manhattan":
            return manhattan_distance(state_tuple, goal_pos_map, size)
        else:
            return misplaced_tiles(state_tuple, goal_state, size)
            
    h_start = get_h(tuple(initial_state))
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
        
        if list(current_state) == list(goal_state):
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
    """
    Solve the puzzle using Iterative Deepening A* (IDA*) Search yielding states.
    
    Args:
        initial_state: Starting board state
        goal_state: Target board state
        size: Board dimension
        max_nodes: Maximum nodes to explore
    
    Yields:
        Dict with search progress information
    """
    start_time = time.time()
    goal_state = tuple(goal_state)
    goal_pos_map = build_goal_position_map(goal_state)
    initial_state = tuple(initial_state)
    
    def get_h(state):
        return manhattan_distance(state, goal_pos_map, size)
        
    nodes_expanded = 0
    final_path = None
    
    def search(g, threshold, path_states, path_moves):
        """Recursive depth-first search with threshold pruning."""
        nonlocal nodes_expanded
        current = path_states[-1]
        h = get_h(current)
        f = g + h
        
        nodes_expanded += 1
        
        if list(current) == list(goal_state):
            return "FOUND", f, list(path_moves)
            
        if f > threshold:
            return "PRUNED", f, []
            
        if nodes_expanded >= max_nodes:
            return "LIMIT", f, []
            
        min_val = float('inf')
        result_path = None
        
        for neighbor, move_idx in get_neighbors(current, size):
            if neighbor not in path_states:
                path_states.append(neighbor)
                path_moves.append(move_idx)
                
                res, val, path = search(g + 1, threshold, path_states, path_moves)
                if res == "FOUND":
                    return res, val, path
                if res == "LIMIT":
                    return res, val, []
                    
                if val < min_val:
                    min_val = val
                    
                path_states.pop()
                path_moves.pop()
                
        return "NOT_FOUND", min_val, []

    threshold = get_h(initial_state)
    
    while True:
        path_states = [initial_state]
        path_moves = []
        
        # Yield initial state
        h = get_h(initial_state)
        yield {
            "status": "searching",
            "current_state": list(initial_state),
            "frontier_size": 1,
            "explored_size": nodes_expanded,
            "depth": 0,
            "h_score": h,
            "f_score": h,
            "nodes_expanded": nodes_expanded,
            "path_to_current": []
        }
        
        res, val, path = search(0, threshold, path_states, path_moves)
        
        if res == "FOUND":
            final_path = path
            break
        elif res == "LIMIT":
            break
        elif val == float('inf'):
            break
        else:
            threshold = val
            
        if nodes_expanded >= max_nodes:
            break

    if final_path:
        duration = (time.time() - start_time) * 1000
        yield {
            "status": "success",
            "path": final_path,
            "nodes_expanded": nodes_expanded,
            "frontier_size": 0,
            "explored_size": nodes_expanded,
            "depth": len(final_path),
            "h_score": 0,
            "f_score": len(final_path),
            "total_time_ms": duration
        }
    else:
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
    """
    Reconstruct the path from initial state to given state.
    
    Args:
        state: Current state tuple
        visited_map: Dict mapping state -> (g_cost, parent_state, move_index)
    
    Returns:
        List of move indices to reach this state
    """
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
    """
    Reconstruct path from bidirectional search collision point.
    
    Args:
        collision_state: State where forward and backward searches meet
        visited_f: Forward search visited map
        visited_b: Backward search visited map
    
    Returns:
        Complete path from initial to goal state
    """
    path_f = reconstruct_path_to(collision_state, visited_f)
    
    path_b = []
    curr = collision_state
    while curr in visited_b:
        g, parent, move_idx = visited_b[curr]
        if parent is None:
            break
        path_b.append(parent.index(0))
        curr = parent
        
    return path_f + path_b


def bidirectional_astar_simulator(initial_state, goal_state, size=3, max_nodes=10000):
    """
    Solve the puzzle using Bi-directional A* Search algorithm yielding states.
    
    Runs two simultaneous A* searches: forward from initial state and backward
    from goal state, meeting in the middle.
    
    Args:
        initial_state: Starting board state
        goal_state: Target board state
        size: Board dimension
        max_nodes: Maximum nodes to explore
    
    Yields:
        Dict with search progress and metrics
    """
    start_time = time.time()
    goal_state = tuple(goal_state)
    initial_state = tuple(initial_state)
    
    goal_pos_map_f = build_goal_position_map(goal_state)
    goal_pos_map_b = build_goal_position_map(initial_state)
    
    def get_h_forward(state):
        return manhattan_distance(state, goal_pos_map_f, size)
        
    def get_h_backward(state):
        return manhattan_distance(state, goal_pos_map_b, size)
        
    counter = 0
    pq_f = [(get_h_forward(initial_state), 0, get_h_forward(initial_state), counter, initial_state, None, None)]
    pq_b = [(get_h_backward(goal_state), 0, get_h_backward(goal_state), counter, goal_state, None, None)]
    
    visited_f = {initial_state: (0, None, None)}
    visited_b = {goal_state: (0, None, None)}
    
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