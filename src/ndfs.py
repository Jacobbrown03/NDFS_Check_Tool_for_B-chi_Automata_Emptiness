from typing import List, Set, Dict
from src.structures import ProductAutomaton, ProductState, NDFSResult


def run_ndfs(product: ProductAutomaton) -> NDFSResult:
    """
    Perform the classic Nested-Depth-First Search (NDFS) emptiness check
    on a product automaton.
    
    The algorithm consists of two DFS phases:
    * **Blue (outer) DFS** - Explores the whole reachable part of the product,
      building a recursion stack ``blue_stack`` that represents the current
      search path.
    * **Red (inner) DFS** - Triggered only when the blue DFS backs-up from an
      accepting state. It searches *inside* the sub-graph induced by the
      current blue stack to see whether the accepting state participates in a
      reachable SCC (i.e. an accepting cycle).
      
    If such a cycle is found the function returns an ``NDFSResult`` containing
    a concrete counter-example (prefix + loop) and the sets of visisted states.
    """
    # ---------------------------------------------------------------------
    # Global data (blue phase)
    # ---------------------------------------------------------------------
    visited_blue: Set[ProductState] = set()
    blue_stack: List[ProductState] = []
    parent_blue: Dict[ProductState, ProductState | None] = {}

    # Witness Structures - Filled only when an accepting cycle is discovered.
    witness_prefix: List[ProductState] = []
    witness_cycle: List[ProductState] = []

    # ---------------------------------------------------------------------
    # Helper: Reconstruct the prefix (initial -> start_of_cycle)
    # ---------------------------------------------------------------------
    def prefix_to(state: ProductState) -> List[ProductState]:
        """
        Return the simple path from the root of the current blue stack to *state*
        (inclusive). The ``parent_blue`` map stores each node's predecessor,
        allowing us to walk backwards and then reverse the list.
        """
        path: List[ProductState] = []
        cur: ProductState | None = state
        while cur is not None:
            path.append(cur)
            cur = parent_blue.get(cur)
        path.reverse()
        return path

    # ---------------------------------------------------------------------
    # Inner (red) DFS – confined to the current blue stack
    # ---------------------------------------------------------------------
    def red_dfs(start: ProductState,
                cur: ProductState,
                red_visited: Set[ProductState],
                red_stack: List[ProductState]) -> bool:
        """
        DFS that stays inside the set of states currently on ``blue_stack``.
        It returns ``True`` as soon as it reaches ``start`` again, i.e. a
        cycle containing the accepting state has been found.
        
        Parameters
        ----------
        start : ProductState
            The accepting state that triggered this red search.
        cur : ProductState
            The node currently being explored.
        red_visited : set
            States visited by this particular red DFS (local to the call).
        red_stack : list
            Recursion stack for the red DFS - used only for cycle reconstruction.
        """
        red_visited.add(cur)
        red_stack.append(cur)

        for nxt in product.successors(cur):
            # Restrict the search to the SCC under exploration
            if nxt not in blue_stack:
                continue
            if nxt == start:            # Cycle closed
                red_stack.append(nxt)   # add the start again to close the loop
                return True
            if nxt not in red_visited:
                if red_dfs(start, nxt, red_visited, red_stack):
                    return True

        red_stack.pop()     # Backtrack
        return False

    # ---------------------------------------------------------------------
    # Outer (blue) DFS
    # ---------------------------------------------------------------------
    def blue_dfs(state: ProductState, parent: ProductState | None) -> bool:
        """
        Standard DFS that populates ``visited_blue`` and maintains ``blue_stack``.
        When back-tracking from an accepting state we invoke the red DFS.
        """
        visited_blue.add(state)
        parent_blue[state] = parent
        blue_stack.append(state)

        # Explore successors recursively
        for nxt in product.successors(state):
            if nxt not in visited_blue:
                if blue_dfs(nxt, state):
                    return True

        # ---------------------------------------------------------------------
        # Back‑track: If the current node is accepting, launch a red search
        # ---------------------------------------------------------------------
        if state in product.accepting_states:
            red_visited: Set[ProductState] = set()
            red_stack: List[ProductState] = []

            if red_dfs(state, state, red_visited, red_stack):
                # Build witness: prefix + cycle
                witness_prefix.extend(prefix_to(state))
                # red_stack is [start, …, start] – drop the duplicated start at the end
                witness_cycle.extend(red_stack[:-1])
                return True

        blue_stack.pop()
        return False

    # ---------------------------------------------------------------------
    # Launch the outer DFS from every initial product state
    # ---------------------------------------------------------------------
    for init in product.initial_states:
        if init not in visited_blue:
            if blue_dfs(init, None):
                break   # Stop as soon as a counter-example is found.

    return NDFSResult(
        accepting_cycle_found=bool(witness_cycle),   # True iff accepting cycle found
        witness_prefix=witness_prefix,
        witness_cycle=witness_cycle,
        visited_blue=visited_blue,
        # ``visited_red`` is left empty on purpose - red visits are local
        # to each accepting-state invocation and are not needed globally.
        visited_red=set(),
    )
