# Implements the nested depth-first search.
# Centerpiece of the project

from src.structures import ProductAutomaton, ProductState, NDFSResult


def run_ndfs(product: ProductAutomaton) -> NDFSResult:
    visited_blue: set[ProductState] = set()
    visited_red: set[ProductState] = set()
    parent_blue: dict[ProductState, ProductState | None] = {}
    cycle_found = {"value": False}
    witness_prefix: list[ProductState] = []
    witness_cycle: list[ProductState] = []

    def build_prefix(state: ProductState) -> list[ProductState]:
        path = []
        cur = state
        while cur is not None:
            path.append(cur)
            cur = parent_blue.get(cur)
        path.reverse()
        return path

    def red_dfs(start: ProductState, state: ProductState, stack: list[ProductState]) -> bool:
        visited_red.add(state)
        stack.append(state)

        for nxt in product.successors(state):
            if nxt == start:
                stack.append(nxt)
                return True
            if nxt not in visited_red:
                if red_dfs(start, nxt, stack):
                    return True

        stack.pop()
        return False

    def blue_dfs(state: ProductState, parent: ProductState | None) -> bool:
        visited_blue.add(state)
        parent_blue[state] = parent

        for nxt in product.successors(state):
            if nxt not in visited_blue:
                if blue_dfs(nxt, state):
                    return True

        if state in product.accepting_states:
            red_stack: list[ProductState] = []
            visited_red.clear()
            if red_dfs(state, state, red_stack):
                witness_prefix.extend(build_prefix(state))
                witness_cycle.extend(red_stack)
                cycle_found["value"] = True
                return True

        return False

    if product.initial_state in product.states:
        blue_dfs(product.initial_state, None)

    return NDFSResult(
        accepting_cycle_found=cycle_found["value"],
        witness_prefix=witness_prefix,
        witness_cycle=witness_cycle,
        visited_blue=visited_blue,
        visited_red=visited_red,
    )

