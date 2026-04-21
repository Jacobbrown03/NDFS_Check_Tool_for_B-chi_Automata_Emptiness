"""ast_nodes.py

Abstract Syntax Tree (AST) definitions for propositional and LTL formulas

Each subclass implements the method 'to_string()' which produces a
human-readable representation of the formula. The classes are
immutable (frozen=True) so they can be safely used as dictionary
keys or stored in sets.
"""

from dataclasses import dataclass

# -------------------------------------------------------------------------
# Base Class
# -------------------------------------------------------------------------
class Formula:
    # Base for all formula nodes
    def to_string(self) -> str:
        raise NotImplementedError

# -------------------------------------------------------------------------
# Atomic Proposition
# -------------------------------------------------------------------------
@dataclass(frozen=True)
class Atomic(Formula):
    # Node representing a propositional variable
    name: str

    def to_string(self) -> str:
        return self.name 

# -------------------------------------------------------------------------
# Unary Operators
# -------------------------------------------------------------------------
@dataclass(frozen=True)
class Not(Formula):
    # Logical Negation
    child: Formula

    def to_string(self) -> str:
        return f"!({self.child.to_string()})"
    
@dataclass(frozen=True)
class X(Formula):
    # Next Operator
    child: Formula 

    def to_string(self) -> str:
        return f"X {self.child.to_string()}"

@dataclass(frozen=True)
class F(Formula):
    # Eventually Operator
    child: Formula

    def to_string(self) -> str:
        return f"F {self.child.to_string()}"

@dataclass(frozen=True)
class G(Formula):
    # Globally Operator
    child: Formula

    def to_string(self) -> str:
        return f"G {self.child.to_string()}"

# -------------------------------------------------------------------------
# Binary Propositional Operators
# -------------------------------------------------------------------------
@dataclass(frozen=True)
class And(Formula):
    # Logical Conjunction
    left: Formula
    right: Formula

    def to_string(self) -> str:
        return f"({self.left.to_string()} && {self.right.to_string()})"

@dataclass(frozen=True)
class Or(Formula):
    # Logical Disjunction
    left: Formula  
    right: Formula 

    def to_string(self) -> str:
        return f"({self.left.to_string()} || {self.right.to_string()})"

@dataclass(frozen=True)
class Implies(Formula):
    # Logical Implication
    left: Formula 
    right: Formula 

    def to_string(self) -> str:
        return f"({self.left.to_string()} -> {self.right.to_string()})"

# -------------------------------------------------------------------------
# Temporal Propositional Operators
# -------------------------------------------------------------------------
@dataclass(frozen=True)
class Until(Formula):
    # Temporal Until
    left: Formula 
    right: Formula
    
    def to_string(self) -> str:
        return f"({self.left.to_string()} U {self.right.to_string()})"

@dataclass(frozen=True)
class Release(Formula):
    # Temporal Release
    left: Formula
    right: Formula 
    
    def to_string(self) -> str:
        return f"({self.left.to_string()} R {self.right.to_string()})"

@dataclass(frozen=True)
class WeakUntil(Formula):
    # Temporal Weak Until
    left: Formula 
    right: Formula
    
    def to_string(self) -> str:
        return f"({self.left.to_string()} W {self.right.to_string()})"

# -------------------------------------------------------------------------
# Boolean constants
# -------------------------------------------------------------------------
@dataclass(frozen=True)
class BoolConst(Formula):
    # True or False literal
    value: bool

    def to_string(self) -> str:
        return "TRUE" if self.value else "FALSE"
