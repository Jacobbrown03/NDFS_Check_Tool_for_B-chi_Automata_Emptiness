# Parses the traffic-light graph file
# Responsibilities:
# States
# Transitions
# Initial State
# Proposition Labels

from src.structures import TransitionSystem


def load_model(path: str) -> TransitionSystem:
    transitions: dict[str, set[str]] = {}
    labels: dict[str, set[str]] = {}
    states: set[str] = set()
    accepting_states: set[str] = set()
    initial_state: str | None = None

    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    for line in lines:
        if line.startswith("accept:"):
            rest = line.split(":", 1)[1].strip()
            accepting_states = set(rest.split()) if rest else set()
        elif line.startswith("init:"):
            initial_state = line.split(":", 1)[1].strip()
        elif ":" in line:
            state, props = line.split(":", 1)
            state = state.strip()
            prop_set = set(props.strip().split()) if props.strip() else set()
            labels[state] = prop_set
            states.add(state)
        else:
            parts = line.split()
            if len(parts) >= 2:
                src = parts[0]
                dsts = set(parts[1:])
                transitions[src] = dsts
                states.add(src)
                states.update(dsts)

    if initial_state is None:
        raise ValueError("Model file is missing an init: line")

    for s in states:
        transitions.setdefault(s, set())
        labels.setdefault(s, set())

    return TransitionSystem(
        states=states,
        transitions=transitions,
        initial_state=initial_state,
        labels=labels,
        accepting_states=accepting_states,
    )