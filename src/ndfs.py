from __future__ import annotations
from typing import List, Set, Dict, Tuple
from src.structures import ProductAutomaton, ProductState, NDFSResult


def run_ndfs(product: ProductAutomaton) -> NDFSResult:
    """
    Classic nested‑DFS emptiness check.

    Returns:
        NDFSResult with:
            - accepting_cycle_found: True iff the product contains an
              accepting SCC (i.e. the negated LTL formula is realizable).
            - witness_prefix / witness_cycle: concrete counter‑example
              path + loop, if one was found.
            - visited_blue / visited_red: sets of states explored during
              the search (useful for debugging/visualisation).
    """

    # -----------------------------------------------------------------
    # Global data (blue phase)
    # -----------------------------------------------------------------
    visited_blue: Set[ProductState] = set()               # all states ever entered
    blue_stack: List[ProductState] = []                  # recursion stack of the outer DFS
    parent_blue: Dict[ProductState, ProductState | None] = {}

    # Witness that will be filled once a cycle is found
    witness_prefix: List[ProductState] = []
    witness_cycle: List[ProductState] = []

    # -----------------------------------------------------------------
    # Helper to reconstruct the prefix (initial → start_of_cycle)
    # -----------------------------------------------------------------
    def prefix_to(state: ProductState) -> List[ProductState]:
        """Return the simple path from the root of the current blue stack
        to *state* (inclusive). The stack already stores the ancestors."""
        path: List[ProductState] = []
        cur: ProductState | None = state
        while cur is not None:
            path.append(cur)
            cur = parent_blue.get(cur)
        path.reverse()
        return path

    # -----------------------------------------------------------------
    # Inner (red) DFS – confined to the current blue stack
    # -----------------------------------------------------------------
    def red_dfs(start: ProductState,
                cur: ProductState,
                red_visited: Set[ProductState],
                red_stack: List[ProductState]) -> bool:
        """Search only inside the set of states that belong to the
        current blue stack.  Return True as soon as *start* is hit again."""
        red_visited.add(cur)
        red_stack.append(cur)

        for nxt in product.successors(cur):
            # Stay inside the SCC that the outer DFS is currently exploring
            if nxt not in blue_stack:          # <-- crucial restriction
                continue
            if nxt == start:                    # cycle completed
                red_stack.append(nxt)
                return True
            if nxt not in red_visited:
                if red_dfs(start, nxt, red_visited, red_stack):
                    return True

        red_stack.pop()
        return False

    # -----------------------------------------------------------------
    # Outer (blue) DFS
    # -----------------------------------------------------------------
    def blue_dfs(state: ProductState, parent: ProductState | None) -> bool:
        visited_blue.add(state)
        parent_blue[state] = parent
        blue_stack.append(state)                # push on recursion stack

        for nxt in product.successors(state):
            if nxt not in visited_blue:
                if blue_dfs(nxt, state):
                    return True

        # -----------------------------------------------------------------
        # Back‑track: if the current node is accepting, launch a red search
        # -----------------------------------------------------------------
        if state in product.accepting_states:
            red_visited: Set[ProductState] = set()
            red_stack: List[ProductState] = []

            if red_dfs(state, state, red_visited, red_stack):
                # Build witness: prefix + cycle (the cycle already contains the start node at its end)
                witness_prefix.extend(prefix_to(state))
                # red_stack is [start, …, start] – drop the duplicated start at the end
                witness_cycle.extend(red_stack[:-1])
                return True

        blue_stack.pop()                         # pop on back‑track
        return False

    # -----------------------------------------------------------------
    # Launch the outer DFS from every initial product state
    # -----------------------------------------------------------------
    for init in product.initial_states:
        if init not in visited_blue:
            if blue_dfs(init, None):
                break

    return NDFSResult(
        accepting_cycle_found=bool(witness_cycle),   # True iff we found one
        witness_prefix=witness_prefix,
        witness_cycle=witness_cycle,
        visited_blue=visited_blue,
        visited_red=set(),          # we keep no global red set – it is local to each call
    )
