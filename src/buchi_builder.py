"""buchi_builder.py

Utility for constructing Buchi Automata that recognise the language of
negated LTL formulas. Only a small, fixed set of patters is supported.
Each pattern has a dedicated helper that creates the appropriate automaton
using the generic :class:`BuchiAutomaton` container from ``src.structures``
"""

from itertools import combinations
from src.ast_nodes import Atomic, Not, And, Or, X, F, G, Formula
from src.structures import BuchiAutomaton

# -------------------------------------------------------------------------
# Helper Utilities
# -------------------------------------------------------------------------
def powerset(items: set[str]) -> list[frozenset[str]]:
    """
    Compute the power-set of a set of atomic proposition names.
    The result is a list of *frozenset*, each representing one possible
    label (i.e. a subset of atomic propositions) that can appear on a
    transition system state.
    """
    values = list(items)
    return [
        frozenset(combo)
        for r in range(len(values) + 1)
        for combo in combinations(values, r)
    ]

def collect_atomic_props(formula: Formula) -> set[str]:
    """
    Recursively collect all atomic proposition names occuring in *formula*.
    Returns a set of strings (the proposition identifiers).
    """
    # Return Atomic Propositions
    if isinstance(formula, Atomic):
        return {formula.name}
    # Unary Temporal Operators - Propagate to the child
    if isinstance(formula, (X, F, G, Not)):
        return collect_atomic_props(formula.child)
    # Binary Operators - Union the names from both sides
    if isinstance(formula, (And, Or)):
        return collect_atomic_props(formula.left) | collect_atomic_props(formula.right)
    # Formula does not ontain any Atomic Propositions
    return set()

def eval_state_predicate(formula: Formula, label: set[str]) -> bool:
    """
    Evaluate a *pure state predicate* on a single TS label.
    Supported constructs are Atomic, Not, And, Or. Implication should have
    been eliminated earlier in the pipeline
    """
    if isinstance(formula, Atomic):
        return formula.name in label
    if isinstance(formula, Not):
        return not eval_state_predicate(formula.child, label)
    if isinstance(formula, And):
        return eval_state_predicate(formula.left, label) and \
               eval_state_predicate(formula.right, label)
    if isinstance(formula, Or):
        return eval_state_predicate(formula.left, label) or \
               eval_state_predicate(formula.right, label)
    raise ValueError(f"Expected a state predicate, got: {type(formula).__name__}")

# -------------------------------------------------------------------------
# Public Entry Point
# -------------------------------------------------------------------------
def build_buchi_for_negated_formula(formula: Formula) -> BuchiAutomaton:
    """
    Dispatch to the appropriate construction routine based on the
    syntactic shape of the *formula*. Only the patterns listed are
    recognised; otherwise a ``NotImplementedError`` is raised

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
    # Determine the alphabet from the Atomic Proposition that appear.
    aps = collect_atomic_props(formula)
    alphabet = set(powerset(aps))

    # ---------------------------------------------------------------------
    # Pattern 1: X p
    # ---------------------------------------------------------------------
    if isinstance(formula, X):
        return _build_X_predicate_buchi(formula.child, alphabet)

    # ---------------------------------------------------------------------
    # Pattern 2: F ...
    # ---------------------------------------------------------------------
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

    # ---------------------------------------------------------------------
    # Pattern 3: G ...
    # ---------------------------------------------------------------------
    if isinstance(formula, G):
        child = formula.child

        # Pattern 3a: G(F p)
        if isinstance(child, F):
            return _build_GF_buchi(child.child, alphabet)

        # Plain G p
        return _build_G_predicate_buchi(child, alphabet)

    # No supported pattern matched
    raise NotImplementedError(f"No Büchi pattern implemented for: {formula.to_string()}")

# -------------------------------------------------------------------------
# Construction Helpers - Each returns a fully initialised BuchiAutomaton
# -------------------------------------------------------------------------
def _build_F_predicate_buchi(p: Formula, 
                             alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi Automaton for the "eventually" pattern F p.
    
    States:
        q0 - waiting to see p
        q1 - p has been seen
    
    Accepting State:
        q1
    """
    states = {"q0", "q1"}
    transitions = {} 

    for label in alphabet:
        if eval_state_predicate(p, set(label)):
            # Observation of p moves us to the accepting state
            transitions[("q0", label)] = {"q1"}
        else:
            # Remain in the waiting state
            transitions[("q0", label)] = {"q0"}
        # Once accepting we stay there forever
        transitions[("q1", label)] = {"q1"}

    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)

