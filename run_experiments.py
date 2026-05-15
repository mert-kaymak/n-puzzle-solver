"""
run_experiments.py
==================
Runs all required search algorithms on the Part IV start state and
prints a structured summary for inclusion in the written report.
Also runs the Part VIII puzzle-size experiments.
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from puzzle import PuzzleState
from algorithms import (
    bfs, dfs, ids,
    astar, heuristic_misplace, heuristic_manhattan,
)


# ── Part IV start state ────────────────────────────────────────────────
# Board as given in the assignment (0 = blank):
#   2 3 5
#   0 7 8
#   6 1 4
START_BOARD = [2, 3, 5,
               0, 7, 8,
               6, 1, 4]
SIZE = 3

start = PuzzleState(START_BOARD, SIZE)
goal  = PuzzleState.generate_goal(SIZE)


def separator(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def print_result(algo_label, path, nodes, elapsed):
    moves = len(path) - 1 if path else -1
    print(f"  Nodes expanded : {nodes}")
    print(f"  Moves in path  : {moves}")
    print(f"  Time (s)       : {elapsed:.6f}")
    if path:
        print(f"  Move sequence  : {[s.move for s in path if s.move]}")


# ── START STATE DISPLAY ────────────────────────────────────────────────
separator("START  STATE")
print(start)
separator("GOAL STATE")
print(goal)


# ── Part IV – BFS ──────────────────────────────────────────────────────
separator("Part IV – Breadth-First Search (BFS)")
path, nodes, elapsed = bfs(start, goal)
print_result("BFS", path, nodes, elapsed)
bfs_moves = len(path) - 1 if path else -1


# ── Part V – DFS ──────────────────────────────────────────────────────
separator("Part V – Depth-First Search (DFS, depth cap=50)")
path_dfs, nodes_dfs, elapsed_dfs = dfs(start, goal, max_depth=50)
print_result("DFS", path_dfs, nodes_dfs, elapsed_dfs)

print()
print("  NOTE: Plain DFS (without cycle checking) would loop forever")
print("  on the sliding-puzzle because the state space contains cycles.")
print("  Fix applied: an explored-state set + a depth cap of 50.")
print("  DFS does NOT guarantee optimality → its path may be longer")
print(f"  than the BFS optimum of {bfs_moves} moves.")


# ── Part VI – IDS ─────────────────────────────────────────────────────
separator("Part VI – Iterative-Deepening Search (IDS)")
path_ids, nodes_ids, elapsed_ids = ids(start, goal)
print_result("IDS", path_ids, nodes_ids, elapsed_ids)


# ── Part VII – A* ─────────────────────────────────────────────────────
separator("Part VII-c – A* with Misplaced-Tiles heuristic")
path_am, nodes_am, elapsed_am = astar(start, goal, heuristic_misplace)
print_result("A* (misplace)", path_am, nodes_am, elapsed_am)

separator("Part VII-c – A* with Manhattan-Distance heuristic")
path_amd, nodes_amd, elapsed_amd = astar(start, goal, heuristic_manhattan)
print_result("A* (manhattan)", path_amd, nodes_amd, elapsed_amd)

print()
print("  Part VII-a commentary on heuristics:")
print("  Both h1 (misplaced) and h2 (manhattan) are admissible, so")
print("  A* with either is guaranteed optimal.  h2 dominates h1 because")
print("  h2(n) >= h1(n) for every state n: each misplaced tile must move")
print("  at least 1 step but may need more.  A* with h2 therefore expands")
print("  fewer nodes than with h1, which in turn expands far fewer nodes")
print("  than uninformed BFS/IDS.")


# ── Summary table ─────────────────────────────────────────────────────
separator("COMPARISON SUMMARY")
print(f"{'Algorithm':<35} {'Nodes':>8} {'Moves':>7} {'Time (s)':>12}")
print("-" * 65)

results = [
    ("BFS",                      nodes,     len(path)-1 if path else -1,        elapsed),
    ("DFS (depth cap 50)",       nodes_dfs, len(path_dfs)-1 if path_dfs else -1, elapsed_dfs),
    ("IDS",                      nodes_ids, len(path_ids)-1 if path_ids else -1, elapsed_ids),
    ("A* – Misplaced tiles",     nodes_am,  len(path_am)-1 if path_am else -1,  elapsed_am),
    ("A* – Manhattan distance",  nodes_amd, len(path_amd)-1 if path_amd else -1,elapsed_amd),
]

for name, n, m, t in results:
    print(f"  {name:<33} {n:>8} {m:>7} {t:>12.6f}")


# ── Part VIII – Puzzle-size experiments ───────────────────────────────
separator("Part VIII – Scalability: A* (Manhattan) on different sizes")
print(f"{'Puzzle':^12} {'Tiles':^8} {'Nodes':>10} {'Moves':>8} {'Time (s)':>12}")
print("-" * 56)

import random
random.seed(42)   # reproducibility

for sz in [3, 5, 7]:
    # Generate a random state that is exactly 10 moves from the goal
    # to keep runtimes manageable for 5×5 and 7×7
    g = PuzzleState.generate_goal(sz)
    state = g
    prev  = None
    for _ in range(10 * sz):       # more steps for larger puzzles
        succs = [s for _, s in state.successors()
                 if prev is None or s.board != prev.board]
        prev  = state
        state = random.choice(succs)
    state = PuzzleState(state.board, sz)   # detach parent chain

    p, n, t = astar(state, PuzzleState.generate_goal(sz),
                    heuristic_manhattan)
    m = len(p) - 1 if p else -1
    print(f"  {sz}×{sz}      {sz*sz-1:^8} {n:>10} {m:>8} {t:>12.6f}")

print()
print("  Observation: as puzzle size grows from 3×3 to 7×7, both the")
print("  number of nodes expanded and time increase dramatically,")
print("  reflecting the exponential growth of the state space (which")
print("  has (L²)! / 2 solvable configurations for an L×L puzzle).")
print("  The Manhattan heuristic mitigates this but A* still struggles")
print("  on 7×7 without more powerful heuristics (e.g. pattern databases).")
