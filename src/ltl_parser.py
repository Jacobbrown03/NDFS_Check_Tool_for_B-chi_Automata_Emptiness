# Parses formulas from the .txt file into ASTs
# For a short project, a hand-writtten recursive descent parser is fine

from src.ast_nodes import Atomic, Not, And, Or, Implies, X, F, G, Formula


def tokenize(text: str) -> list[str]:
    spaced = (
        text.replace("(", " ( ")
        .replace(")", " ) ")
        .replace("&&", " && ")
        .replace("||", " || ")
        .replace("->", " -> ")
    )
    # keep ! attached if it's standalone
    spaced = spaced.replace("!", " ! ")
    return [tok for tok in spaced.split() if tok]


class Parser:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> str | None:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def consume(self, expected: str | None = None) -> str:
        token = self.peek()
        if token is None:
            raise ValueError("Unexpected end of formula")
        if expected is not None and token != expected:
            raise ValueError(f"Expected '{expected}', got '{token}'")
        self.pos += 1
        return token

    def parse(self) -> Formula:
        formula = self.parse_implies()
        if self.peek() is not None:
            raise ValueError(f"Unexpected token: {self.peek()}")
        return formula

    def parse_implies(self) -> Formula:
        left = self.parse_until()
        while self.peek() == "->":
            self.consume("->")
            right = self.parse_until()
            left = Implies(left, right)
        return left

    def parse_or(self) -> Formula:
        left = self.parse_and()
        while self.peek() == "||":
            self.consume("||")
            right = self.parse_and()
            left = Or(left, right)
        return left

    def parse_and(self) -> Formula:
        left = self.parse_unary()
        while self.peek() == "&&":
            self.consume("&&")
            right = self.parse_unary()
            left = And(left, right)
        return left

    def parse_unary(self) -> Formula:
        tok = self.peek()

        if tok == "!":
            self.consume("!")
            return Not(self.parse_unary())
        if tok == "X":
            self.consume("X")
            return X(self.parse_unary())
        if tok == "F":
            self.consume("F")
            return F(self.parse_unary())
        if tok == "G":
            self.consume("G")
            return G(self.parse_unary())
        if tok == "(":
            self.consume("(")
            inner = self.parse_implies()
            self.consume(")")
            return inner
        if tok is None:
            raise ValueError("Unexpected end of formula")

        self.consume()
        return Atomic(tok)


def parse_formula(text: str) -> Formula:
    tokens = tokenize(text)
    return Parser(tokens).parse()


def load_formulas(path: str) -> list[Formula]:
    formulas: list[Formula] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            formulas.append(parse_formula(line))
    return formulas