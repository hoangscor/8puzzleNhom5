from game_logic import PuzzleGame
from search_simulators import astar_simulator

# Test with columns goal
game = PuzzleGame(size=3)
game.set_goal_preset('columns')
print('Columns goal:', game.goal_state)
print('Current state:', game.current_state)
print('Is solvable:', game.is_solvable(game.current_state))

# Try to solve
gen = astar_simulator(list(game.current_state), game.goal_state, 'manhattan', size=3, max_nodes=10000)
for step in gen:
    if step['status'] in ('success', 'failed'):
        print(f'Result: {step["status"]}, nodes: {step["nodes_expanded"]}, path length: {len(step.get("path", []))}')
        break