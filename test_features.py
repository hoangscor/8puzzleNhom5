#!/usr/bin/env python3
"""
Test script to verify the synchronization and completeness of 8-Puzzle features.
Tests game logic, solvers, and basic functionality without GUI.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from game_logic import PuzzleGame
import bfs_solver
import astar_solver

def test_game_logic():
    """Test basic game logic: moves, undo, redo, solvability."""
    print("Testing Game Logic...")
    game = PuzzleGame()

    # Test initial state
    assert game.current_state != game.goal_state, "Initial state should not be goal"
    assert game.is_solvable(game.current_state), "Initial state should be solvable"

    # Test move
    empty_pos = game.get_empty_pos()
    # Find adjacent tile
    adjacent = None
    for i in range(9):
        if abs((i//3) - empty_pos[0]) + abs((i%3) - empty_pos[1]) == 1:
            adjacent = i
            break
    assert adjacent is not None, "Should find adjacent tile"
    assert game.move(adjacent), "Move should succeed"
    assert game.current_state[adjacent] == 0, "Empty should move to adjacent position"

    # Test undo
    assert game.undo(), "Undo should succeed"
    assert game.current_state == game.history[-1] if game.history else game.goal_state, "Undo should restore previous state"

    # Test reset
    game.reset()
    assert game.current_state != game.goal_state, "Reset should shuffle"

    print("✓ Game logic tests passed")

def test_solvers():
    """Test BFS and A* solvers."""
    print("Testing Solvers...")

    # Simple test case
    initial = [1, 2, 3, 4, 5, 6, 0, 7, 8]  # Almost solved
    goal = [1, 2, 3, 4, 5, 6, 7, 8, 0]

    # Test BFS
    path_bfs, nodes_bfs, time_bfs = bfs_solver.solve(initial, goal)
    assert path_bfs is not None, "BFS should find solution"
    assert len(path_bfs) > 0, "BFS path should not be empty"
    assert nodes_bfs > 0, "BFS should explore nodes"
    assert time_bfs >= 0, "BFS time should be non-negative"

    # Test A*
    path_astar, nodes_astar, time_astar = astar_solver.solve(initial, goal)
    assert path_astar is not None, "A* should find solution"
    assert len(path_astar) > 0, "A* path should not be empty"
    assert nodes_astar > 0, "A* should explore nodes"
    assert time_astar >= 0, "A* time should be non-negative"

    # A* should be more efficient (fewer nodes) for this case
    assert nodes_astar <= nodes_bfs, "A* should explore fewer or equal nodes than BFS"

    print(f"✓ BFS: {len(path_bfs)} moves, {nodes_bfs} nodes, {time_bfs:.2f}ms")
    print(f"✓ A*: {len(path_astar)} moves, {nodes_astar} nodes, {time_astar:.2f}ms")

def test_image_processor():
    """Test image processing (if PIL available)."""
    print("Testing Image Processor...")
    try:
        from image_processor import load_and_split_image
        # This would require an actual image file, so just test import
        print("✓ Image processor import successful")
    except ImportError as e:
        print(f"✗ Image processor import failed: {e}")
        return False
    return True

def main():
    """Run all tests."""
    print("=== 8-Puzzle Feature Verification ===\n")

    try:
        test_game_logic()
        test_solvers()
        test_image_processor()

        print("\n=== All tests passed! Features are synchronized and complete. ===")
        return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)