"""Simple Abstract Syntax Tree (AST) definitions for propositional
and LTL formulas

Each concrete subclass of :class:`Formula` implements :meth:`to_string`
which produces a human-readable representation of the formula. The classes
are immutable (``frozen=True``) so they can be safely used as dictionary
keys or stored in sets.
"""

from dataclasses import dataclass

# -------------------------------------------------------------------------
# Base Class
# -------------------------------------------------------------------------
class Formula:
    """Abstract base for all formula nodes
    
    Sub-classes must implement :meth:`to-string` which returns a textual
    representation of the formula.
    """
    def to_string(self) -> str:
        raise NotImplementedError

# -------------------------------------------------------------------------
# Atomic Proposition
# -------------------------------------------------------------------------
@dataclass(frozen=True)
class Atomic(Formula):
    """Leaf node representing a propositional variable."""
    name: str               # Identifier of the Atomic Proposition

    def to_string(self) -> str:
        return self.name    # e.g. ``p``

# -------------------------------------------------------------------------
# Unary Operators
# -------------------------------------------------------------------------
@dataclass(frozen=True)
class Not(Formula):
    """Logical Negation"""
    child: Formula          # Formula being negated

    def to_string(self) -> str:
        return f"!({self.child.to_string()})"
    
@dataclass(frozen=True)
class X(Formula):
    """Next Operator (LTL)"""
    child: Formula          # Formula that must hold in the next state

    def to_string(self) -> str:
        return f"X {self.child.to_string()}"

@dataclass(frozen=True)
class F(Formula):
    """Eventually (Future) Operator (LTL)"""
    child: Formula          # Formula that must hold at some future state

    def to_string(self) -> str:
        return f"F {self.child.to_string()}"

@dataclass(frozen=True)
class G(Formula):
    """Globally (Always) Operator (LTL)"""
    child: Formula          # Formula that must hold in all future states

    def to_string(self) -> str:
        return f"G {self.child.to_string()}"

# -------------------------------------------------------------------------
# Binary Propositional Operators
# -------------------------------------------------------------------------
@dataclass(frozen=True)
class And(Formula):
    """Logical Conjunction"""
    left: Formula           # Left operand
    right: Formula          # Right operand

    def to_string(self) -> str:
        return f"({self.left.to_string()} && {self.right.to_string()})"

@dataclass(frozen=True)
class Or(Formula):
    """Logical Disjunction"""
    left: Formula           # Left operand
    right: Formula          # Right operand

    def to_string(self) -> str:
        return f"({self.left.to_string()} || {self.right.to_string()})"

@dataclass(frozen=True)
class Implies(Formula):
    """Logical Implication (A -> B)"""
    left: Formula           # Antecedent
    right: Formula          # Consequent

    def to_string(self) -> str:
        return f"({self.left.to_string()} -> {self.right.to_string()})"
