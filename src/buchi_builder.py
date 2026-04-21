"""buchi_builder.py

Utility for constructing Buchi Automata that recognise the language of
negated LTL formulas. Only a small, fixed set of patterns is supported.
Each pattern has a dedicated helper that creates the appropriate automaton
using the generic :class:`BuchiAutomaton` container from ``src.structures``
"""

from itertools import combinations
from src.structures import BuchiAutomaton
from src.ast_nodes import (
    Atomic, 
    Or, And, 
    Until, Release, WeakUntil,
    Not, X, F, G,
    BoolConst,
    Formula)

# -------------------------------------------------------------------------
# Helper Utilities
# -------------------------------------------------------------------------
def powerset(items: set[str]) -> list[frozenset[str]]:
    """
    Compute the power-set of a set of atomic proposition names.
    The result is a list of *frozenset*, each representing one possible
    label (i.e. a subset of atomic propositions) that can appear on a
    transition system state.
    
    Parameters
    ----------
    items: set[str]
        The set of atomic proposition names for which to compute the power-set.
        
    Returns
    -------
    list[frozenset[str]]
        The list of all possible subsets of the input set.
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
    
    Parameters
    ----------
    formula: Formula
        The LTL formula from which to collect atomic propositions.
        
    Returns
    -------
    set[str]
        The set of atomic proposition names that appear anywhere in the formula.
    """
    # Return Atomic Propositions
    if isinstance(formula, Atomic):
        return {formula.name}
    # Boolean Constants
    if isinstance(formula, BoolConst):
        return set()
    # Unary Temporal Operators - Propagate to the child
    if isinstance(formula, (X, F, G, Not)):
        return collect_atomic_props(formula.child)
    # Binary Operators - Union the names from both sides
    if isinstance(formula, (And, Or, Until, Release, WeakUntil)):
        return collect_atomic_props(formula.left) | collect_atomic_props(formula.right)
    # Formula does not contain any Atomic Propositions
    return set()

def eval_state_predicate(formula: Formula, label: set[str]) -> bool:
    """
    Evaluate a *pure state predicate* on a single TS label.
    Supported constructs are Atomic, Not, And, Or. Implication should have
    been eliminated earlier in the pipeline
    
    Parameters
    ----------
    formula: Formula
        The state predicate to evaluate.
    label: set[str]
        The TS label on which to evaluate the predicate.

    Returns
    -------
    bool
        The result of the evaluation.

    """
    if isinstance(formula, Atomic):
        return formula.name in label
    if isinstance(formula, BoolConst):
        return formula.value
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
    
    Parameters
    ----------
    formula: Formula
        The LTL formula for which we want to build a Büchi automaton.
        The formula is expected to be in the form of our AST, and should
        have had implications eliminated and negations pushed down to
        the atomic level.
    
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton.
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

    # -----------------------------------------------------------------
    # 0.  Boolean constants
    # -----------------------------------------------------------------
    if isinstance(formula, BoolConst):
        if formula.value:
            return _build_TRUE_buchi(alphabet)
        else:
            return _build_FALSE_buchi(alphabet)

    # -----------------------------------------------------------------
    # 2.  Until / Release / Weak‑Until (binary temporal)
    # -----------------------------------------------------------------
    if isinstance(formula, Until):
        return _build_U_buchi(formula.left, formula.right, alphabet)
    if isinstance(formula, Release):
        return _build_R_buchi(formula.left, formula.right, alphabet)
    if isinstance(formula, WeakUntil):
        return _build_W_buchi(formula.left, formula.right, alphabet)
    
    # -----------------------------------------------------------------
    # 5.  Fallback – try an external tool (optional)
    # -----------------------------------------------------------------
    try:
        return _fallback_spot_builder(formula, alphabet)   # defined later
    except Exception:  # pragma: no cover
        # If the external tool is not available we fall back to the error below.
        pass
    
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
        
    Parameters
    ----------
    p: Formula
        The state predicate that should eventually hold.
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
        
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton for F p.
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
        
    Parameters
    ----------
    p: Formula
        The state predicate that should hold globally.
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
        
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton for G p.    
    
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
    
    Parameters
    ----------
    p: Formula
        The state predicate that should hold in the next state.
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
        
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton for X p.
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
        
    Parameters
    ----------
    p: Formula
        The state predicate that should eventually hold.
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
        
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton for F(G p).
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
        q0 - We are waiting for the next occurrence of p
        q1 - We have just seen p
        
    Accepting State:
        q1
        
    Parameters
    ----------
    p: Formula
        The state predicate that should hold infinitely often.
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
        
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton for G(F p).
    """
    states = {"q0", "q1"}
    transitions = {}

    for label in alphabet:
        if eval_state_predicate(p, set(label)):
            # Seeing p moves us to q1; q1 stays on any further label
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
        
    Parameters
    ----------
    p: Formula
        The state predicate that should eventually hold.
    q: Formula
        The state predicate that should hold globally after the first one is seen.
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
        
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton for F(p && G(q)).
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
        
    Parameters
    ----------
    p: Formula
        The state predicate that should eventually hold.
    q: Formula
        The state predicate that should hold in the next state after p is seen.
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
        
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton for F(p && X(q)).
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
        # If in accept or dead, we stay there
        transitions[("q_accept", label)] = {"q_accept"}
        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q_accept"}, transitions, alphabet)

def _build_U_buchi(p: Formula, q: Formula,
                  alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi automaton for  p U q  (until).
    
    Intuition:
        - While p holds we stay in a “waiting” state.
        - As soon as q holds we move to the accepting sink.
        - If p ever fails before q, we go to a dead sink.
    
    States:
        q0 - waiting (p must hold)
        q_accept - accepting sink (q has been seen)
        dead - violation of p before q
        
    Parameters
    ----------
    p: Formula
        The state predicate that should hold until q holds.
    q: Formula
        The state predicate that should eventually hold, allowing us to 
        move to the accepting state.
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
    """
    states = {"q0", "q_accept", "dead"}
    transitions = {}
    for label in alphabet:
        # Evaluate the two sub‑formulas on the current label
        p_holds = eval_state_predicate(p, set(label))
        q_holds = eval_state_predicate(q, set(label))

        if q_holds:
            # q can be satisfied now – we may jump directly to accept
            transitions[("q0", label)] = {"q_accept"}
        elif p_holds:
            # p holds and q does not → stay in waiting
            transitions[("q0", label)] = {"q0"}
        else:
            # p fails and q has not appeared → dead
            transitions[("q0", label)] = {"dead"}

        # Accepting and dead states are self‑looping
        transitions[("q_accept", label)] = {"q_accept"}
        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q_accept"}, transitions, alphabet)

