"""ltl_negation.py

Utility functions that transform an LTL formula into its negation in
Negation Normal Form (NNF).
"""

from src.ast_nodes import (
    Atomic, 
    Implies, 
    Or, And, 
    Until, Release, WeakUntil,
    Not, X, F, G,
    BoolConst,
    Formula)

def eliminate_implication(formula: Formula) -> Formula:
    """
    Recursively replace every implication in formula.
    
    Parameters
    ----------
    formula: Formula
        The LTL formula to transform
        
    Returns
    -------
    Formula
        An equivalent formula without (->).
    """
    # Base Cases - Atomic Propositions and Boolean constants are unchanged
    if isinstance(formula, Atomic):
        return formula
    
    if isinstance(formula, BoolConst):
        return formula
    
    # Negation propagates unchanged; only its child is processed
    if isinstance(formula, Not):
        return Not(eliminate_implication(formula.child))
    
    # Binary Boolean Connectives - Recurse on both operands.
    if isinstance(formula, And):
        return And(
            eliminate_implication(formula.left),
            eliminate_implication(formula.right),
        )
    if isinstance(formula, Or):
        return Or(
            eliminate_implication(formula.left),
            eliminate_implication(formula.right),
        )
    
    # Implication Case - Replace with '!left || right'.
    if isinstance(formula, Implies):
        return Or(
            Not(eliminate_implication(formula.left)),
            eliminate_implication(formula.right),
        )
        
    # Temporal Operators - Recurse on their single child.
    if isinstance(formula, X):
        return X(eliminate_implication(formula.child))
    if isinstance(formula, F):
        return F(eliminate_implication(formula.child))
    if isinstance(formula, G):
        return G(eliminate_implication(formula.child))
    
    # Binary Temporal Operators - recurse on both sides
    if isinstance(formula, Until):
        return Until(
            eliminate_implication(formula.left),
            eliminate_implication(formula.right),
        )
    if isinstance(formula, Release):
        return Release(
            eliminate_implication(formula.left),
            eliminate_implication(formula.right),
        )
    if isinstance(formula, WeakUntil):
        return WeakUntil(
            eliminate_implication(formula.left),
            eliminate_implication(formula.right),
        )
    
    # Anything else is not part of the supported AST.
    raise NotImplementedError(f"Unsupported formula type: {type(formula)}")

def push_negation(formula: Formula) -> Formula:
    """
    Push a leading negation inward until it only appears in front of
    atomic propositions. This yields NNF.
    
    Parameters
    ----------
    formula : Formula
        A formula possibly containing a top-level Not node.
        
    Returns
    -------
    Formula
        An equivalent formula in NNF.
    """
    # Atomic Propositions and Boolean constants are already in NNF.
    if isinstance(formula, Atomic):
        return formula
    if isinstance(formula, BoolConst):
        return formula

    # When we encounter a negation we apply the appropriate De Morgan
    # or temporal duality rule.
    if isinstance(formula, Not):
        child = formula.child

        # Negation of an Atomic Proposition stays as Not(Atomic)
        if isinstance(child, Atomic):
            return formula
        
        if isinstance(child, BoolConst):
            return BoolConst(not child.value)
        
        # Double negation cancels out
        if isinstance(child, Not):
            return push_negation(child.child)
        
        # De Morgan for conjunction/disjunction
        if isinstance(child, And):
            # !(q && p) -> !q || !p
            return Or(
                push_negation(Not(child.left)),
                push_negation(Not(child.right)),
            )
        if isinstance(child, Or):
            # !(q || p) -> !q && !p
            return And(
                push_negation(Not(child.left)),
                push_negation(Not(child.right)),
            )
        
        # Temporal Dualities.
        if isinstance(child, X):
            # !X q -> X !q
            return X(push_negation(Not(child.child)))
        if isinstance(child, F):
            # !F q -> G !q
            return G(push_negation(Not(child.child)))
        if isinstance(child, G):
            # !G q -> F !q
            return F(push_negation(Not(child.child)))
        
        # Binary Temporal Operators
        if isinstance(child, Until):
            # !(a U b) -> (!a) R (!b)
            return Release(
                push_negation(Not(child.left)),
                push_negation(Not(child.right)),
            )
        if isinstance(child, Release):
            # !(a R b) -> (!a) U (!b)
            return Until(
                push_negation(Not(child.left)),
                push_negation(Not(child.right)),
            )
        if isinstance(child, WeakUntil):
            # Weak-until is defined as (a U b) || G a.
            # ! (a W b) -> !(a U b) && !G a
            #           -> (!a) R (!b) && F (!a)
            return And(
                Release(
                    push_negation(Not(child.left)),
                    push_negation(Not(child.right)),
                ),
                F(push_negation(Not(child.left))),
            )
        
        # Any other construct under a negation is unsupported.
        raise NotImplementedError(f"Unsupported negation child: {type(child)}")

    # For the remaining (non-negated) cases we simply recurse.
    if isinstance(formula, And):
        return And(
            push_negation(formula.left),
            push_negation(formula.right),
        )
    if isinstance(formula, Or):
        return Or(
            push_negation(formula.left),
            push_negation(formula.right),
        )
    if isinstance(formula, X):
        return X(push_negation(formula.child))
    if isinstance(formula, F):
        return F(push_negation(formula.child))
    if isinstance(formula, G):
        return G(push_negation(formula.child))

    # Binary Temporal Operators
    if isinstance(formula, Until):
        return Until(
            push_negation(formula.left),
            push_negation(formula.right),
        )
    if isinstance(formula, Release):
        return Release(
            push_negation(formula.left),
            push_negation(formula.right),
        )
    if isinstance(formula, WeakUntil):
        return WeakUntil(
            push_negation(formula.left),
            push_negation(formula.right),
        )
        
    # Unexpected Node Type.
    raise NotImplementedError(f"Unsupported formula type: {type(formula)}")


def negate_formula(formula: Formula) -> Formula:
    """
    Helper function that returns the negation of formula in NNF.
    
    Parameters
    ----------
    formula : Formula
        The original LTL formula.
        
    Returns
    -------
    Formula
        An equivalent formula representing '!formula' in NNF.
    """
    no_imp = eliminate_implication(formula)
    return push_negation(Not(no_imp))
