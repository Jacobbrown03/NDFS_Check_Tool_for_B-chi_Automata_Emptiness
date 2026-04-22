import sys

# Import utility functions from the project's source package
from src.model_parser import load_model
from src.ltl_parser import load_formulas
from src.ltl_negation import negate_formula
from src.buchi_builder import build_buchi_for_negated_formula
from src.product_builder import build_product
from src.ndfs import run_ndfs
from src.printer import print_result, print_TS, print_product

def load_expected(path: str) -> dict[str, str]:
    """
    Load expected results file of format:
    f_1: EMPTY
    f_2: NON-EMPTY
    """
    expected = {}

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            label, value = line.split(":", 1)
            expected[label.strip()] = value.strip()

    return expected

def main() -> None:
    """
    Expects exactly two command-line arguments:
    1. Path to a model file describing the transition system.
    2. Path to a file containing one or more LTL formulas
    3. (Optional) Print flag to print each formula's details during processing.
    The script checks each formula using the NDFS algorithm 
    and prints the outcome.
    """
    # Validate command-line arguments
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python NDFS_Check.py <model_file> <ltl_file> [print_flag]")
        sys.exit(1)

    # Extract file names
    model_file = sys.argv[1]
    ltl_file = sys.argv[2]

    # Optional print flag
    print_flag = len(sys.argv) > 3 and sys.argv[3].lower() == "print"

    # ---------------------------------------------------------------------
    # [1] Load the Transition System (TS) and the list of LTL formulas
    # ---------------------------------------------------------------------
    ts = load_model(model_file)
    formulas = load_formulas(ltl_file)
    
    # ---------------------------------------------------------------------
    # [2] Load expected results for each formula
    # ---------------------------------------------------------------------
    expected = load_expected("specs/Traffic_Light_Expected.txt")
    results_summary = []
    correct_count = 0
    total = 0
    
    # Show the loaded TS for debugging / information purposes
    if print_flag:
        print_TS(ts)

    # ---------------------------------------------------------------------
    # [3] Process each LTL formula independently
    # ---------------------------------------------------------------------
    for idx, (label, formula) in enumerate(formulas, start=1):
        if print_flag:
            print("=" * 70)
            print(f"{label or f'f_{idx}'}: {formula.to_string()}")

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
            product = build_product(ts, ba)
            #print_product(product)
            
            # -------------------------------------------------------------
            # (d) Run the Nested Depth-First Search algorithm on the product.
            #     It returns True if an accepting cycle (i.e., a counterexample)
            #     is found, otherwise False.
            # -------------------------------------------------------------
            result = run_ndfs(product)
            
            
            # -------------------------------------------------------------
            # (e) Compare actual and expected results and add to counters.
            # -------------------------------------------------------------
            actual = "NON-EMPTY" if result.accepting_cycle_found else "EMPTY"
            expected_value = expected.get(label, "UNKNOWN")
            
            is_correct = (actual == expected_value)
            if is_correct:
                correct_count += 1
            total += 1
            
            results_summary.append((label, formula.to_string(), actual, expected_value, is_correct))

            # -------------------------------------------------------------
            # (f) Print a nicely formatted summary of the whole verification
            #     step, including the original formula, its negation, the
            #     Buchi Automaton, the product, and the NDFS outcome.
            # -------------------------------------------------------------
            if print_flag:
                print_result(formula, neg, ba, product, result)
                print()
            
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
            print(f"Error while processing formula {idx} ({formula.to_string()}): {exc}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"{'Label':<6} | {'Formula':<40} | {'Result':<10} | {'Expected':<10} | {'OK'}")
    print("-" * 80)

    for label, formula_str, actual, expected_value, ok in results_summary:
        status = "✔" if ok else "✘"
        print(f"{label:<6} | {formula_str:<40} | {actual:<10} | {expected_value:<10} | {status}")

    print("-" * 80)
    print(f"{correct_count}/{total} correct")
# -------------------------------------------------------------------------
# Run the program whenthe file is executed as a script.
# -------------------------------------------------------------------------
if __name__ == "__main__":
    main()
