import sys

# Import utility functions from the project's source package
from src.model_parser import load_model
from src.ltl_parser import load_formulas
from src.ltl_negation import negate_formula
from src.buchi_builder import build_buchi_for_negated_formula
from src.product_builder import build_product
from src.ndfs import run_ndfs
from src.printer import print_result, print_TS, print_product


def main() -> None:
    """
    Expects exactly two command-line arguments:
    1. Path to amodel file describing the transition system.
    2. Path to a file containing one ore more LTL formulas
    The script checks each formula using the NDFS algorithm 
    and prints the outcome.
    """
    # Validate command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python NDFS_Check.py <model_file> <ltl_file>")
        sys.exit(1)

    # Extract file names from arguments
    model_file = sys.argv[1]
    ltl_file = sys.argv[2]

    # ---------------------------------------------------------------------
    # [1] Load the Transition System (TS) and the list of LTL formulas
    # ---------------------------------------------------------------------
    TS = load_model(model_file)
    formulas = load_formulas(ltl_file)
    
    # Show the loaded TS for debugging / information purposes
    print_TS(TS)

    # ---------------------------------------------------------------------
    # [2] Process each LTL formula independently
    # ---------------------------------------------------------------------
    for idx, formula in enumerate(formulas, start=1):
        print("=" * 70)
        print(f"Formula {idx}: {formula.to_string()}")

        try:
            # -------------------------------------------------------------
            # (a) Negate the formula - Model-Checking verifies that the
            #     system satisfies the original formula by looking for a
            #     counterexample to its negation.
            # -------------------------------------------------------------
            neg = negate_formula(formula)
            
            # -------------------------------------------------------------
            # (b) Build a Buchi Automaton that accepts exactly the traces
            #     satisfying the negated formula.
            # -------------------------------------------------------------
            ba = build_buchi_for_negated_formula(neg)
            
            # -------------------------------------------------------------
            # (c) Compute the product of the system and the Buchi Automaton.
            #     This yields a combined transition system whose accepting
            #     runs correspond to counterexamples.
            # -------------------------------------------------------------
            product = build_product(TS, ba)
            print_product(product)
            
            # -------------------------------------------------------------
            # (d) Run the Nested Depth-First Search algorithm on the product.
            #     It returns True if an accepting cycle (i.e., a counterexample)
            #     is found, otherwise False.
            # -------------------------------------------------------------
            result = run_ndfs(product)

            # -------------------------------------------------------------
            # (e) Print a nicely formatted summary of the whole verification
            #     step, including the original formula, its negation, the
            #     Buchi Automaton, the product, and the NDFS outcome.
            # -------------------------------------------------------------
            print_result(formula, neg, ba, product, result)
            
        # -----------------------------------------------------------------
        # Handle expected "not implemented" placeholders gracefully
        # -----------------------------------------------------------------
        except NotImplementedError as exc:
            print(f"Skipped: {exc}")
        
        # -----------------------------------------------------------------
        # Catch any other unexpected errors so that one faulty formula does
        # not abort the whole script.
        # -----------------------------------------------------------------
        except Exception as exc:
            print(f"Error while processing formula {idx}: {exc}")

# -------------------------------------------------------------------------
# Run the program whenthe file is executed as a script.
# -------------------------------------------------------------------------
if __name__ == "__main__":
    main()
