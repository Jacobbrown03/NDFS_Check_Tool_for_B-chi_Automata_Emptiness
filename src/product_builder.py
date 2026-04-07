# ----------------------------------------------------------------------
# product_builder.py
# ----------------------------------------------------------------------
"""
Construction of the synchronous product TS × BA.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, Set, Tuple, FrozenSet

from src.structures import TransitionSystem, BuchiAutomaton, ProductAutomaton, ProductState


def _ap_set_from_alphabet(alphabet: Set[FrozenSet[str]]) -> Set[str]:
    """Return the set of atomic propositions that appear in any valuation."""
    return {ap for valuation in alphabet for ap in valuation}


def label_for_ba(ts_label: Set[str], ba: BuchiAutomaton) -> FrozenSet[str]:
    """
    Project a TS label onto the atomic‑proposition set that the
    Büchi automaton knows about.
    """
    ap_set = _ap_set_from_alphabet(ba.alphabet)
    return frozenset(p for p in ts_label if p in ap_set)


def debug_initial_ba(ts: TransitionSystem, ba: BuchiAutomaton) -> Set[str]:
    """Small debugging routine – prints the first product step."""
    raw_label = ts.label_of(ts.initial_state)
    proj_label = label_for_ba(raw_label, ba)

    print("\n=== DEBUG: initial BA step ===")
    print(f"TS initial state      : {ts.initial_state}")
    print(f"Raw TS label          : {raw_label}")
    print(f"Projected label       : {proj_label}")

    init = ba.initial_state
    print(f"BA initial state      : {init}")

    outgoing = [
        (dst, lbl) for (src, lbl), dsts in ba.transitions.items()
        if src == init for dst in dsts
    ]
    if not outgoing:
        print("⚠️  No outgoing edges – check the BA builder!")
    else:
        print("Outgoing edges (src, label) → dst:")
        for dst, lbl in outgoing:
            print(f"   ({init}, {set(lbl)}) → {dst}")

    result = ba.next_states(init, proj_label)
    print(f"Result of next_states : {result}")
    print("=== END DEBUG ===\n")
    return result


def build_product(ts: TransitionSystem, ba: BuchiAutomaton) -> ProductAutomaton:
    """
    Bread‑first construction of the reachable part of the product.
    The product state is a tuple (ts_state, ba_state).  A product state is
    accepting iff its BA component is accepting.
    """
    # ---------- 1️⃣  Initial product states ----------
    init_label = label_for_ba(ts.label_of(ts.initial_state), ba)
    init_ba_states = ba.next_states(ba.initial_state, init_label)

    if not init_ba_states:
        # No transition on the initial TS label → empty product.
        return ProductAutomaton(set(), set(), set(), {})

    init_prod: Set[ProductState] = {
        (ts.initial_state, q) for q in init_ba_states
    }

    # ---------- 2️⃣  BFS over the product ----------
    visited: Set[ProductState] = set(init_prod)
    accepting: Set[ProductState] = set()
    trans: Dict[ProductState, Set[ProductState]] = {}
    worklist: deque[ProductState] = deque(init_prod)

    while worklist:
        cur_ts, cur_ba = worklist.popleft()
        cur_prod = (cur_ts, cur_ba)

        if cur_ba in ba.accepting_states:
            accepting.add(cur_prod)

        succs: Set[ProductState] = set()
        for ts_nxt in ts.successors(cur_ts):
            # Project the label of the *destination* TS state.
            proj_label = label_for_ba(ts.label_of(ts_nxt), ba)

            for ba_nxt in ba.next_states(cur_ba, proj_label):
                prod_nxt = (ts_nxt, ba_nxt)
                succs.add(prod_nxt)

                if prod_nxt not in visited:
                    visited.add(prod_nxt)
                    worklist.append(prod_nxt)

        trans[cur_prod] = succs

    # ---------- 3️⃣  Return the product automaton ----------
    return ProductAutomaton(
        states=visited,
        initial_states=init_prod,
        accepting_states=accepting,
        transitions=trans,
    )
