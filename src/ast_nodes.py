# Simple classes for LTL formulas
# Examples
# Atomic
# Not
# And
# Or
# Next
# Eventually
# Globally
# Until
# Implies

from dataclasses import dataclass


class Formula:
    def to_string(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class Atomic(Formula):
    name: str

    def to_string(self) -> str:
        return self.name


@dataclass(frozen=True)
class Not(Formula):
    child: Formula

    def to_string(self) -> str:
        return f"!({self.child.to_string()})"


@dataclass(frozen=True)
class And(Formula):
    left: Formula
    right: Formula

    def to_string(self) -> str:
        return f"({self.left.to_string()} && {self.right.to_string()})"


@dataclass(frozen=True)
class Or(Formula):
    left: Formula
    right: Formula

    def to_string(self) -> str:
        return f"({self.left.to_string()} || {self.right.to_string()})"


@dataclass(frozen=True)
class Implies(Formula):
    left: Formula
    right: Formula

    def to_string(self) -> str:
        return f"({self.left.to_string()} -> {self.right.to_string()})"


@dataclass(frozen=True)
class X(Formula):
    child: Formula

    def to_string(self) -> str:
        return f"X {self.child.to_string()}"


@dataclass(frozen=True)
class F(Formula):
    child: Formula

    def to_string(self) -> str:
        return f"F {self.child.to_string()}"


@dataclass(frozen=True)
class G(Formula):
    child: Formula

    def to_string(self) -> str:
        return f"G {self.child.to_string()}"


@dataclass(frozen=True)
class U(Formula):
    left: Formula
    right: Formula

    def to_string(self) -> str:
        return f"({self.left.to_string()} U {self.right.to_string()})"