import sys
from src.model_parser import load_model
from src.ltl_parser import load_formulas
from src.ltl_negation import negate_formula
from src.buchi_builder import build_buchi_for_negated_formula
from src.product_builder import build_product
from src.ndfs import run_ndfs
from src.printer import print_result, print_TS

def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python NDFS_Check.py <model_file> <ltl_file>")
        sys.exit(1)

    model_file = sys.argv[1]
    ltl_file = sys.argv[2]

    ts = load_model(model_file)
    formulas = load_formulas(ltl_file)
    
    print_TS(ts)

    for idx, formula in enumerate(formulas, start=1):
        print("=" * 70)
        print(f"Formula {idx}: {formula.to_string()}")

        try:
            neg = negate_formula(formula)
            ba = build_buchi_for_negated_formula(neg)
            product = build_product(ts, ba)
            result = run_ndfs(product)

            print_result(formula, neg, ba, product, result)
        except NotImplementedError as exc:
            print(f"Skipped: {exc}")
        except Exception as exc:
            print(f"Error while processing formula {idx}: {exc}")


if __name__ == "__main__":
    main()
