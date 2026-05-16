# N-Puzzle Solver

A Python-based N-Puzzle solver implementing four classic search algorithms with an interactive Tkinter GUI. Developed as Assignment #1 for the Artificial Intelligence course.

## Algorithms Implemented

| Algorithm | Optimal? | Complete? | Space Complexity |
|-----------|----------|-----------|-----------------|
| BFS (Breadth-First Search) | ✅ Yes | ✅ Yes | O(b^d) |
| DFS (Depth-First Search) | ❌ No | ✅ Yes (with depth cap) | O(b·d) |
| IDS (Iterative Deepening Search) | ✅ Yes | ✅ Yes | O(b·d) |
| A* — Misplaced Tiles | ✅ Yes | ✅ Yes | O(b^d) |
| A* — Manhattan Distance | ✅ Yes | ✅ Yes | O(b^d) |

## Performance Comparison

All results on the same start state: `[[2,3,5],[0,7,8],[6,1,4]]` → goal: `[[1,2,3],[4,5,6],[7,8,0]]`

| Algorithm | Nodes Expanded | Moves | Time (s) |
|-----------|---------------|-------|----------|
| BFS | 18,344 | 17 | 0.392 |
| DFS (depth cap 100) | 24,046 | 97 | 0.301 |
| IDS | 97,425 | 17 | 0.990 |
| A* Misplaced Tiles | 847 | 17 | 0.007 |
| A* Manhattan Distance | 67 | 17 | 0.0006 |

> A* with Manhattan Distance is **640x faster** than BFS while still finding the optimal solution.

## Features

- Interactive GUI built with Tkinter
- Step-by-step solution navigation (forward and backward)
- Free-run animation mode with pause/cancel
- Random solvable state generator
- Load puzzle state from .txt file
- Visual highlighting of correctly placed tiles
- Real-time stats: nodes expanded, moves, elapsed time
- Supports any NxN puzzle size (tested up to 7x7)

## Project Structure

```
main.py              --> Entry point, launches the GUI
puzzle.py            --> PuzzleState class, successor generation
algorithms.py        --> BFS, DFS, IDS, A* implementations
gui.py               --> Tkinter GUI
run_experiments.py   --> Runs all algorithm comparisons
sample_state.txt     --> Example start state
```

## How to Run

Requirements: Python 3.8 or higher, Tkinter (comes with Python)

```
python main.py
```

To run algorithm comparison experiments:

```
python run_experiments.py
```

If Tkinter is missing on Linux:

```
sudo apt-get install python3-tk
```

## Scalability

| Puzzle Size | Tiles | Nodes Expanded | Time (s) |
|-------------|-------|----------------|----------|
| 3x3 | 8 | 2,242 | 0.096 |
| 5x5 | 24 | 8,267 | 0.589 |
| 7x7 | 48 | 100,000+ | 30+ |

## Team

- Mert KAYMAK
- Ahmet Alperen ARSLAN
- Utkan Onur ÖZBEDEL

Konya Food and Agriculture University — Computer Engineering
Artificial Intelligence Course — Spring 2026
