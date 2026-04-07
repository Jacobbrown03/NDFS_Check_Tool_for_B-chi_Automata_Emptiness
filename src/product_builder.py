# Build reachable product states:
# (ts_state, ba_state)
# and product transitions.

from collections import deque
from src.structures import TransitionSystem, BuchiAutomaton, ProductAutomaton


def build_product(ts: TransitionSystem, ba: BuchiAutomaton) -> ProductAutomaton:
    initial_label = ts.label_of(ts.initial_state)
    initial_ba_states = ba.next_states(ba.initial_state, initial_label)

    if not initial_ba_states:
        # no valid move from initial BA state with the initial TS label
        initial_product = (ts.initial_state, ba.initial_state)
        return ProductAutomaton(set(), initial_product, set(), {})

    initial_product = (ts.initial_state, next(iter(initial_ba_states)))

    states = set()
    transitions: dict[tuple[str, str], set[tuple[str, str]]] = {}
    accepting = set()

    queue = deque([initial_product])
    states.add(initial_product)

    while queue:
        current_ts, current_ba = queue.popleft()
        current = (current_ts, current_ba)

        if current_ba in ba.accepting_states:
            accepting.add(current)

        succs = set()
        for ts_next in ts.successors(current_ts):
            label = ts.label_of(ts_next)
            for ba_next in ba.next_states(current_ba, label):
                prod_next = (ts_next, ba_next)
                succs.add(prod_next)
                if prod_next not in states:
                    states.add(prod_next)
                    queue.append(prod_next)

        transitions[current] = succs

    return ProductAutomaton(
        states=states,
        initial_state=initial_product,
        accepting_states=accepting,
        transitions=transitions,
    )

