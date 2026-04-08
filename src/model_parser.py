"""model_parser.py

Helper that reads a textual dscription of a Transition System (TS) and
creates a :class:`~src.structures.TransitionSystem` instance.

The file format (a smal custom DSL) is line-oriented

- ``s t1 t2 ...``       - Declares outgoing edges from ``s`` to the
                          listed destination states
- ``accept: s1 s2 ...`` - Space-separated list of accepting states
- ``init: <state>``     - Declares the initial state.
- ``s: p q ...``        - Gives the set of Atomic Propositions that
                          hold in state ``s`` (the label of ``s``)
- Lines starting with ``#`` are comments and are ignored.

The parser builds the five components required by ``TransitionSystem``:
states, transitions, initial_state, labels, and accepting_states.
"""

from src.structures import TransitionSystem

def load_model(path: str) -> TransitionSystem:
    """Parse *path* and return a populated :class:`TransitionSystem`.
    
    Parameters
    ----------
    path: str
        Path to a model file following the DSL described in the module
        doc-string.
        
    Returns
    -------
    TransitionSystem
        An immutable representation of the parsed Transition System
        
    Raises
    ------
    ValueError
        If the file does not contain an ``init:`` line.
    """
    
    # Containers for the components required by TransitionSystem.
    states: set[str] = set()
    transitions: dict[str, set[str]] = {}
    initial_state: str | None = None
    labels: dict[str, set[str]] = {}
    accepting_states: set[str] = set()
    
    # ---------------------------------------------------------------------
    # [1] Read the file, strip wihitespace and drop comments / empty lines.
    # ---------------------------------------------------------------------
    with open(path, "r", encoding="utf-8") as f:
        lines = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]
    
    # ---------------------------------------------------------------------
    # [2] Process each remaining line according to its prefix.
    # ---------------------------------------------------------------------
    for line in lines:
        # ---- Accepting States -------------------------------------------
        if line.startswith("accept:"):
            # Everything after the colon are space-separated state names
            rest = line.split(":", 1)[1].strip()
            accepting_states = set(rest.split()) if rest else set()
            
        # ---- Initial State ----------------------------------------------
        elif line.startswith("init:"):
            # NOTE: It is assumed there is only one initial state.
            # Extract the state name after the colon
            initial_state = line.split(":", 1)[1].strip()
            
        # ---- State Label (Atomic Propositions) --------------------------
        elif ":" in line:
            # Format <state>: <prop1> <prop2> ...
            state, props = line.split(":", 1)
            state = state.strip()
            # An empty right-hand side means the state carries no propositions.
            prop_set = set(props.strip().split()) if props.strip() else set()
            labels[state] = prop_set
            states.add(state)
            
        # ---- Transition Definition --------------------------------------
        else:
            # Format: <src> <dst1> <dst2> ...
            parts = line.split()
            if len(parts) >= 2:
                src = parts[0]
                dsts = set(parts[1:])
                transitions[src] = dsts
                # Ensure both source and destinations are recorded as states.
                states.add(src)
                states.update(dsts)
    
    # ---------------------------------------------------------------------
    # [3] Validate the mandatory initial state.
    # ---------------------------------------------------------------------                
    if initial_state is None:
        raise ValueError("Model file is missing an init: line")
    
    # ---------------------------------------------------------------------
    # [4] Fill missing entries so every state has a transition set and a
    #     label, even if they are empty.
    for s in states:
        transitions.setdefault(s, set())
        labels.setdefault(s, set())
    
    # ---------------------------------------------------------------------
    # [5] Construct and return the immutable TransitionSystem object
    # ---------------------------------------------------------------------
    return TransitionSystem(
        states=states,
        transitions=transitions,
        initial_state=initial_state,
        labels=labels,
        accepting_states=accepting_states,
    )
    
