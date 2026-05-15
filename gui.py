"""
gui.py - Graphical User Interface for the N-Puzzle Solver
==========================================================
Implements a Tkinter-based GUI that satisfies all Part II requirements:
  a) Algorithm selection (dropdown)
  b) Continuous puzzle display
  c) Single-step through search iterations
  d) Iteration counter display
  e) Start / Pause / Cancel free-run with live updates
  f) Random initial state generation
  g) Load initial state from a formatted text file OR configure via mouse
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import random
import os

from puzzle import PuzzleState
from algorithms import (
    bfs, dfs, ids,
    astar, heuristic_misplace, heuristic_manhattan,
)


# ── colour palette ────────────────────────────────────────────────────
TILE_BG       = "#4A90D9"
TILE_FG       = "#FFFFFF"
BLANK_BG      = "#E8E8E8"
CORRECT_BG    = "#27AE60"   # tile in correct position → green
BOARD_BG      = "#2C3E50"
HEADER_BG     = "#1A252F"
BUTTON_BG     = "#3498DB"
BUTTON_FG     = "#FFFFFF"
BUTTON_ACTIVE = "#2980B9"
STOP_BG       = "#E74C3C"
STOP_ACTIVE   = "#C0392B"
PAUSE_BG      = "#F39C12"
PAUSE_ACTIVE  = "#E67E22"
PANEL_BG      = "#34495E"
TEXT_FG       = "#ECF0F1"
FONT_TILE     = ("Helvetica", 22, "bold")
FONT_LABEL    = ("Helvetica", 10, "bold")
FONT_VALUE    = ("Helvetica", 11)
FONT_HEADER   = ("Helvetica", 14, "bold")


ALGORITHMS = {
    "Breadth-First Search (BFS)":          "bfs",
    "Depth-First Search (DFS)":            "dfs",
    "Iterative-Deepening Search (IDS)":    "ids",
    "A* – Misplaced Tiles":                "astar_misplace",
    "A* – Manhattan Distance":             "astar_manhattan",
}


class NPuzzleApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("N-Puzzle Solver")
        self.resizable(True, True)
        self.configure(bg=HEADER_BG)

        # ── state ───────────────────────────────────────────────────
        self.puzzle_size   = tk.IntVar(value=3)
        self.algo_name     = tk.StringVar(value=list(ALGORITHMS.keys())[0])
        self.iteration_var = tk.StringVar(value="0")
        self.status_var    = tk.StringVar(value="Ready.")
        self.nodes_var     = tk.StringVar(value="–")
        self.moves_var     = tk.StringVar(value="–")
        self.time_var      = tk.StringVar(value="–")

        self._solution_path  = []      # list[PuzzleState] – full solution
        self._step_index     = 0       # current display position in path
        self._running        = False   # free-run active?
        self._paused         = False
        self._cancel_flag    = False
        self._run_thread     = None

        # Current displayed state & goal
        self.current_state   = PuzzleState.generate_random(3)
        self.goal_state      = PuzzleState.generate_goal(3)

        # tile buttons (rebuilt when size changes)
        self._tile_buttons   = []
        # For mouse-click editing: track which tile is "selected"
        self._selected_tile_pos = None

        self._build_ui()
        self._render_board(self.current_state)

    # ==================================================================
    # UI construction
    # ==================================================================

    def _build_ui(self):
        """Assemble the full layout."""
        # ── top header bar ─────────────────────────────────────────
        header = tk.Frame(self, bg=HEADER_BG, pady=8)
        header.pack(fill="x")
        tk.Label(header, text="N-Puzzle Solver",
                 font=FONT_HEADER, bg=HEADER_BG, fg=TEXT_FG).pack()

        # ── main area: left panel + board + right panel ─────────────
        main = tk.Frame(self, bg=HEADER_BG)
        main.pack(fill="both", expand=True, padx=10, pady=6)

        self._left_panel(main)

        # board frame (centre)
        self.board_frame = tk.Frame(main, bg=BOARD_BG,
                                    bd=3, relief="ridge")
        self.board_frame.pack(side="left", padx=10, pady=4)
        self._build_board_grid()

        self._right_panel(main)

        # ── status bar ─────────────────────────────────────────────
        sb = tk.Frame(self, bg=PANEL_BG, pady=3)
        sb.pack(fill="x")
        tk.Label(sb, textvariable=self.status_var,
                 bg=PANEL_BG, fg=TEXT_FG,
                 font=("Helvetica", 9)).pack(side="left", padx=8)

    def _left_panel(self, parent):
        frame = tk.Frame(parent, bg=PANEL_BG, width=210,
                         bd=2, relief="groove")
        frame.pack(side="left", fill="y", padx=(0, 4), pady=4)
        frame.pack_propagate(False)

        def section(text):
            tk.Label(frame, text=text, font=FONT_LABEL,
                     bg=PANEL_BG, fg="#BDC3C7",
                     anchor="w").pack(fill="x", padx=8, pady=(10, 2))
            ttk.Separator(frame, orient="horizontal").pack(
                fill="x", padx=6, pady=2)

        # ── Puzzle size ─────────────────────────────────────────────
        section("PUZZLE SIZE")
        size_row = tk.Frame(frame, bg=PANEL_BG)
        size_row.pack(fill="x", padx=8)
        for s in [3, 5, 7]:
            tk.Radiobutton(size_row, text=f"{s}×{s}",
                           variable=self.puzzle_size, value=s,
                           bg=PANEL_BG, fg=TEXT_FG,
                           selectcolor=BOARD_BG,
                           activebackground=PANEL_BG,
                           command=self._on_size_change).pack(
                               side="left", padx=4)

        # ── Algorithm ───────────────────────────────────────────────
        section("ALGORITHM")
        tk.OptionMenu(frame, self.algo_name,
                      *ALGORITHMS.keys()).pack(fill="x", padx=8, pady=2)

        # ── Initial state ───────────────────────────────────────────
        section("INITIAL STATE")
        self._btn(frame, "🎲  Random State",  self._gen_random)
        self._btn(frame, "📂  Load from File", self._load_file)
        tk.Label(frame,
                 text="(click two tiles on\nthe board to swap them)",
                 bg=PANEL_BG, fg="#95A5A6",
                 font=("Helvetica", 8), justify="center").pack(pady=2)

        # ── Run controls ─────────────────────────────────────────────
        section("SEARCH CONTROLS")
        self._btn(frame, "▶  Solve  (find path)", self._solve)
        self._btn(frame, "⏭  Step Forward",        self._step_forward)
        self._btn(frame, "⏮  Step Backward",       self._step_backward)

        self.run_btn   = self._btn(frame, "▷  Free Run",  self._start_run,
                                   bg=BUTTON_BG)
        self.pause_btn = self._btn(frame, "⏸  Pause",     self._pause_run,
                                   bg=PAUSE_BG,   disabled=True)
        self.stop_btn  = self._btn(frame, "⏹  Cancel",    self._cancel_run,
                                   bg=STOP_BG,    disabled=True)

    def _right_panel(self, parent):
        frame = tk.Frame(parent, bg=PANEL_BG, width=175,
                         bd=2, relief="groove")
        frame.pack(side="left", fill="y", padx=(4, 0), pady=4)
        frame.pack_propagate(False)

        def row(label, var):
            r = tk.Frame(frame, bg=PANEL_BG)
            r.pack(fill="x", padx=8, pady=3)
            tk.Label(r, text=label, bg=PANEL_BG, fg="#BDC3C7",
                     font=FONT_LABEL, width=13, anchor="w").pack(
                         side="left")
            tk.Label(r, textvariable=var, bg=PANEL_BG, fg=TEXT_FG,
                     font=FONT_VALUE).pack(side="left")

        tk.Label(frame, text="STATISTICS", font=FONT_LABEL,
                 bg=PANEL_BG, fg="#BDC3C7",
                 anchor="w").pack(fill="x", padx=8, pady=(12, 2))
        ttk.Separator(frame, orient="horizontal").pack(
            fill="x", padx=6, pady=2)

        row("Iteration:",      self.iteration_var)
        row("Nodes expanded:", self.nodes_var)
        row("Moves (path):",   self.moves_var)
        row("Time (s):",       self.time_var)

        # Goal state preview
        tk.Label(frame, text="GOAL STATE", font=FONT_LABEL,
                 bg=PANEL_BG, fg="#BDC3C7",
                 anchor="w").pack(fill="x", padx=8, pady=(14, 2))
        ttk.Separator(frame, orient="horizontal").pack(
            fill="x", padx=6, pady=2)

        self.goal_frame = tk.Frame(frame, bg=PANEL_BG)
        self.goal_frame.pack(pady=6)
        self._render_mini_board(self.goal_frame, self.goal_state)

    def _btn(self, parent, text, cmd, bg=BUTTON_BG, disabled=False):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=BUTTON_FG,
                      activebackground=BUTTON_ACTIVE,
                      activeforeground=BUTTON_FG,
                      relief="flat", bd=0, pady=5,
                      font=("Helvetica", 9, "bold"),
                      cursor="hand2")
        b.pack(fill="x", padx=8, pady=2)
        if disabled:
            b.configure(state="disabled")
        return b

    # ==================================================================
    # Board grid
    # ==================================================================

    def _build_board_grid(self):
        """Create (or recreate) the grid of tile buttons."""
        for w in self.board_frame.winfo_children():
            w.destroy()
        self._tile_buttons = []
        size = self.puzzle_size.get()

        for r in range(size):
            row_btns = []
            for c in range(size):
                btn = tk.Button(
                    self.board_frame,
                    text="", width=3, height=1,
                    font=FONT_TILE,
                    relief="flat", bd=0,
                    cursor="hand2",
                )
                btn.grid(row=r, column=c, padx=3, pady=3)
                pos = r * size + c
                btn.configure(
                    command=lambda p=pos: self._tile_clicked(p))
                row_btns.append(btn)
            self._tile_buttons.append(row_btns)

    def _render_board(self, state: PuzzleState):
        """Update every tile button to reflect *state*."""
        goal = PuzzleState.generate_goal(state.size)
        for i, tile in enumerate(state.board):
            r, c = i // state.size, i % state.size
            btn  = self._tile_buttons[r][c]
            if tile == 0:
                btn.configure(text="", bg=BLANK_BG,
                              activebackground=BLANK_BG)
            else:
                # highlight tiles already in their correct position
                correct = (tile == goal.board[i])
                bg = CORRECT_BG if correct else TILE_BG
                btn.configure(text=str(tile), bg=bg, fg=TILE_FG,
                              activebackground=bg)

    def _render_mini_board(self, parent, state: PuzzleState):
        """Small read-only board preview (used for goal state)."""
        for w in parent.winfo_children():
            w.destroy()
        size = state.size
        cell = max(20, 50 - size * 5)
        fnt  = ("Helvetica", max(7, 14 - size * 2), "bold")
        for i, tile in enumerate(state.board):
            r, c = i // size, i % size
            bg   = BLANK_BG if tile == 0 else TILE_BG
            lbl  = tk.Label(parent, text=str(tile) if tile else "",
                            bg=bg, fg=TILE_FG,
                            font=fnt,
                            width=2, height=1,
                            relief="flat", bd=1)
            lbl.grid(row=r, column=c, padx=1, pady=1)

    # ==================================================================
    # Tile click → swap (mouse-based state editing, Part II g)
    # ==================================================================

    def _tile_clicked(self, pos):
        if self._running:
            return   # don't allow edits during a run
        if self._selected_tile_pos is None:
            self._selected_tile_pos = pos
            r, c = pos // self.puzzle_size.get(), pos % self.puzzle_size.get()
            self._tile_buttons[r][c].configure(relief="solid", bd=2)
        else:
            # Swap the two tiles
            board = list(self.current_state.board)
            board[self._selected_tile_pos], board[pos] = \
                board[pos], board[self._selected_tile_pos]
            # Reset highlight on old selection
            or_, oc = (self._selected_tile_pos // self.puzzle_size.get(),
                       self._selected_tile_pos %  self.puzzle_size.get())
            self._tile_buttons[or_][oc].configure(relief="flat", bd=0)
            self._selected_tile_pos = None

            self.current_state = PuzzleState(
                board, self.puzzle_size.get())
            self._solution_path = []
            self._step_index    = 0
            self._reset_stats()
            self._render_board(self.current_state)

    # ==================================================================
    # Puzzle-size change
    # ==================================================================

    def _on_size_change(self):
        size = self.puzzle_size.get()
        self.current_state = PuzzleState.generate_random(size)
        self.goal_state    = PuzzleState.generate_goal(size)
        self._solution_path = []
        self._step_index    = 0
        self._reset_stats()
        self._build_board_grid()
        self._render_board(self.current_state)
        # Refresh goal preview
        for w in self.goal_frame.winfo_children():
            w.destroy()
        self._render_mini_board(self.goal_frame, self.goal_state)
        self.status_var.set(f"Puzzle size set to {size}×{size}.")

    # ==================================================================
    # Initial-state helpers
    # ==================================================================

    def _gen_random(self):
        """Generate a random solvable start state (Part II f)."""
        size = self.puzzle_size.get()
        self.current_state = PuzzleState.generate_random(size)
        self._solution_path = []
        self._step_index    = 0
        self._reset_stats()
        self._render_board(self.current_state)
        self.status_var.set("Random state generated.")

    def _load_file(self):
        """Load initial state from a text file (Part II g)."""
        path = filedialog.askopenfilename(
            title="Load puzzle state",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            state = PuzzleState.from_file(path)
            self.puzzle_size.set(state.size)
            self.current_state  = state
            self.goal_state     = PuzzleState.generate_goal(state.size)
            self._solution_path = []
            self._step_index    = 0
            self._reset_stats()
            self._build_board_grid()
            self._render_board(self.current_state)
            for w in self.goal_frame.winfo_children():
                w.destroy()
            self._render_mini_board(self.goal_frame, self.goal_state)
            self.status_var.set(f"Loaded: {os.path.basename(path)}")
        except Exception as exc:
            messagebox.showerror("Load Error", str(exc))

    # ==================================================================
    # Solve (run algorithm in background thread)
    # ==================================================================

    def _solve(self):
        """Run the selected algorithm and store the solution path."""
        self._solution_path = []
        self._step_index    = 0
        self._reset_stats()
        self.status_var.set("Solving… please wait.")
        self.update()

        algo_key = ALGORITHMS[self.algo_name.get()]
        start    = self.current_state
        goal     = PuzzleState.generate_goal(start.size)

        def run():
            try:
                if algo_key == "bfs":
                    path, n, t = bfs(start, goal)
                elif algo_key == "dfs":
                    path, n, t = dfs(start, goal)
                elif algo_key == "ids":
                    path, n, t = ids(start, goal)
                elif algo_key == "astar_misplace":
                    path, n, t = astar(start, goal, heuristic_misplace)
                elif algo_key == "astar_manhattan":
                    path, n, t = astar(start, goal, heuristic_manhattan)
                else:
                    path, n, t = None, 0, 0.0

                self.after(0, lambda: self._on_solve_done(path, n, t))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror(
                    "Error", str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def _on_solve_done(self, path, nodes, elapsed):
        if path is None:
            self.status_var.set("No solution found.")
            messagebox.showinfo("Result", "No solution found.")
            return

        self._solution_path = path
        self._step_index    = 0
        moves = len(path) - 1

        self.nodes_var.set(str(nodes))
        self.moves_var.set(str(moves))
        self.time_var.set(f"{elapsed:.4f}")
        self.iteration_var.set("0")
        self.status_var.set(
            f"Solution found! {moves} moves, {nodes} nodes expanded, "
            f"{elapsed:.4f}s")
        self._render_board(self.current_state)

    # ==================================================================
    # Step navigation (Part II c & d)
    # ==================================================================

    def _step_forward(self):
        if not self._solution_path:
            self.status_var.set("Run 'Solve' first.")
            return
        if self._step_index < len(self._solution_path) - 1:
            self._step_index += 1
            self.iteration_var.set(str(self._step_index))
            self._render_board(self._solution_path[self._step_index])
            if self._step_index == len(self._solution_path) - 1:
                self.status_var.set("Goal reached!")

    def _step_backward(self):
        if not self._solution_path:
            return
        if self._step_index > 0:
            self._step_index -= 1
            self.iteration_var.set(str(self._step_index))
            self._render_board(self._solution_path[self._step_index])

    # ==================================================================
    # Free-run (Part II e)
    # ==================================================================

    def _start_run(self):
        if not self._solution_path:
            self.status_var.set("Run 'Solve' first.")
            return
        if self._running:
            return
        self._running     = True
        self._paused      = False
        self._cancel_flag = False
        self.run_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self._step_index = 0

        def animate():
            while self._step_index < len(self._solution_path) - 1:
                if self._cancel_flag:
                    break
                if self._paused:
                    time.sleep(0.1)
                    continue
                self._step_index += 1
                self.after(0, lambda idx=self._step_index:
                           self._free_run_tick(idx))
                time.sleep(0.35)   # 350 ms per frame

            self.after(0, self._run_finished)

        self._run_thread = threading.Thread(target=animate, daemon=True)
        self._run_thread.start()

    def _free_run_tick(self, idx):
        self.iteration_var.set(str(idx))
        self._render_board(self._solution_path[idx])
        if idx == len(self._solution_path) - 1:
            self.status_var.set("Goal reached!")

    def _pause_run(self):
        self._paused = not self._paused
        self.pause_btn.configure(
            text="▷  Resume" if self._paused else "⏸  Pause")
        self.status_var.set(
            "Paused." if self._paused else "Resumed.")

    def _cancel_run(self):
        self._cancel_flag = True
        self.status_var.set("Cancelled.")

    def _run_finished(self):
        self._running = False
        self._paused  = False
        self.run_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled",
                                 text="⏸  Pause")
        self.stop_btn.configure(state="disabled")

    # ==================================================================
    # Helpers
    # ==================================================================

    def _reset_stats(self):
        self.nodes_var.set("–")
        self.moves_var.set("–")
        self.time_var.set("–")
        self.iteration_var.set("0")
        self.status_var.set("Ready.")
