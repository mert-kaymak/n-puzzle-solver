# 🧩 N-Puzzle Solver

An interactive N-Puzzle solver implementing and comparing four classic AI search algorithms: **BFS, DFS, IDS, and A\***.  
Built with Python and a Tkinter GUI for step-by-step visualization.

> 📌 AI Course — Assignment | Konya Food & Agriculture University, 2025–2026

---

## 📌 Overview

The N-Puzzle (sliding tile puzzle) is a classic AI problem. This project solves it using four search strategies, compares their performance, and provides a visual GUI to replay solutions step by step.

---

## ✨ Features

- **4 Search Algorithms** — BFS, DFS (with depth cap), IDS, A* (Misplaced Tiles & Manhattan Distance)
- **Interactive GUI** — Tkinter-based interface with step-by-step and animated playback
- **Real-time Stats** — Nodes expanded, moves, and elapsed time displayed live
- **Configurable Board** — Supports any N×N puzzle size (3×3, 5×5, etc.)
- **Random State Generator** — Generates solvable configurations using Fisher-Yates shuffle
- **File Input** — Load custom puzzle states from `.txt` files

---

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-blue?style=flat-square)

| File | Description |
|------|-------------|
| `main.py` | Entry point — launches the GUI |
| `puzzle.py` | `PuzzleState` class, state representation, successor generation |
| `algorithms.py` | BFS, DFS, IDS, A* implementations |
| `gui.py` | Tkinter GUI — visualization and controls |
| `run_experiments.py` | Automated benchmark experiments across puzzle sizes |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- No external libraries required (uses only Python standard library)

### Run

**Windows:**
```bash
calistir.bat
```

**Linux / macOS:**
```bash
bash calistir.sh
```

**Or directly:**
```bash
python main.py
```

### Load a Custom State

Create a `.txt` file with space-separated tile values (0 = blank):
```
2 3 5
0 7 8
6 1 4
```
Then use **"Load from File"** in the GUI.

---

## 📊 Algorithm Comparison

All results on the same start state: `[[2,3,5],[0,7,8],[6,1,4]]` → goal: `[[1,2,3],[4,5,6],[7,8,0]]`

| Algorithm | Nodes Expanded | Moves | Time (s) | Optimal? |
|-----------|---------------|-------|----------|----------|
| BFS | 18,344 | 17 | 0.392 | ✅ Yes |
| DFS (depth cap 100) | 24,046 | 97 | 0.301 | ❌ No |
| IDS | 97,425 | 17 | 0.990 | ✅ Yes |
| A\* – Misplaced Tiles | 847 | 17 | 0.00738 | ✅ Yes |
| A\* – Manhattan Distance | **67** | 17 | **0.000613** | ✅ Yes (best) |

> **Key insight:** A\* with Manhattan Distance is **640× faster than BFS** and **1,613× faster than IDS** while still finding the optimal 17-move solution. The heuristic quality is the dominant factor in A\* performance.

---

## 🔬 Scalability Experiment

A\* (Manhattan) was tested across different puzzle sizes:

| Size | Tiles | Nodes Expanded | Optimal Moves | Time (s) |
|------|-------|---------------|---------------|----------|
| 3×3 | 8 | 2,242 | 24 | 0.096 |
| 5×5 | 24 | 8,267 | 32 | 0.589 |
| 7×7 | 48 | 100,000+ | — | > 30s |

The 7×7 puzzle becomes intractable for plain A\* due to state space explosion — the solvable state count jumps from ~181,440 (3×3) to ~7.75 × 10²³ (5×5).

---

## 🧠 Algorithm Notes

**BFS** — Optimal and complete, but memory-intensive (stores entire frontier).  
**DFS** — Fast but non-optimal; requires depth cap to avoid infinite loops.  
**IDS** — Combines BFS optimality with DFS memory efficiency; re-expands nodes at each depth.  
**A\*** — Best performance with a good heuristic. Manhattan distance dominates Misplaced Tiles because it accounts for distance, not just position.

---

## 👥 Team

| Name | Role |
|------|------|
| **Mert Kaymak** | Algorithm implementation, state representation, experiments |
| **Ahmet Alperen Arslan** | GUI development, project structure |
| **Utkan Onur Özbedel** | Testing, documentation, report |
