from itertools import combinations
from src.ast_nodes import Atomic, Not, And, Or, X, F, G, Formula
from src.structures import BuchiAutomaton


def powerset(items: set[str]) -> list[frozenset[str]]:
    values = list(items)
    return [
        frozenset(combo)
        for r in range(len(values) + 1)
        for combo in combinations(values, r)
    ]


def collect_atomic_props(formula: Formula) -> set[str]:
    if isinstance(formula, Atomic):
        return {formula.name}
    if isinstance(formula, Not):
        return collect_atomic_props(formula.child)
    if isinstance(formula, (And, Or)):
        return collect_atomic_props(formula.left) | collect_atomic_props(formula.right)
    if isinstance(formula, (X, F, G)):
        return collect_atomic_props(formula.child)
    return set()


def eval_state_predicate(formula: Formula, label: set[str]) -> bool:
    """
    Evaluate a formula as a pure state predicate over one TS label.
    Supported here: Atomic, Not, And, Or.
    Implication should already have been eliminated before this stage.
    """
    if isinstance(formula, Atomic):
        return formula.name in label
    if isinstance(formula, Not):
        return not eval_state_predicate(formula.child, label)
    if isinstance(formula, And):
        return eval_state_predicate(formula.left, label) and eval_state_predicate(formula.right, label)
    if isinstance(formula, Or):
        return eval_state_predicate(formula.left, label) or eval_state_predicate(formula.right, label)

    raise ValueError(f"Expected a state predicate, got: {type(formula).__name__}")


def build_buchi_for_negated_formula(formula: Formula) -> BuchiAutomaton:
    """
    Build a Büchi automaton for a restricted set of negated LTL patterns.

    Supported patterns:
      - F p
      - G p
      - X p
      - F(G p)
      - G(F p)
      - F(p && G(q))
      - F(p && X(q))

    where p and q are state predicates.
    """
    aps = collect_atomic_props(formula)
    alphabet = set(powerset(aps))

    # Pattern 1: X p
    if isinstance(formula, X):
        return _build_X_predicate_buchi(formula.child, alphabet)

    # Pattern 2: F p
    if isinstance(formula, F):
        child = formula.child

        # Pattern 2a: F(G p)
        if isinstance(child, G):
            return _build_FG_buchi(child.child, alphabet)

        # Pattern 2b: F(p && G(q))
        if isinstance(child, And):
            left = child.left
            right = child.right

            if isinstance(right, G):
                return _build_F_and_G_buchi(left, right.child, alphabet)

            # Pattern 2c: F(p && X(q))
            if isinstance(right, X):
                return _build_F_and_X_buchi(left, right.child, alphabet)

        # Plain F p
        return _build_F_predicate_buchi(child, alphabet)

    # Pattern 3: G p
    if isinstance(formula, G):
        child = formula.child

        # Pattern 3a: G(F p)
        if isinstance(child, F):
            return _build_GF_buchi(child.child, alphabet)

        # Plain G p
        return _build_G_predicate_buchi(child, alphabet)

    raise NotImplementedError(f"No Büchi pattern implemented for: {formula.to_string()}")


def _build_F_predicate_buchi(p: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi for F p:
      q0 = waiting to see p
      q1 = p has been seen
    Accepting: q1
    """
    states = {"q0", "q1"}
    transitions = {} 

    for label in alphabet:
        if eval_state_predicate(p, set(label)):
            transitions[("q0", label)] = {"q1"}
        else:
            transitions[("q0", label)] = {"q0"}

        transitions[("q1", label)] = {"q1"}

    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)


def _build_G_predicate_buchi(p: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi for G p:
      q0 = still satisfying p forever
      dead = violation seen
    Accepting: q0
    """
    states = {"q0", "dead"}
    transitions = {}

    for label in alphabet:
        if eval_state_predicate(p, set(label)):
            transitions[("q0", label)] = {"q0"}
        else:
            transitions[("q0", label)] = {"dead"}

        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q0"}, transitions, alphabet)


def _build_X_predicate_buchi(p: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi for X p:
      q0 = before the next step
      q1 = checking the next state's label
      q_accept = next state satisfied p
      dead = next state violated p

    Accepting: q_accept
    """
    states = {"q0", "q1", "q_accept", "dead"}
    transitions = {}

    for label in alphabet:
        # First step: ignore current label and move to q1
        transitions[("q0", label)] = {"q1"}

        # Second step: evaluate p on the next state's label
        if eval_state_predicate(p, set(label)):
            transitions[("q1", label)] = {"q_accept"}
        else:
            transitions[("q1", label)] = {"dead"}

        transitions[("q_accept", label)] = {"q_accept"}
        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q_accept"}, transitions, alphabet)


def _build_FG_buchi(p: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi for F(G p):
      q0 = before guessing the start of the forever-p region
      q1 = inside the forever-p region
      dead = guessed wrong
    Accepting: q1
    """
    states = {"q0", "q1", "dead"}
    transitions = {}

    for label in alphabet:
        current_label = set(label)

        # Stay in q0, or nondeterministically guess that now begins the G p suffix
        transitions[("q0", label)] = {"q0", "q1"}

        if eval_state_predicate(p, current_label):
            transitions[("q1", label)] = {"q1"}
        else:
            transitions[("q1", label)] = {"dead"}

        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)


def _build_GF_buchi(p: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi for G(F p):
      q0 = waiting for next p
      q1 = just saw p
    Accepting: q1
    """
    states = {"q0", "q1"}
    transitions = {}

    for label in alphabet:
        current_label = set(label)

        if eval_state_predicate(p, current_label):
            transitions[("q0", label)] = {"q1"}
            transitions[("q1", label)] = {"q1"}
        else:
            transitions[("q0", label)] = {"q0"}
            transitions[("q1", label)] = {"q0"}

    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)


def _build_F_and_G_buchi(p: Formula, q: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi for F(p && G(q)):
      q0 = before the guessed violation point
      q1 = guessed point reached; now q must hold forever
      dead = q failed after the guess
    Accepting: q1
    """
    states = {"q0", "q1", "dead"}
    transitions = {}

    for label in alphabet:
        current_label = set(label)

        transitions[("q0", label)] = {"q0"}
        if eval_state_predicate(p, current_label) and eval_state_predicate(q, current_label):
            transitions[("q0", label)].add("q1")

        if eval_state_predicate(q, current_label):
            transitions[("q1", label)] = {"q1"}
        else:
            transitions[("q1", label)] = {"dead"}

        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)


def _build_F_and_X_buchi(p: Formula, q: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi for F(p && X q):
      q0 = waiting for a position where p holds and next state should satisfy q
      q1 = just saw such a p-position; now check q on the next input label
      q_accept = success
      dead = failed after making the guess

    Accepting: q_accept
    """
    states = {"q0", "q1", "q_accept", "dead"}
    transitions = {}

    for label in alphabet:
        current_label = set(label)

        # In q0 we can always keep waiting.
        next_states = {"q0"}

        # If p holds now, we may nondeterministically guess this is the position
        # whose next state should satisfy q.
        if eval_state_predicate(p, current_label):
            next_states.add("q1")

        transitions[("q0", label)] = next_states

        # In q1 we are now reading the next state's label, so q must hold here.
        if eval_state_predicate(q, current_label):
            transitions[("q1", label)] = {"q_accept"}
        else:
            transitions[("q1", label)] = {"dead"}

        transitions[("q_accept", label)] = {"q_accept"}
        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q_accept"}, transitions, alphabet)
        

