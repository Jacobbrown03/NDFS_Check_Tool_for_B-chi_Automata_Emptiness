# ----------------------------------------------------------------------
# product_builder.py
# ----------------------------------------------------------------------
"""
Construction of the synchronous product TS x BA.

A *product* state is a pair (ts_state, ba_state). The product automaton
represents the behavior of the transition system while tracking the
progress of the Buchi Automaton that recognises the negated LTL formula.
Only reachable product states are generated.
"""

from collections import deque
from typing import Dict, Set, Tuple, FrozenSet

from src.structures import TransitionSystem, BuchiAutomaton, ProductAutomaton, ProductState

# -------------------------------------------------------------------------
# Helper Functions - label handling
# -------------------------------------------------------------------------
def _ap_set_from_alphabet(alphabet: Set[FrozenSet[str]]) -> Set[str]:
    """
    Return the set of *all* atomic propositions that appear in any
    valuation of the Buchi alphabet.
    
    Parameters
    ----------
    alphabet:
        The set of labels (each a frozenset of proposition names) that the
        Buchi automaton can read.
        
    Returns
    -------
    set[str]:
        Union of all proposition names occurring in the alphabet.    
    """
    return {ap for valuation in alphabet for ap in valuation}


def label_for_ba(ts_label: Set[str], ba: BuchiAutomaton) -> FrozenSet[str]:
    """
    Project a transition-system label onto the subset of propositions
    that the Buchi automaton is aware of.
    
    The TS may contain propositions irrelevant to the BA; they are simply
    filtered out.
    
    Parameters
    ----------
    ts_label:
        Set of atomic propositions that hold in a TS state.
    ba:
        The Buchi Automaton whose alphabet defines the relevant propositions.
        
    Returns
    -------
    frozenset[str]:
        The filtered label that can be used with ``ba.next_states``.
    """
    ap_set = _ap_set_from_alphabet(ba.alphabet)
    return frozenset(p for p in ts_label if p in ap_set)

# -------------------------------------------------------------------------
# Core Product Construction
# -------------------------------------------------------------------------
def build_product(ts: TransitionSystem, ba: BuchiAutomaton) -> ProductAutomaton:
    """
    Bread-first construction of the reachable part of the product
    automaton TS x BA.
    
    The product state is a tuple (ts_state, ba_state). A product state is
    *accepting* iff its BA components belongs to ``ba.accepting_states``.
    
    Parameters
    ----------
    ts:
        Transition system representing the model.
    ba:
        Buchi Automaton that recognises the language of the *negated*
        LTL formula.
    
    Returns
    -------
    ProductAutomaton
        A fully initialised product automaton containing only the states
        reachable from the initial product configuration.
    """
    # ---------------------------------------------------------------------
    # [1] Initial product states
    # ---------------------------------------------------------------------
    # Project the label of the TS initial state onto the BA alphabet
    init_label = label_for_ba(ts.label_of(ts.initial_state), ba)
    
    # From the BA initial state, follow all transitions that match this label.
    init_ba_states = ba.next_states(ba.initial_state, init_label)

    # If the BA cannot move on the initial label, the product is empty.
    if not init_ba_states:
        return ProductAutomaton(set(), set(), set(), {})

    # Each reachable BA state yields a distinct product state.
    init_prod: Set[ProductState] = {
        (ts.initial_state, q) for q in init_ba_states
    }

    # ---------------------------------------------------------------------
    # [2] Breadth-first search over the product
    # ---------------------------------------------------------------------
    visited: Set[ProductState] = set(init_prod)
    accepting: Set[ProductState] = set()
    trans: Dict[ProductState, Set[ProductState]] = {}
    worklist: deque[ProductState] = deque(init_prod)

    while worklist:
        cur_ts, cur_ba = worklist.popleft()
        cur_prod = (cur_ts, cur_ba)

        # Record acceptance as soon as we pop the state.
        if cur_ba in ba.accepting_states:
            accepting.add(cur_prod)

        # Collect successors of the current product state.
        succs: Set[ProductState] = set()
        
        for ts_nxt in ts.successors(cur_ts):
            # Project the *destination* TS label.
            proj_label = label_for_ba(ts.label_of(ts_nxt), ba)

            # ...and ask the BA which of its states can be reached on that label.
            for ba_nxt in ba.next_states(cur_ba, proj_label):
                prod_nxt = (ts_nxt, ba_nxt)
                succs.add(prod_nxt)

                # If this product state has never been seen, enqueu it.
                if prod_nxt not in visited:
                    visited.add(prod_nxt)
                    worklist.append(prod_nxt)
        # Store the outgoing edges of ``cur_prod``.
        trans[cur_prod] = succs

    # ---------------------------------------------------------------------
    # [3] Return the fully build product automaton
    # ---------------------------------------------------------------------
    return ProductAutomaton(
        states=visited,
        initial_states=init_prod,
        accepting_states=accepting,
        transitions=trans,
    )
