"""
algorithms.py - Search Algorithms for the N-Puzzle
====================================================
Implements four search strategies discussed in Russell & Norvig:
  1. Breadth-First Search   (BFS)
  2. Depth-First Search     (DFS)  – with cycle checking & depth cap
  3. Iterative-Deepening Search (IDS)
  4. A* Search              – with pluggable heuristic functions

All solvers share the same return signature:
    (path, nodes_expanded, elapsed_seconds)

where:
    path           : list[PuzzleState] from start to goal (None if unsolvable)
    nodes_expanded : int  – number of nodes popped from the frontier
    elapsed_seconds: float
"""

from collections import deque
import heapq
import time

from puzzle import PuzzleState


# ======================================================================
# Part IV – Breadth-First Search
# ======================================================================

def bfs(initial_state: PuzzleState, goal_state: PuzzleState):
    """
    Breadth-First Search (BFS).

    Explores states level by level using a FIFO queue.
    Guaranteed to find the *shortest* path (fewest moves).

    Complexity:
        Time  : O(b^d)   where b = branching factor, d = solution depth
        Space : O(b^d)   – stores entire frontier + explored set

    Returns
    -------
    (path, nodes_expanded, elapsed_seconds)
    """
    t0 = time.time()

    # FIFO frontier
    frontier  = deque([initial_state])
    # Explored set keyed by board tuple to avoid revisiting states
    explored  = {hash(initial_state)}
    nodes_expanded = 0

    while frontier:
        state = frontier.popleft()   # FIFO → breadth-first order
        nodes_expanded += 1

        # Goal test
        if state.board == goal_state.board:
            return state.get_path(), nodes_expanded, time.time() - t0

        # Expand: generate successors and add unseen ones to frontier
        for _, child in state.successors():
            h = hash(child)
            if h not in explored:
                explored.add(h)
                frontier.append(child)

    # No solution found
    return None, nodes_expanded, time.time() - t0


# ======================================================================
# Part V – Depth-First Search
# ======================================================================

def dfs(initial_state: PuzzleState, goal_state: PuzzleState,
        max_depth: int = 100):
    """
    Depth-First Search (DFS) with cycle checking and a depth cap.

    WHY THE FIX IS NEEDED
    ----------------------
    In its simplest (tree-search) form DFS can revisit states, creating
    infinite loops on graph-search problems like the sliding puzzle.
    Two complementary fixes are applied here:
      1. *Explored set*  – prevents revisiting any state already processed.
      2. *Depth cap*     – bounds the search to `max_depth` moves, giving
         an upper limit on memory/time even when the goal is unreachable.

    Note: DFS does NOT guarantee an optimal (shortest) path.

    Returns
    -------
    (path, nodes_expanded, elapsed_seconds)
    """
    t0 = time.time()

    frontier = [initial_state]       # LIFO stack → depth-first order
    explored = set()
    nodes_expanded = 0

    while frontier:
        state = frontier.pop()       # LIFO

        s_hash = hash(state)
        if s_hash in explored:
            continue
        explored.add(s_hash)
        nodes_expanded += 1

        if state.board == goal_state.board:
            return state.get_path(), nodes_expanded, time.time() - t0

        # Only expand if we haven't exceeded the depth cap
        if state.depth < max_depth:
            # Push in reverse order so that the first successor
            # is processed first (consistent ordering)
            for _, child in reversed(state.successors()):
                if hash(child) not in explored:
                    frontier.append(child)

    return None, nodes_expanded, time.time() - t0


# ======================================================================
# Part VI – Iterative-Deepening Search (IDS)
# ======================================================================

def ids(initial_state: PuzzleState, goal_state: PuzzleState,
        max_limit: int = 150):
    """
    Iterative-Deepening Depth-First Search (IDS / IDDFS).

    Runs depth-limited DFS with increasing depth limits (0, 1, 2, …)
    until the goal is found.  Combines the space-efficiency of DFS with
    BFS's optimality guarantee.

    nodes_expanded counts *total* nodes across **all** depth iterations,
    which shows the overhead of re-expansion.

    Returns
    -------
    (path, nodes_expanded, elapsed_seconds)
    """
    t0 = time.time()
    total_nodes = 0

    for limit in range(max_limit + 1):
        result, nodes = _depth_limited_search(initial_state, goal_state, limit)
        total_nodes += nodes

        if result not in (None, 'cutoff'):
            return result.get_path(), total_nodes, time.time() - t0

        # 'cutoff'  → limit was too shallow, increase
        # None      → all paths exhausted at this limit (unsolvable)
        if result is None:
            break

    return None, total_nodes, time.time() - t0


