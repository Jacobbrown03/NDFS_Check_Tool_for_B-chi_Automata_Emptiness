# Handles:
# Implication elimination
# Pushing negation inward
# Simplification

from src.ast_nodes import Atomic, Not, And, Or, Implies, X, F, G, Formula


def eliminate_implication(formula: Formula) -> Formula:
    if isinstance(formula, Atomic):
        return formula
    if isinstance(formula, Not):
        return Not(eliminate_implication(formula.child))
    if isinstance(formula, And):
        return And(eliminate_implication(formula.left), eliminate_implication(formula.right))
    if isinstance(formula, Or):
        return Or(eliminate_implication(formula.left), eliminate_implication(formula.right))
    if isinstance(formula, Implies):
        return Or(Not(eliminate_implication(formula.left)), eliminate_implication(formula.right))
    if isinstance(formula, X):
        return X(eliminate_implication(formula.child))
    if isinstance(formula, F):
        return F(eliminate_implication(formula.child))
    if isinstance(formula, G):
        return G(eliminate_implication(formula.child))
    raise NotImplementedError(f"Unsupported formula type: {type(formula)}")


def push_negation(formula: Formula) -> Formula:
    if isinstance(formula, Atomic):
        return formula

    if isinstance(formula, Not):
        child = formula.child

        if isinstance(child, Atomic):
            return formula
        if isinstance(child, Not):
            return push_negation(child.child)
        if isinstance(child, And):
            return Or(push_negation(Not(child.left)), push_negation(Not(child.right)))
        if isinstance(child, Or):
            return And(push_negation(Not(child.left)), push_negation(Not(child.right)))
        if isinstance(child, X):
            return X(push_negation(Not(child.child)))
        if isinstance(child, F):
            return G(push_negation(Not(child.child)))
        if isinstance(child, G):
            return F(push_negation(Not(child.child)))
        raise NotImplementedError(f"Unsupported negation child: {type(child)}")

    if isinstance(formula, And):
        return And(push_negation(formula.left), push_negation(formula.right))
    if isinstance(formula, Or):
        return Or(push_negation(formula.left), push_negation(formula.right))
    if isinstance(formula, X):
        return X(push_negation(formula.child))
    if isinstance(formula, F):
        return F(push_negation(formula.child))
    if isinstance(formula, G):
        return G(push_negation(formula.child))

    raise NotImplementedError(f"Unsupported formula type: {type(formula)}")


def negate_formula(formula: Formula) -> Formula:
    no_imp = eliminate_implication(formula)
    return push_negation(Not(no_imp))

