"""ltl_negation.py

Utility functions that transform an LTL formula into its **negation in
Negation Normal Form (NNF)**. The transformation is performed in two steps:

1. **Eliminate Implication** - Replace every ``A -> B`` with ``!A || B``.
2. **Push Negations** - Move ``!`` inward using Demorgan laws and the
   dualities of the temporal operators (``X, F, G``).
   
The result of the ``negate_formula`` is a formula that is logically
equivalent to the original formula's negation and contains only the
connectives ``!, &&, ||, X, F, G`` with ``!`` applied directly to
atomic propositions.
"""

from src.ast_nodes import Atomic, Not, And, Or, Implies, X, F, G, Formula

def eliminate_implication(formula: Formula) -> Formula:
    """
    Recursively replace every implication in formula. The function returns
    a new formula tree that no longer contains ``Implies`` nodes.
    
    Parameters
    ----------
    formula: Formula
        The (possibly nested) LTL formula to transform
        
    Returns
    -------
    Formula
        An equivalent formula without ``Implies``.
    """
    # Base Case - Atomic Propositions are unchanged
    if isinstance(formula, Atomic):
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
    
    # Implication Case - Replace ``!left || right``.
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
    
    # Anything else is not part of the supported AST.
    raise NotImplementedError(f"Unsupported formula type: {type(formula)}")

def push_negation(formula: Formula) -> Formula:
    """
    Push a leading negation inward until it only appears in front of
    atomic propositions. This yields NNF.
    
    The function expects that the input formula **does not contain
    ``Implies``** - that transformation should be performed first by
    :func:`eliminate_implication`.
    
    Parameters
    ----------
    formula : Formula
        A formula possibly containing a top-level ``Not`` node.
        
    Returns
    -------
    Formula
        An equivalent formula in NNF.
    """
    # Atomic Propositions are already in NNF.
    if isinstance(formula, Atomic):
        return formula

    # When we encounter a negation we apply the appropriate De Morgan
    # or temporal dualit yrule.
    if isinstance(formula, Not):
        child = formula.child

        # Negation of an Atomic Proposition stays as ``Not(atom)``
        if isinstance(child, Atomic):
            return formula
        
        # Double negation cancels out ``!!q`` -> ``q``
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

    # Unexpected Node Type.
    raise NotImplementedError(f"Unsupported formula type: {type(formula)}")


def negate_formula(formula: Formula) -> Formula:
    """
    Public helper that returns the negation of *formula* in NNF.
    
    The process is:
    1. Remove all implications(``->``) -> ``eliminate_implication``.
    2. Apply a top-level negation and push it inward -> ``push_negation``.
    
    Parameters
    ----------
    formula : Formula
        The original LTL formula.
        
    Returns
    -------
    Formula
        An equivalent formula representing ``!formula`` in NNF.
    """
    no_imp = eliminate_implication(formula)
    return push_negation(Not(no_imp))
