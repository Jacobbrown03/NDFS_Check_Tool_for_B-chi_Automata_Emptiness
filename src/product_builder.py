# Build reachable product states:
# (ts_state, ba_state)
# and product transitions.

from collections import deque
from src.structures import TransitionSystem, BuchiAutomaton, ProductAutomaton


def build_product(ts: TransitionSystem, ba: BuchiAutomaton) -> ProductAutomaton:
    initial_label = ts.label_of(ts.initial_state)
    initial_ba_states = ba.next_states(ba.initial_state, initial_label)

    # If the BA has no valid transition on the initial TS label,
    # the product is empty.
    if not initial_ba_states:
        return ProductAutomaton(
            states=set(),
            initial_states=set(),
            accepting_states=set(),
            transitions={},
        )

    initial_products = {(ts.initial_state, q) for q in initial_ba_states}

    states = set(initial_products)
    transitions: dict[tuple[str, str], set[tuple[str, str]]] = {}
    accepting = set()

    queue = deque(initial_products)

    while queue:
        current_ts, current_ba = queue.popleft()
        current = (current_ts, current_ba)

        if current_ba in ba.accepting_states:
            accepting.add(current)

        succs = set()
        for ts_next in ts.successors(current_ts):
            label = ts.label_of(ts_next)
            ba_next_states = ba.next_states(current_ba, label)

            for ba_next in ba_next_states:
                prod_next = (ts_next, ba_next)
                succs.add(prod_next)

                if prod_next not in states:
                    states.add(prod_next)
                    queue.append(prod_next)

        transitions[current] = succs

    return ProductAutomaton(
        states=states,
        initial_states=initial_products,
        accepting_states=accepting,
        transitions=transitions,
    )


