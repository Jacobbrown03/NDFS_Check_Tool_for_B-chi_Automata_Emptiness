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
    Print a concise, human-readable summary of a model-checking run.
    
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
    print("-" * 50)
    print(f"Original LTL          : {formula.to_string()}")
    print(f"Negated LTL           : {negated.to_string()}")
    print(f"Buchi states          : {len(ba.states)}")
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
    print("Result:", "HOLDS (no counterexample)" if emptiness else "FAILS (counterexample found)")


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
    """Print the Transition System in a readable, section-wise format.
    
    Parameters
    ----------
    ts: TransitionSystem
        The transition system to be printed.
    """
    print("# Adjacency List")
    for state in sorted(ts.states):
        print(f"{state} -> ", end="")
        print(*sorted(ts.transitions[state]))
        
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
        
    Parameters
    ----------
    ba: BuchiAutomaton
        The Büchi automaton to be printed.
    """
    print("# Buchi Automaton")
    print("States:"," ".join(sorted(ba.states)))
    print("Initial State:", ba.initial_state)
    print("Accepting States:"," ".join(sorted(ba.accepting_states)))
    
    # Render the alphabet as a set of propositions for each symbol.
    alphabet_str = " ".join(
        "{" + ", ".join(sorted(val)) + "}" if val else "{}"
        for val in sorted(ba.alphabet, key=lambda x: sorted(x))
    )
    print("Alphabet:", alphabet_str)
    print("Transitions")
    for (src, lab) in sorted(ba.transitions):
        dsts = ba.transitions[(src, lab)]
        lab_str = "{" + ", ".join(sorted(lab)) + "}" if lab else "{}"
        dst_str = " ".join(sorted(dsts))
        print(f"    ({src}, {lab_str}) -> {{ {dst_str} }}")
    print()
    
    
def print_product(product: ProductAutomaton) -> None:
    """Print a product automaton in a compact adjacency-list representation.
    
    Parameters
    ----------
    product: ProductAutomaton
        The product automaton to be printed.
    """
    print("# Product Automaton")
    print("States:")
    for state in sorted(product.states):
        print(f"\t{state}")
    print("Initial states:")
    for state in sorted(product.initial_states):
        print(f"\t{state}")
    print("Accepting states:")
    for state in sorted(product.accepting_states):
        print(f"\t{state}")

    print("Transitions:")
    for src in sorted(product.transitions):
        dsts = product.transitions[src]
        print(f"  {src} -> ")
        for state in sorted(dsts):
            print(f"\t{state}", end=" ")
        print()
    print()
