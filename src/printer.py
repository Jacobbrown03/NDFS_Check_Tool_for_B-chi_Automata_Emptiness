from src.ast_nodes import Formula
from src.structures import BuchiAutomaton, ProductAutomaton, NDFSResult, TransitionSystem

def print_result(
    formula: Formula,
    negated: Formula,
    ba: BuchiAutomaton,
    product: ProductAutomaton,
    result: NDFSResult,
) -> None:
    """
    Print a concise, human-readable summay of a model-checking run.
    
    Parameters
    ----------
    formula : Formula
        The original LTL formula supplied by the user.
    negated : Formula
        The negated version of ``formula`` (in NNF) that was used to build ``ba``.
    ba : BuchiAutomaton
        Buchi Automaton that recognises the language of ``negated``.
    product : ProductAutomaton
        Synchronous product of the Transition System and ``ba``.
    result : NDFSResult
        Outcome of the NDFS emptiness check on ``product``
    """
    # ---------------------------------------------------------------------
    # [1] General Statistics
    # ---------------------------------------------------------------------
    print(f"Original LTL          : {formula.to_string()}")
    print(f"Negated LTL           : {negated.to_string()}")
    print(f"Büchi states          : {len(ba.states)}")
    print(f"Product states        : {len(product.states)}")
    print(f"Accepting product states: {len(product.accepting_states)}")
    
    # ---------------------------------------------------------------------
    # [2] Emptiness Information
    # ---------------------------------------------------------------------
    emptiness = not result.accepting_cycle_found
    print(
        "Emptiness of product automaton :",
        "EMPTY" if emptiness else "NON-EMPTY"
    )

    # ---------------------------------------------------------------------
    # [3] Truth value of the original formula
    # ---------------------------------------------------------------------
    if emptiness:
        # No accepting SCC -> the negated formula has no model -> original holds
        print("Original formula :", "HOLDS")
    else:
        # An accepting SCC provides a counter-example -> original does not hold
        print("Original formula :", "DOES NOT HOLD")


    # ---------------------------------------------------------------------
    # [4] Counter-example (witness) when the product is non-empty
    # ---------------------------------------------------------------------
    if not emptiness:
        if result.witness_prefix:
            print("Prefix:")
            print("  " + " -> ".join(str(x) for x in result.witness_prefix))
        if result.witness_cycle:
            print("Cycle:")
            print("  " + " -> ".join(str(x) for x in result.witness_cycle))
    print()
    
    
def print_TS(ts: TransitionSystem) -> None:
    """Print the Transition System in a readable, section-wise format."""
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
    """
    Print a Buchi Automaton:
        states, initial/accepting states, alphabet, transitions.
    """
    print("# Buchi Automaton")
    print("States:"," ".join(sorted(ba.states)))
    print("Initial State:", ba.initial_state)
    print("Accepting States:"," ".join(sorted(ba.accepting_states)))
    
    # Render the alphabet as a set of propositions for each symbol.
    alphabet_str = " ".join(
        "{" + ", ".join(sorted(val)) + "}" if val else "{}"
        for val in sorted(ba.alphabet)
    )
    print("Alphabet:", alphabet_str)
    print("Transitions")
    for (src, lab), dsts in ba.transitions.items():
        lab_str = "{" + ", ".join(sorted(lab)) + "}" if lab else "{}"
        dst_str = " ".join(sorted(dsts))
        print(f"    ({src}, {lab_str}) -> {{ {dst_str} }}")
    print()
    
    
def print_product(product: ProductAutomaton) -> None:
    """Print a product automaton in a compact adjacency-list representation."""
    print("# Product Automaton")
    print("States:", " ".join(sorted(product.states)))
    print("Initial states:", " ".join(sorted(product.initial_states)))
    print("Accepting states:", " ".join(sorted(product.accepting_states)))

    print("Transitions:")
    for src, dsts in product.transitions.items():
        dst_str = " ".join(sorted(dsts))
        print(f"  {src} -> {dst_str}")
    print()
