"""structures.py

Data‑type definitions that model the core objects used by the verification
pipeline.

* TransitionSystem – a labelled Kripke structure (the model).
* BuchiAutomaton   – a nondeterministic Büchi automaton that recognises the
                     language of a (negated) LTL formula.
* ProductAutomaton – the synchronous product of a TransitionSystem and a
                     BuchiAutomaton.
* NDFSResult       – the outcome of the Nested‑DFS emptiness check on a
                     product automaton, including a concrete counter‑example
                     when one exists.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional

# ----------------------------------------------------------------------
# Basic type aliases
# ----------------------------------------------------------------------
# A label seen by the Büchi automaton is a *frozenset* of proposition names.
LabelSet = frozenset[str]

# A product state is a pair (ts_state, ba_state).
ProductState = Tuple[str, str]

# ----------------------------------------------------------------------
# Transition system (Kripke structure)
# ----------------------------------------------------------------------
@dataclass
class TransitionSystem:
    """A finite‑state transition system with atomic‑proposition labelling."""
    states: Set[str]                     # all state identifiers
    transitions: Dict[str, Set[str]]     # adjacency list: src → {dst_1, …}
    initial_state: str                   # start state for model checking
    labels: Dict[str, Set[str]]          # state → set of atomic propositions true there
    accepting_states: Set[str]           # states that are considered “final” (used for
                                         # Büchi acceptance when intersected)

    def successors(self, state: str) -> Set[str]:
        """Return the set of direct successors of *state* (empty set if none)."""
        return self.transitions.get(state, set())

    def label_of(self, state: str) -> Set[str]:
        """Return the atomic‑proposition set that holds in *state*."""
        return self.labels.get(state, set())

# ----------------------------------------------------------------------
# Büchi automaton (used for the negated LTL formula)
# ----------------------------------------------------------------------
@dataclass
class BuchiAutomaton:
    """Nondeterministic Büchi automaton over a finite alphabet of
    proposition subsets."""
    states: Set[str]                                          # automaton states
    initial_state: str                                        # unique start state
    accepting_states: Set[str]                                 # set of accepting states
    transitions: Dict[Tuple[str, LabelSet], Set[str]]          # (src, label) → {dst,…}
    alphabet: Set[LabelSet] = field(default_factory=set)      # all possible labels

    def next_states(self, state: str, label: Set[str]) -> Set[str]:
        """
        Given *state* and a concrete *label* (set of propositions), return
        the set of reachable states according to the transition relation.
        The label is converted to a frozenset to match the dictionary key.
        """
        key = (state, frozenset(label))
        return self.transitions.get(key, set())

# ----------------------------------------------------------------------
# Product automaton (TS × BA)
# ----------------------------------------------------------------------
@dataclass
class ProductAutomaton:
    """Synchronous product of a TransitionSystem and a BuchiAutomaton.
    Each product state couples a concrete TS state with a Büchi state."""
    states: Set[ProductState]                              # reachable pairs (ts, ba)
    initial_states: Set[ProductState]                      # possibly multiple because the BA may
                                                            # have several successors on the initial label
    accepting_states: Set[ProductState]                    # product states whose BA component is accepting
    transitions: Dict[ProductState, Set[ProductState]]     # adjacency list in the product

    def successors(self, state: ProductState) -> Set[ProductState]:
        """Return the set of successors of *state* in the product graph."""
        return self.transitions.get(state, set())

# ----------------------------------------------------------------------
# Result container for the Nested‑DFS algorithm
# ----------------------------------------------------------------------
@dataclass
class NDFSResult:
    """Outcome of the NDFS emptiness check.

    Attributes
    ----------
    accepting_cycle_found : bool
        ``True`` if an accepting strongly‑connected component (hence a
        counter‑example) was discovered.
    witness_prefix : List[ProductState]
        The prefix from an initial product state up to the first state of the
        accepting cycle.
    witness_cycle : List[ProductState]
        The cycle itself (states visited repeatedly).  The first state of the
        cycle is *not* duplicated at the end.
    visited_blue : Set[ProductState]
        All states visited during the outer (blue) DFS.
    visited_red : Set[ProductState]
        All states visited during the inner (red) DFS; kept empty globally
        because each red search uses its own local set.
    """
    accepting_cycle_found: bool
    witness_prefix: List[ProductState] = field(default_factory=list)
    witness_cycle: List[ProductState] = field(default_factory=list)
    visited_blue: Set[ProductState] = field(default_factory=set)
    visited_red: Set[ProductState] = field(default_factory=set)