def _build_G_predicate_buchi(p: Formula,
                             alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi Automaton for the "globally" pattern G p:
    
    States:
        q0 - p holds so far
        dead - a violation of p has been seen
    
    Accepting State:
        q0
    """
    states = {"q0", "dead"}
    transitions = {}

    for label in alphabet:
        if eval_state_predicate(p, set(label)):
            # Remain in acceptance state
            transitions[("q0", label)] = {"q0"}
        else:
            # Violation of p moves us to the dead state
            transitions[("q0", label)] = {"dead"}
        # Once dead, we stay there forever
        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q0"}, transitions, alphabet)

def _build_X_predicate_buchi(p: Formula,
                             alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi Automaton for the "next" pattern X p:
    
    States:
        q0 - Initial state (ignore current label)
        q1 - We are reading the *next* label
        q_accept - The next label satisfied p
        dead - The next label violated p

    Accepting State:
        q_accept
    """
    states = {"q0", "q1", "q_accept", "dead"}
    transitions = {}

    for label in alphabet:
        # From the start we unconditionally move to q1 on the next step
        transitions[("q0", label)] = {"q1"}

        # In q1 we evaluate p on the current label (which corresponds to the
        # original "next" step)
        if eval_state_predicate(p, set(label)):
            # Satisfaction of p moves us to the accept state
            transitions[("q1", label)] = {"q_accept"}
        else:
            # Violation of p moves us to the dead state
            transitions[("q1", label)] = {"dead"}
        # Once accepting or dead, we stay there forever
        transitions[("q_accept", label)] = {"q_accept"}
        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q_accept"}, transitions, alphabet)


def _build_FG_buchi(p: Formula,
                    alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi Automaton for the pattern F(G p):
    
    States:
        q0 - Before guessing the start of the forever-p region
        q1 - Inside the forever-p region
        dead - Guessed wrong
        
    Accepting State:
        q1
    """
    states = {"q0", "q1", "dead"}
    transitions = {}

    for label in alphabet:
        # Stay in q0, or nondeterministically guess that the G p suffix starts now
        transitions[("q0", label)] = {"q0", "q1"}

        if eval_state_predicate(p, set(label)):
            # p holds, we are in the "forever-p" region
            transitions[("q1", label)] = {"q1"}
        else:
            # Violation of p moves us to the dead state
            transitions[("q1", label)] = {"dead"}
        # Once dead, we stay there forever
        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)


def _build_GF_buchi(p: Formula,
                    alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi Automaton for the pattern G(F p):
    
    States: 
        q0 - We are waiting for the next occurrnce of p
        q1 - We have just seen p
        
    Accepting State:
        q1
    """
    states = {"q0", "q1"}
    transitions = {}

    for label in alphabet:
        if eval_state_predicate(p, set(label)):
            # Seeing p moves us to q1; q1 stats on any further lable
            transitions[("q0", label)] = {"q1"}
            transitions[("q1", label)] = {"q1"}
        else:
            # No p yet - remain in q0; if we were in q1 we must return to q0
            transitions[("q0", label)] = {"q0"}
            transitions[("q1", label)] = {"q0"}

    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)

def _build_F_and_G_buchi(p: Formula,
                         q: Formula,
                         alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi Automaton for the pattern F(p && G(q)):
    
    States:
        q0 - Before the guessed violation point
        q1 - Guessed point reached; now q must hold forever
        dead - q failed after the guess
    
    Accepting State:
        q1
    """
    states = {"q0", "q1", "dead"}
    transitions = {}

    for label in alphabet:
        # Always stay in q0 (or guess to move to q1)
        transitions[("q0", label)] = {"q0"}
        # Guessed the start of the G-region
        if eval_state_predicate(p, set(label)) and eval_state_predicate(q, set(label)):
            transitions[("q0", label)].add("q1")

        # in q1 we only need to ensure q continues to hold
        if eval_state_predicate(q, set(label)):
            # q continues to hold
            transitions[("q1", label)] = {"q1"}
        else:
            # Violation seen
            transitions[("q1", label)] = {"dead"}
        # Once dead, we stay there
        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q1"}, transitions, alphabet)


def _build_F_and_X_buchi(p: Formula,
                         q: Formula,
                         alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi Automaton for the pattern F(p && X q):
    
    States:
        q0 - Waiting for a position where p holds and next state should satisfy q
        q1 - Just saw such a p-position; now check q on the next input label
        q_accept - Success
        dead - Failed after making the guess

    Accepting State:
        q_accept
    """
    states = {"q0", "q1", "q_accept", "dead"}
    transitions = {}

    for label in alphabet:
        # In q0 we can always keep waiting.
        next_states = {"q0"}

        # If p holds now, we may nondeterministically guess this is the position
        # whose next state should satisfy q.
        if eval_state_predicate(p, set(label)):
            next_states.add("q1")

        transitions[("q0", label)] = next_states

        # In q1 we are now reading the next state's label, so q must hold here.
        if eval_state_predicate(q, set(label)):
            # Satisfaction of q
            transitions[("q1", label)] = {"q_accept"}
        else:
            # Violation of q
            transitions[("q1", label)] = {"dead"}
        # If in accpt or dead, we stay there
        transitions[("q_accept", label)] = {"q_accept"}
        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q_accept"}, transitions, alphabet)
        

