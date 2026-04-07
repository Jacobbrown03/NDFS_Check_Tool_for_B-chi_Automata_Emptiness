# This is where we save time
# Instead of implementing a full generic LTL-to-Buchi translation,
# we'll implement pattern-based Buchi generation for the formula 
# forms we support
# For example, if the negated formula is one of:
# F p
# G p
# p U g
# F (p && G(!q))
# G(p -> F q)
# We generate the automaton directly

from itertools import chain, combinations
from src.ast_nodes import Atomic, Not, And, Or, X, F, G, U, Formula
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
    if isinstance(formula, (And, Or, U)):
        return collect_atomic_props(formula.left) | collect_atomic_props(formula.right)
    if isinstance(formula, (X, F, G)):
        return collect_atomic_props(formula.child)
    return set()


def eval_state_predicate(formula: Formula, label: set[str]) -> bool:
    if isinstance(formula, Atomic):
        return formula.name in label
    if isinstance(formula, Not):
        return not eval_state_predicate(formula.child, label)
    if isinstance(formula, And):
        return eval_state_predicate(formula.left, label) and eval_state_predicate(formula.right, label)
    if isinstance(formula, Or):
        return eval_state_predicate(formula.left, label) or eval_state_predicate(formula.right, label)
    raise ValueError("Expected a state predicate")


def build_buchi_for_negated_formula(formula: Formula) -> BuchiAutomaton:
    aps = collect_atomic_props(formula)
    alphabet = set(powerset(aps))

    # Pattern 1: F p
    if isinstance(formula, F):
        p = formula.child
        return _build_F_predicate_buchi(p, alphabet)

    # Pattern 2: G p
    if isinstance(formula, G):
        p = formula.child
        return _build_G_predicate_buchi(p, alphabet)

    # Pattern 3: p U q
    if isinstance(formula, U):
        return _build_U_buchi(formula.left, formula.right, alphabet)

    # Pattern 4: F(G p)
    if isinstance(formula, F) and isinstance(formula.child, G):
        return _build_FG_buchi(formula.child.child, alphabet)

    # Pattern 5: G(F p)
    if isinstance(formula, G) and isinstance(formula.child, F):
        return _build_GF_buchi(formula.child.child, alphabet)

    # Pattern 6: F(p && G(q))   useful after negation of G(p -> F q)
    if isinstance(formula, F) and isinstance(formula.child, And):
        left = formula.child.left
        right = formula.child.right
        if isinstance(right, G):
            return _build_F_and_G_buchi(left, right.child, alphabet)

    raise NotImplementedError(f"No Büchi pattern implemented for: {formula.to_string()}")


def _build_F_predicate_buchi(p: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
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
    states = {"q0", "dead"}
    transitions = {}
    for label in alphabet:
        if eval_state_predicate(p, set(label)):
            transitions[("q0", label)] = {"q0"}
        else:
            transitions[("q0", label)] = {"dead"}
        transitions[("dead", label)] = {"dead"}
    return BuchiAutomaton(states, "q0", {"q0"}, transitions, alphabet)


def _build_U_buchi(p: Formula, q: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    states = {"q0", "q1", "dead"}
    transitions = {}
    for label in alphabet:
        s = set(label)
        if eval_state_predicate(q, s):
            transitions[("q0", label)] = {"q1"}
        elif eval_state_predicate(p, s):
            transitions[("q0", label)] = {"q0"}
        else:
            transitions[("q0", label)] = {"dead"}

        transitions[("q1", label)] = {"q1"}
        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)


def _build_FG_buchi(p: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    states = {"q0", "q1", "dead"}
    transitions = {}
    for label in alphabet:
        s = set(label)
        transitions[("q0", label)] = {"q0", "q1"}  # nondeterministically guess start of forever region
        if eval_state_predicate(p, s):
            transitions[("q1", label)] = {"q1"}
        else:
            transitions[("q1", label)] = {"dead"}
        transitions[("dead", label)] = {"dead"}
    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)


def _build_GF_buchi(p: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    states = {"q0", "q1"}
    transitions = {}
    for label in alphabet:
        s = set(label)
        if eval_state_predicate(p, s):
            transitions[("q0", label)] = {"q1"}
            transitions[("q1", label)] = {"q1"}
        else:
            transitions[("q0", label)] = {"q0"}
            transitions[("q1", label)] = {"q0"}
    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)


def _build_F_and_G_buchi(p: Formula, q: Formula, alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    states = {"q0", "q1", "dead"}
    transitions = {}
    for label in alphabet:
        s = set(label)
        transitions[("q0", label)] = {"q0"}
        if eval_state_predicate(p, s) and eval_state_predicate(q, s):
            transitions[("q0", label)].add("q1")

        if eval_state_predicate(q, s):
            transitions[("q1", label)] = {"q1"}
        else:
            transitions[("q1", label)] = {"dead"}

        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)