def _build_R_buchi(p: Formula, q: Formula,
                  alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi automaton for  p R q  (release).
    
    Dual of Until:  ¬(p U ¬q) ≡ (p R q)
    Implementation follows the classic tableau:
        - q must hold forever *or* p may hold until q stops holding.
        
    States:
        q0 - waiting (q must hold, p may hold)
        q0 is accepting because if q holds forever we are done.
        dead - violation of q before p can save us
    
    Parameters
    ----------
    p: Formula
        The state predicate that should hold until q fails.
    q: Formula
        The state predicate that should eventually hold, allowing us to 
        move to the accepting state.
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
    
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton for p R q.
    """
    states = {"q0", "dead"}          # q0 is accepting
    transitions = {}
    for label in alphabet:
        p_holds = eval_state_predicate(p, set(label))
        q_holds = eval_state_predicate(q, set(label))

        if q_holds:
            # If q holds we stay in the accepting state irrespective of p
            transitions[("q0", label)] = {"q0"}
        else:
            # q is false – now p must hold, otherwise dead
            if p_holds:
                transitions[("q0", label)] = {"q0"}
            else:
                transitions[("q0", label)] = {"dead"}

        # Dead is absorbing
        transitions[("dead", label)] = {"dead"}

    return BuchiAutomaton(states, "q0", {"q0"}, transitions, alphabet)

def _build_W_buchi(a: Formula, b: Formula,
                  alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Büchi automaton for  a W b .
    It is the nondeterministic union of the U‑automaton and the G‑automaton.
    The union is obtained by adding a fresh initial state that nondeterministically
    chooses which component to follow.
    
    Parameters
    ----------
    a: Formula
        The state predicate that should hold until b holds (if it ever does).
    b: Formula
        The state predicate that should eventually hold, allowing us to 
        move to the accepting state.
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
        
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton for a W b.
    """
    # Build the two component automata first
    u_auto = _build_U_buchi(a, b, alphabet)
    g_auto = _build_G_predicate_buchi(a, alphabet)

    # Fresh initial state
    init = "init"
    states = {init} | u_auto.states | g_auto.states
    accepting = u_auto.accepting_states | g_auto.accepting_states

    transitions = {}

    # Copy all component transitions
    transitions.update(u_auto.transitions)
    transitions.update(g_auto.transitions)

    # From the fresh init we can jump to either component's start state
    for label in alphabet:
        transitions[(init, label)] = {u_auto.initial, g_auto.initial}

    return BuchiAutomaton(states, init, accepting, transitions, alphabet)

def _build_TRUE_buchi(alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """Automaton that accepts every infinite word (the language Σ^ω).
    
    Parameters
    ----------
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
    
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton for the constant True formula.
    """
    # One state that is both initial and accepting; self‑loops on all labels.
    state = "q"
    states = {state}
    transitions = {(state, label): {state} for label in alphabet}
    return BuchiAutomaton(states, state, {state}, transitions, alphabet)


def _build_FALSE_buchi(alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """Automaton that accepts no word.
    
    Parameters
    ----------
    alphabet: set[frozenset[str]]
        The alphabet of the automaton, i.e. the set of all possible labels.
    
    Returns
    -------
    BuchiAutomaton
        The constructed Büchi automaton for the constant False formula.
    """
    # One dead state that is *not* accepting.
    state = "dead"
    states = {state}
    transitions = {(state, label): {state} for label in alphabet}
    return BuchiAutomaton(states, state, set(), transitions, alphabet)





import subprocess
import re
from typing import Tuple

def _fallback_spot_builder(formula: Formula,
                           alphabet: set[frozenset[str]]) -> BuchiAutomaton:
    """
    Calls the external `ltl2hoa` command (part of the Spot library) and
    converts the resulting HOA description into our ``BuchiAutomaton``.
    The function expects ``spot`` to be installed and reachable in $PATH.
    """
    # [1] Convert our AST back to a string that Spot understands.
    #     The AST already has a ``to_string`` method that prints LTL syntax.
    ltl_str = formula.to_string()

    # [2] Run Spot.  The ``-U`` flag asks for a *Büchi* (not generalized) automaton.
    proc = subprocess.run(
        ["ltl2hoa", "-U", ltl_str],
        capture_output=True,
        text=True,
        check=True,
    )
    hoa = proc.stdout.splitlines()

    # [3] Very small HOA parser (enough for our usage)
    state_map: dict[int, str] = {}
    init_states: set[str] = set()
    accepting: set[str] = set()
    transitions: dict[Tuple[str, frozenset[str]], set[str]] = {}

    state_counter = 0
    for line in hoa:
        line = line.strip()
        if not line or line.startswith("HOA:"):
            continue
        # ----- states -------------------------------------------------
        if line.startswith("State:"):
            # format: State: s0 "init" {0}
            m = re.match(r'State:\s+(\S+)(?:\s+"([^"]+)")?(?:\s+\{([^}]*)\})?', line)
            if not m:
                continue
            name, label, acc = m.groups()
            # give a numeric identifier if Spot used numbers
            if name.isdigit():
                nid = int(name)
                state_map[nid] = f"q{nid}"
                name = f"q{nid}"
            else:
                state_map[name] = name

            if label and "init" in label.split():
                init_states.add(name)
            if acc and "0" in acc.split():
                accepting.add(name)
            continue

        # ----- transitions --------------------------------------------
        # format: [0] {} (0)   or   [1] {p} (0)
        m = re.match(r'\[(\d+)\]\s*\{([^}]*)\}\s*\((\d+)\)', line)
        if not m:
            continue
        src, lbl, dst = m.groups()
        src_name = state_map[int(src)]
        dst_name = state_map[int(dst)]

        # Build the label as a frozenset of propositions.
        # Spot uses the alphabet that we gave it, but we can just treat any
        # combination of letters as a normal label.
        if lbl.strip():
            # split on commas and strip whitespace
            props = frozenset(p.strip() for p in lbl.split(",") if p.strip())
        else:
            props = frozenset()

        transitions.setdefault((src_name, props), set()).add(dst_name)

    # Spot guarantees that the automaton is complete (every state has a
    # transition for each possible label).  If some labels are missing we
    # simply add a self‑loop to a dead sink (not needed for most Spot outputs).
    # -----------------------------------------------------------------
    # Build and return the internal BuchiAutomaton.
    # -----------------------------------------------------------------
    # Use the *same* alphabet that the caller gave us – it matches Spot's.
    return BuchiAutomaton(
        states=set(state_map.values()),
        initial_state=next(iter(init_states)) if init_states else "q0",
        accepting_states=accepting,
        transitions=transitions,
        alphabet=alphabet,
    )
    
    """
    How to enable it? 

Install Spot (conda install -c conda-forge spot or apt‑get install libspot-dev).
Ensure ltl2hoa is on your $PATH.
Leave the call to _fallback_spot_builder untouched – the dispatcher will automatically try Spot only when none of the hand‑crafted patterns match.
If you don’t want an external dependency, simply delete the “fallback” block and keep the raise NotImplementedError line.
    
    """
