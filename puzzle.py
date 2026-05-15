"""
puzzle.py - N-Puzzle State Representation
==========================================
Represents the state of an N-puzzle of configurable size L (L x L grid).
The board is stored as a flat list of integers; 0 represents the blank tile.
This module is intentionally decoupled from any particular search algorithm
so that the same puzzle representation can be used with any solver.
"""

import random
import copy


class PuzzleState:
    """
    Encapsulates a single configuration (state) of an L x L sliding-tile puzzle.

    Attributes
    ----------
    board : list[int]
        Flat (1-D) list of length L*L.  0 denotes the blank tile.
    size  : int
        Side length L of the puzzle (e.g. 3 for the 8-puzzle).
    parent : PuzzleState | None
        The state from which this state was generated (back-pointer for path
        reconstruction).
    move   : str | None
        The move applied to the parent to reach this state
        ('UP', 'DOWN', 'LEFT', 'RIGHT' from the blank's perspective).
    depth  : int
        Number of moves from the initial state (= g-cost when all moves cost 1).
    g_cost : int
        Accumulated path cost (same as depth for unit-cost puzzles; kept
        separate for possible future use with non-uniform costs).
    """

    def __init__(self, board, size, parent=None, move=None, depth=0, g_cost=0):
        self.board  = list(board)   # defensive copy
        self.size   = size
        self.parent = parent
        self.move   = move
        self.depth  = depth
        self.g_cost = g_cost
        # Cache blank position for fast successor generation
        self.blank_pos = self.board.index(0)

    # ------------------------------------------------------------------
    # Equality / hashing (based on board content only, not bookkeeping)
    # ------------------------------------------------------------------
    def __eq__(self, other):
        return isinstance(other, PuzzleState) and self.board == other.board

    def __hash__(self):
        return hash(tuple(self.board))

    def __lt__(self, other):
        """Needed so PuzzleState objects can be stored in a heap."""
        return self.g_cost < other.g_cost

    def __str__(self):
        rows = self.board_2d()
        return '\n'.join(
            ' '.join(str(x) if x != 0 else '_' for x in row)
            for row in rows
        )

    def __repr__(self):
        return f"PuzzleState({self.board}, depth={self.depth})"

    # ------------------------------------------------------------------
    # Board helpers
    # ------------------------------------------------------------------
    def board_2d(self):
        """Return the board as a 2-D list (list of rows)."""
        return [
            self.board[i * self.size:(i + 1) * self.size]
            for i in range(self.size)
        ]

    # ------------------------------------------------------------------
    # Successor generation  (Part III requirement)
    # ------------------------------------------------------------------
    def successors(self):
        """
        Generate all reachable states from the current state by sliding
        an adjacent tile into the blank position.

        The function is size-agnostic: it works for any L x L puzzle.

        Returns
        -------
        list of (move_name: str, new_state: PuzzleState)
            Each element is a (move, successor) pair where *move* describes
            the direction the blank tile moves.
        """
        result   = []
        b_row    = self.blank_pos // self.size
        b_col    = self.blank_pos %  self.size

        # (move name, row-delta, col-delta) for the blank tile
        directions = [
            ('UP',    -1,  0),
            ('DOWN',   1,  0),
            ('LEFT',   0, -1),
            ('RIGHT',  0,  1),
        ]

        for move_name, dr, dc in directions:
            new_row = b_row + dr
            new_col = b_col + dc

            # Boundary check
            if 0 <= new_row < self.size and 0 <= new_col < self.size:
                new_board     = list(self.board)          # shallow copy
                new_blank_pos = new_row * self.size + new_col
                # Swap blank with the neighbouring tile
                new_board[self.blank_pos], new_board[new_blank_pos] = \
                    new_board[new_blank_pos], new_board[self.blank_pos]

                child = PuzzleState(
                    board   = new_board,
                    size    = self.size,
                    parent  = self,
                    move    = move_name,
                    depth   = self.depth  + 1,
                    g_cost  = self.g_cost + 1,
                )
                result.append((move_name, child))

        return result

    # ------------------------------------------------------------------
    # Path reconstruction
    # ------------------------------------------------------------------
    def get_path(self):
        """
        Walk back-pointers to reconstruct the sequence of states from the
        initial state to *self*.

        Returns
        -------
        list[PuzzleState]
            Ordered list starting at the root and ending at *self*.
        """
        path, node = [], self
        while node is not None:
            path.append(node)
            node = node.parent
        return list(reversed(path))

    # ------------------------------------------------------------------
    # Goal / solvability utilities
    # ------------------------------------------------------------------
    @staticmethod
    def generate_goal(size):
        """
        Return the canonical goal state for an L x L puzzle:
            1  2  3  … L²-1
            (blank)
        """
        tiles = list(range(1, size * size)) + [0]
        return PuzzleState(tiles, size)

    @staticmethod
    def generate_random(size):
        """
        Return a *solvable* random puzzle state of the given size.
        Shuffles until a solvable permutation is found.
        """
        tiles = list(range(size * size))
        while True:
            random.shuffle(tiles)
            state = PuzzleState(tiles, size)
            if state.is_solvable():
                return state

    def is_solvable(self):
        """
        Determine whether this puzzle configuration can reach the goal state.

        For odd-width grids  : solvable iff the inversion count is even.
        For even-width grids : solvable iff
            (blank row from bottom + inversion count) is odd.
        """
        flat = [x for x in self.board if x != 0]
        inversions = sum(
            1
            for i in range(len(flat))
            for j in range(i + 1, len(flat))
            if flat[i] > flat[j]
        )

        if self.size % 2 == 1:           # odd grid (3x3, 5x5, …)
            return inversions % 2 == 0
        else:                            # even grid (4x4, …)
            blank_row_from_bottom = self.size - (self.blank_pos // self.size)
            return (blank_row_from_bottom % 2 == 0) != (inversions % 2 == 0)

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------
    @staticmethod
    def from_file(filename):
        """
        Load a puzzle state from a plain-text file.

        File format (one row per line, values space-separated, 0 = blank):
            2 3 5
            0 7 8
            6 1 4
        Lines starting with '#' and blank lines are ignored.
        The puzzle size L is inferred from the first data row.
        """
        board, size = [], None
        with open(filename, 'r') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                row = list(map(int, line.split()))
                if size is None:
                    size = len(row)
                board.extend(row)

        if size is None or len(board) != size * size:
            raise ValueError(
                f"Invalid puzzle file: expected {size}x{size} = {size*size} "
                f"values, got {len(board)}."
            )
        return PuzzleState(board, size)

    @staticmethod
    def from_flat_list(flat, size):
        """Convenience constructor from a flat list."""
        return PuzzleState(flat, size)
