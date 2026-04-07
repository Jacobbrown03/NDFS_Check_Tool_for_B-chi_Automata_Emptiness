from src.ast_nodes import Formula
from src.structures import BuchiAutomaton, ProductAutomaton, NDFSResult, TransitionSystem
#from typing import List

def print_result(
    formula: Formula,
    negated: Formula,
    ba: BuchiAutomaton,
    product: ProductAutomaton,
    result: NDFSResult,
) -> None:
    """
    Print a summary of the model‑checking run.

    * ``result.accepting_cycle_found`` tells us whether the product
      automaton contains an accepting SCC.  In the NDFS algorithm this
      means the language of the Büchi automaton (built from the **negated**
      LTL formula) is **non‑empty**.
    * If the language is non‑empty, the original formula does **not**
      hold on the transition system; otherwise it **holds**.

    The output therefore reports:
        – emptiness of the product (EMPTY / NON‑EMPTY)
        – the truth value of the original formula
    """
    # -----------------------------------------------------------------
    # 3️⃣  Additional information (kept from the original printer)
    # -----------------------------------------------------------------
    print(f"Original LTL          : {formula.to_string()}")
    print(f"Negated LTL           : {negated.to_string()}")
    print(f"Büchi states          : {len(ba.states)}")
    print(f"Product states        : {len(product.states)}")
    print(f"Accepting product states: {len(product.accepting_states)}")
    
    
    # -----------------------------------------------------------------
    # 1️⃣  Emptiness information
    # -----------------------------------------------------------------
    emptiness = not result.accepting_cycle_found
    print("Emptiness of product automaton :", "EMPTY" if emptiness else "NON‑EMPTY")

    # -----------------------------------------------------------------
    # 2️⃣  Original‑formula truth value
    # -----------------------------------------------------------------
    if emptiness:
        # The product is empty ⇒ the negated formula has no model
        # ⇒ the original formula is true on the TS.
        print("Original formula :", "HOLDS")
    else:
        # Non‑empty product ⇒ there is a counter‑example
        print("Original formula :", "DOES NOT HOLD")


    # -----------------------------------------------------------------
    # 4️⃣  Counter‑example (if one exists)
    # -----------------------------------------------------------------
    if not emptiness:
        # there is an accepting SCC → we have a witness
        if result.witness_prefix:
            print("Prefix:")
            print("  " + " -> ".join(str(x) for x in result.witness_prefix))
        if result.witness_cycle:
            print("Cycle:")
            print("  " + " -> ".join(str(x) for x in result.witness_cycle))
    print()
    
    
def print_TS(ts: TransitionSystem) -> None:
    print("# Adjacency List")
    for state in sorted(ts.states):
        print(f"{state} -> ", end="")
        print(*sorted(ts.transitions[state]))
        
    print("\n# Accepting State\naccept:", end=" ")
    print(*ts.accepting_states)
    print("\n# Initial State\ninit:", end=" ")
    print(ts.initial_state)
    print("\n# Proposition Labelling")
    for state in sorted(ts.states):
        print(state, end=": ")
        print(*sorted(ts.labels[state]))

    
def print_buchi(ba: BuchiAutomaton) -> None:
    print("# Buchi Automaton")
    print("States:"," ".join(sorted(ba.states)))
    print("Initial State:", ba.initial_state)
    print("Accepting States:"," ".join(sorted(ba.accepting_states)))
    alphabet_str = " ".join(
        "{" + ", ".join(sorted(val)) + "}" if val else "{}" for val in sorted(ba.alphabet)
    )
    print("Alphabet:", alphabet_str)
    print("Transitions")
    for (src, lab), dsts in ba.transitions.items():
        lab_str = "{" + ", ".join(sorted(lab)) + "}" if lab else "{}"
        dst_str = " ".join(sorted(dsts))
        print(f"    ({src}, {lab_str}) -> {{ {dst_str} }}")
    print()
    
    
def print_product(product: ProductAutomaton) -> None:
    print("# Product Automaton")
    print("States:", " ".join(sorted(product.states)))
    print("Initial states:", " ".join(sorted(product.initial_states)))
    print("Accepting states:", " ".join(sorted(product.accepting_states)))

    print("Transitions:")
    for src, dsts in product.transitions.items():
        dst_str = " ".join(sorted(dsts))
        print(f"  {src} -> {dst_str}")
    print()
