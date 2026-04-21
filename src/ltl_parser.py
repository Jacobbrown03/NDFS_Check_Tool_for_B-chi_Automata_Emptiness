"""ltl_parser.py

Utility for turning a textual LTL formula into an AST built from the node
classes defined in `src.ast_nodes`. The parser follows the following
precedence rules:
 
    -> lowest precedence
    || disjunction
    && conjunction
    temporal operators (U, R, W)
    unary operators (!, X, F, G) and parentheses have the highest precedence
"""

from src.ast_nodes import (
    Atomic, 
    Implies, 
    Or, And, 
    Until, Release, WeakUntil,
    Not, X, F, G,
    BoolConst,
    Formula)

# -------------------------------------------------------------------------
# Lexical Analysis
# -------------------------------------------------------------------------
def tokenize(text: str) -> list[str]:
    """Convert a raw formula string into a list of tokens.
    
    Parameters
    ----------
    text: str
        The raw formula string.
        
    Returns
    -------
    list[str]
        The tokenized formula as a list of strings.
    """
    spaced = (
        text.replace("(", " ( ")
        .replace(")", " ) ")
        .replace("&&", " && ")
        .replace("||", " || ")
        .replace("->", " -> ")
        .replace("!" , " ! ")
        .replace("TRUE", " TRUE ")
        .replace("FALSE", " FALSE ")
    )
    # filter out any empty strings that may appear after the split
    return [tok for tok in spaced.split() if tok]

# -------------------------------------------------------------------------
# Recursive-Descent Parser
# -------------------------------------------------------------------------
class Parser:
    """A recursive-descent parser for LTL formulas. The parsing methods are
        organized according to operator precedence, with the lowest precedence
        at the top and the highest at the bottom. The `parse` method serves as
        the entry point, and it ensures that the entire token list is consumed.
        The parser raises ValueError with informative messages when it encounters
        unexpected tokens or end-of-input.
        The resulting AST is built from the node classes defined in `src.ast_nodes`.
        The supported syntax includes:
        - Atomic propositions (any token that is not an operator or parenthesis)
        - Boolean constants: TRUE, FALSE
        - Unary operators: ! (negation), X (next), F (eventually), G (globally)
        - Binary operators: && (and), || (or), -> (implies)
        - Temporal binary operators: U (until), R (release), W (weak until)
        - Parentheses for grouping
        
        Parameters
        ----------
        tokens: list[str]
            The tokenized formula as a list of strings.
            
        Returns
        -------
        Formula
            The parsed formula as an AST.
        """
    def __init__(self,tokens: list[str]) -> None:
        self.tokens = tokens
        self.pos = 0
    
    def peek(self) -> str | None:
        # Return the next token without consuming it, or None if at EOF.
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]
    
    def consume(self, expected: str | None = None) -> str:
        # Return the next token and advance the cursor.
        token = self.peek()
        if token is None:
            raise ValueError("Unexpected end of formula")
        if expected is not None and token != expected:
            raise ValueError(f"Expected '{expected}', got '{token}'")
        self.pos += 1
        return token
    
    # Parsing Entry Point
    def parse(self) -> Formula:
        # Parse the whole token list and ensure no trailing tokens remain
        formula = self.parse_implies()
        if self.peek() is not None:
            raise ValueError(f"Unexpected token '{self.peek()}' at position {self.pos}")
        return formula

    # Grammar Rules (ordered by precedence, highest at the bottom)
    def parse_implies(self) -> Formula:
        # Implication (->)
        left = self.parse_or()
        while self.peek() == "->":
            self.consume("->")
            right = self.parse_or()
            left = Implies(left, right)
        return left
    
    def parse_or(self) -> Formula:
        # Disjunction (||)
        left = self.parse_and()
        while self.peek() == "||":
            self.consume("||")
            right = self.parse_and()
            left = Or(left, right)
        return left
    
    def parse_and(self) -> Formula:
        # Conjunction (&&)
        left = self.parse_temporal()
        while self.peek() == "&&":
            self.consume("&&")
            right = self.parse_temporal()
            left = And(left, right)
        return left
    
    def parse_temporal(self) -> Formula:
        # Temporal (unary ('U' | 'R' | 'W') Unary)
        
        left = self.parse_unary()
        while (tok := self.peek()) in ("U", "R", "W"):
            self.consume(tok)
            right = self.parse_unary()
            if tok == "U":
                left = Until(left, right)
            elif tok == "R":
                left = Release(left, right)
            else:
                left = WeakUntil(left, right)
        return left
    
    def parse_unary(self) -> Formula:
        # unary ->
        #       '!' unary
        #     | 'X' unary
        #     | 'F' unary
        #     | 'G' unary
        #     | '(' implies ')'
        #     | atomic
        tok = self.peek()
        
        # Negation
        if tok == "!":
            self.consume("!")
            return Not(self.parse_unary())
        
        # Temporal next
        if tok == "X":
            self.consume("X")
            return X(self.parse_unary())
        
        # Temporal Eventually
        if tok == "F":
            self.consume("F")
            return F(self.parse_unary())
        
        # Temporal Globally
        if tok == "G":
            self.consume("G")
            return G(self.parse_unary())
        
        # Parenthesised sub-formula
        if tok == "(":
            self.consume("(")
            inner = self.parse_implies()
            self.consume(")")
            return inner
        
        # Boolean Constants
        if tok == "TRUE":
            self.consume()
            return BoolConst(True)
        
        if tok == "FALSE":
            self.consume()
            return BoolConst(False)
        
        # End-of-input while a token is expired
        if tok is None:
            raise ValueError("Unexpected end of formula")
        
        # Anything else is treated as an atomic proposition
        self.consume()
        return Atomic(tok)

def parse_formula(text: str) -> Formula:
    """Parse a single LTL formula given as a string.
    
    Parameters
    ----------
    text: str
        The raw formula string.
        
    Returns
    -------
    Formula
        The parsed formula as an AST.
    """
    tokens = tokenize(text)
    return Parser(tokens).parse()

def load_formulas (path: str) -> list[Formula]:
    """Read a file line-by-line and return a list of parsed LTL formulas.
    
    Parameters
    ----------
    path: str
        Path to a LTL formula file. Lines starting with ``#`` are treated
        as comments and ignored.
        
    Returns
    -------
    list[Formula]
        A list of parsed LTL formulas.
    """
    formulas: list[Formula] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            # Ignore comments and empty lines
            if not line or line.startswith("#"):
                continue
            formulas.append(parse_formula(line))
    return formulas
