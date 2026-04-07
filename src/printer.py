# Pretty output:
# formula name
# parsed formula
# negated formula
# product size
# emptiness result
# optional accepting cycles

from src.structures import BuchiAutomaton, ProductAutomaton, NDFSResult
from src.ast_nodes import Formula


def print_result(
    formula: Formula,
    negated: Formula,
    ba: BuchiAutomaton,
    product: ProductAutomaton,
    result: NDFSResult,
) -> None:
    print(f"Original: {formula.to_string()}")
    print(f"Negated : {negated.to_string()}")
    print(f"Buchi states: {len(ba.states)}")
    print(f"Product states: {len(product.states)}")
    print(f"Accepting product states: {len(product.accepting_states)}")

    if result.accepting_cycle_found:
        print("Result: FAILS")
        if result.witness_prefix:
            print("Prefix:")
            print("  " + " -> ".join(str(x) for x in result.witness_prefix))
        if result.witness_cycle:
            print("Cycle:")
            print("  " + " -> ".join(str(x) for x in result.witness_cycle))
    else:
        print("Result: HOLDS")