def _depth_limited_search(initial_state, goal_state, limit):
    """
    Recursive depth-limited search helper used by IDS.

    Returns (node_or_status, nodes_expanded) where node_or_status is:
        PuzzleState  – goal reached
        'cutoff'     – depth limit reached before finding goal
        None         – failure (no solution within limit)
    """
    nodes_expanded = [0]   # mutable container so the closure can increment it

    def rdls(state, limit):
        nodes_expanded[0] += 1

        if state.board == goal_state.board:
            return state          # GOAL

        if limit == 0:
            return 'cutoff'       # hit depth limit

        cutoff_hit = False

        for _, child in state.successors():
            # Cycle check: walk back-pointers to avoid revisiting ancestors
            ancestor = state.parent
            is_cycle = False
            while ancestor is not None:
                if ancestor.board == child.board:
                    is_cycle = True
                    break
                ancestor = ancestor.parent
            if is_cycle:
                continue

            result = rdls(child, limit - 1)

            if result == 'cutoff':
                cutoff_hit = True
            elif result is not None:
                return result     # propagate success upward

        return 'cutoff' if cutoff_hit else None

    outcome = rdls(initial_state, limit)
    return outcome, nodes_expanded[0]


# ======================================================================
# Part VII – Heuristic Functions
# ======================================================================

def heuristic_misplace(state: PuzzleState, goal_state: PuzzleState) -> int:
    """
    Misplaced-tiles heuristic h1.

    Counts the number of tiles that are *not* in their goal position
    (the blank is excluded).

    Admissible: each misplaced tile needs at least 1 move ⇒ h1 ≤ h*.
    Consistent: moving one tile changes the misplace count by at most 1.
    """
    return sum(
        1
        for i, tile in enumerate(state.board)
        if tile != 0 and tile != goal_state.board[i]
    )


def heuristic_manhattan(state: PuzzleState, goal_state: PuzzleState) -> int:
    """
    Manhattan-distance heuristic h2.

    For each non-blank tile, computes the sum of horizontal + vertical
    distances to its goal position.

    Admissible: each unit of Manhattan distance requires at least 1 move.
    Consistent: moving one tile changes its Manhattan distance by 1.
    Dominates h1: h2(n) ≥ h1(n) for all n, so A* with h2 expands ≤
                  nodes compared with h1.
    """
    size = state.size
    # Pre-build goal position lookup: tile → (row, col)
    goal_pos = {
        tile: (i // size, i % size)
        for i, tile in enumerate(goal_state.board)
    }

    total = 0
    for i, tile in enumerate(state.board):
        if tile != 0:
            cur_row, cur_col   = i // size, i % size
            goal_row, goal_col = goal_pos[tile]
            total += abs(cur_row - goal_row) + abs(cur_col - goal_col)
    return total


# ======================================================================
# Part VII – A* Search
# ======================================================================

def astar(initial_state: PuzzleState, goal_state: PuzzleState,
          heuristic_func):
    """
    A* Search with a pluggable heuristic function.

    Priority queue ordered by f(n) = g(n) + h(n).
    Uses a best-g dict to prune dominated paths.

    Parameters
    ----------
    heuristic_func : callable(state, goal_state) → int
        Any admissible heuristic.  The two standard choices are
        `heuristic_misplace` and `heuristic_manhattan`.

    Returns
    -------
    (path, nodes_expanded, elapsed_seconds)
    """
    t0 = time.time()

    h0      = heuristic_func(initial_state, goal_state)
    counter = 0    # tie-breaker ensures FIFO ordering for equal f-values

    # heap entries: (f_cost, counter, state)
    frontier = [(h0, counter, initial_state)]
    heapq.heapify(frontier)

    # Best g-cost discovered so far for each state hash
    best_g = {hash(initial_state): 0}

    nodes_expanded = 0

    while frontier:
        f, _, state = heapq.heappop(frontier)

        # Optimality check: if we already found a better path, skip
        if state.g_cost > best_g.get(hash(state), float('inf')):
            continue

        nodes_expanded += 1

        if state.board == goal_state.board:
            return state.get_path(), nodes_expanded, time.time() - t0

        for _, child in state.successors():
            c_hash  = hash(child)
            new_g   = child.g_cost

            if new_g < best_g.get(c_hash, float('inf')):
                best_g[c_hash] = new_g
                h       = heuristic_func(child, goal_state)
                f_child = new_g + h
                counter += 1
                heapq.heappush(frontier, (f_child, counter, child))

    return None, nodes_expanded, time.time() - t0
