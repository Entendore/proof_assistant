"""
Lexer and Parser for Logical Formulas
=====================================

This module provides lexical analysis and parsing for logical formulas
in a human-readable syntax with Unicode support.

Supported Syntax:
    - Connectives: ∧ (and), ∨ (or), → (implies), ¬ (not), ↔ (iff)
    - Quantifiers: ∀ (forall), ∃ (exists)
    - Constants: ⊥ (bottom/false)
    - Equality: =
    - Variables: lowercase identifiers (x, y, z)
    - Constants: uppercase identifiers (P, Q, Zero)
    - Functions: Capitalized identifiers with arguments (Succ(x))

Example:
    >>> from proof_assistant.core.parser import parse_formula
    >>> formula = parse_formula("forall x. P(x) -> Q(x)")
    >>> print(formula)
    ('forall', 'x', ('implies', ('pred', 'P', [('var', 'x')]), ('pred', 'Q', [('var', 'x')])))
"""

import re
from typing import List, Tuple, Optional, Union

from .terms import (
    Term, Prop,
    var, const, fun, pred,
    implies, and_, or_, not_,
    forall, exists, bottom, eq
)


# === Token Definitions ===

TOKEN_SPECIFICATION = [
    ('FORALL',   r'∀|forall'),
    ('EXISTS',   r'∃|exists'),
    ('NOT',      r'¬|~|not\b'),
    ('BOTTOM',   r'⊥|False|false'),
    ('TOP',      r'True|true'),
    ('AND',      r'∧|&&|and\b'),
    ('OR',       r'∨|\|\||or\b'),
    ('IMPLIES',  r'→|->|=>|implies\b'),
    ('IFF',      r'↔|<=>|iff\b'),
    ('EQ',       r'='),
    ('DOT',      r'\.'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('COMMA',    r','),
    ('LAMBDA',   r'λ|\\|lambda\b'),
    ('VAR',      r'[a-z_][a-zA-Z0-9_]*'),
    ('CONST',    r'[A-Z][a-zA-Z0-9_]*'),
    ('SKIP',     r'[ \t\n]+'),
    ('MISMATCH', r'.'),
]

TOKEN_RE = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION))


# === Lexer ===

def lex(characters: str) -> List[Tuple[str, str, int, int]]:
    """Tokenize a string into a list of tokens.
    
    Args:
        characters: Input string to tokenize
        
    Returns:
        List of (type, value, start, end) tuples
        
    Raises:
        SyntaxError: If an unexpected character is encountered
    """
    tokens = []
    for mo in TOKEN_RE.finditer(characters):
        kind = mo.lastgroup
        value = mo.group()
        start = mo.start()
        end = mo.end()
        
        if kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(f'Unexpected character {value!r} at position {start}')
        else:
            tokens.append((kind, value, start, end))
    
    return tokens


# === Parser ===

class Parser:
    """Recursive descent parser for logical formulas.
    
    Grammar:
        formula     → implication
        implication → iff ( '→' iff )*
        iff         → disjunction ( '↔' disjunction )*
        disjunction → conjunction ( '∨' conjunction )*
        conjunction → negation ( '∧' negation )*
        negation    → '¬' negation | quantifier
        quantifier  → ( '∀' | '∃' ) VAR '.' formula | atomic
        atomic      → PRED '(' term_list ')' | VAR | CONST | '⊥' | '(' formula ')'
        term        → VAR | CONST | FUN '(' term_list ')' | 'λ' VAR+ '.' term | '(' term ')'
    """
    
    def __init__(self, tokens: List[Tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self) -> Optional[Tuple[str, str]]:
        """Look at the current token without consuming it."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def consume(self, expected_type: Optional[str] = None) -> Tuple[str, str]:
        """Consume and return the current token.
        
        Args:
            expected_type: If provided, verify the token type
            
        Returns:
            The consumed token
            
        Raises:
            SyntaxError: If the token doesn't match or input is exhausted
        """
        token = self.peek()
        if token is None:
            raise SyntaxError("Unexpected end of input")
        if expected_type and token[0] != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {token[0]}")
        self.pos += 1
        return token
    
    def parse(self) -> Prop:
        """Parse a complete formula.
        
        Returns:
            The parsed proposition
            
        Raises:
            SyntaxError: If parsing fails
        """
        result = self.parse_implication()
        if self.peek() is not None:
            raise SyntaxError(f"Unexpected token after end of expression: {self.peek()}")
        return result
    
    def parse_implication(self) -> Prop:
        """Parse implication (right-associative)."""
        left = self.parse_iff()
        while self.peek() and self.peek()[0] == 'IMPLIES':
            self.consume('IMPLIES')
            right = self.parse_implication()
            left = implies(left, right)
        return left
    
    def parse_iff(self) -> Prop:
        """Parse biconditional."""
        left = self.parse_or()
        while self.peek() and self.peek()[0] == 'IFF':
            self.consume('IFF')
            right = self.parse_or()
            left = and_(implies(left, right), implies(right, left))
        return left
    
    def parse_or(self) -> Prop:
        """Parse disjunction."""
        left = self.parse_and()
        while self.peek() and self.peek()[0] == 'OR':
            self.consume('OR')
            right = self.parse_and()
            left = or_(left, right)
        return left
    
    def parse_and(self) -> Prop:
        """Parse conjunction."""
        left = self.parse_not()
        while self.peek() and self.peek()[0] == 'AND':
            self.consume('AND')
            right = self.parse_not()
            left = and_(left, right)
        return left
    
    def parse_not(self) -> Prop:
        """Parse negation."""
        if self.peek() and self.peek()[0] == 'NOT':
            self.consume('NOT')
            prop = self.parse_not()
            return not_(prop)
        else:
            return self.parse_quantifier_or_atomic()
    
    def parse_quantifier_or_atomic(self) -> Prop:
        """Parse quantifiers or atomic formulas."""
        tok = self.peek()
        
        if tok and tok[0] == 'FORALL':
            self.consume('FORALL')
            var_token = self.consume('VAR')
            self.consume('DOT')
            body = self.parse_implication()
            return forall(var_token[1], body)
        
        elif tok and tok[0] == 'EXISTS':
            self.consume('EXISTS')
            var_token = self.consume('VAR')
            self.consume('DOT')
            body = self.parse_implication()
            return exists(var_token[1], body)
        
        else:
            return self.parse_atomic()
    
    def parse_atomic(self) -> Prop:
        """Parse atomic formulas, including infix equality."""
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input")
        
        # Parenthesized formula
        if tok[0] == 'LPAREN':
            self.consume('LPAREN')
            prop = self.parse_implication()
            self.consume('RPAREN')
            return prop
        
        # Predicate with arguments
        elif tok[0] == 'CONST':
            pred_name = self.consume('CONST')[1]
            if self.peek() and self.peek()[0] == 'LPAREN':
                self.consume('LPAREN')
                if self.peek() and self.peek()[0] == 'RPAREN':
                    self.consume('RPAREN')
                    return pred(pred_name, [])
                args = self.parse_term_list()
                self.consume('RPAREN')
                return pred(pred_name, args)
            # Check for infix equality after constant
            elif self.peek() and self.peek()[0] == 'EQ':
                self.consume('EQ')
                right = self.parse_term()
                return eq(const(pred_name), right)
            else:
                # Propostional constant (0-ary predicate)
                return pred(pred_name, [])
        
        # Variable as proposition - might be start of equality
        elif tok[0] == 'VAR':
            var_name = self.consume('VAR')[1]
            # Check if it's a predicate application
            if self.peek() and self.peek()[0] == 'LPAREN':
                self.consume('LPAREN')
                if self.peek() and self.peek()[0] == 'RPAREN':
                    self.consume('RPAREN')
                    return pred(var_name.capitalize(), [])
                args = self.parse_term_list()
                self.consume('RPAREN')
                return pred(var_name.capitalize(), args)
            # Check for infix equality: x = y
            elif self.peek() and self.peek()[0] == 'EQ':
                self.consume('EQ')
                right = self.parse_term()
                return eq(var(var_name), right)
            return var(var_name)
        
        # Bottom (false)
        elif tok[0] == 'BOTTOM':
            self.consume('BOTTOM')
            return bottom()
        
        # Top (true)
        elif tok[0] == 'TOP':
            self.consume('TOP')
            return not_(bottom())
        
        # Equality (prefix notation = t1 t2 or infix t1 = t2)
        elif tok[0] == 'EQ':
            self.consume('EQ')
            # Try infix parsing
            left = self.parse_term()
            if self.peek() and self.peek()[0] == 'EQ':
                self.consume('EQ')
                right = self.parse_term()
                return eq(left, right)
            else:
                raise SyntaxError("Expected second term for equality")
        
        else:
            raise SyntaxError(f"Unexpected token: {tok}")
    
    def parse_term_list(self) -> List[Term]:
        """Parse a comma-separated list of terms."""
        terms = [self.parse_term()]
        while self.peek() and self.peek()[0] == 'COMMA':
            self.consume('COMMA')
            terms.append(self.parse_term())
        return terms
    
    def parse_term(self) -> Term:
        """Parse a term."""
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input in term")
        
        # Variable
        if tok[0] == 'VAR':
            return var(self.consume('VAR')[1])
        
        # Constant or function
        elif tok[0] == 'CONST':
            name = self.consume('CONST')[1]
            if self.peek() and self.peek()[0] == 'LPAREN':
                self.consume('LPAREN')
                if self.peek() and self.peek()[0] == 'RPAREN':
                    self.consume('RPAREN')
                    return const(name)
                args = self.parse_term_list()
                self.consume('RPAREN')
                return fun(name, args)
            else:
                return const(name)
        
        # Lambda abstraction
        elif tok[0] == 'LAMBDA':
            self.consume('LAMBDA')
            params = []
            while self.peek() and self.peek()[0] == 'VAR':
                params.append(self.consume('VAR')[1])
            self.consume('DOT')
            body = self.parse_term()
            return ("lambda", params, body)
        
        # Parenthesized term
        elif tok[0] == 'LPAREN':
            self.consume('LPAREN')
            term = self.parse_term()
            self.consume('RPAREN')
            return term
        
        else:
            raise SyntaxError(f"Unexpected token in term: {tok}")


def parse_formula(formula_str: str) -> Prop:
    """Parse a formula string into an AST.
    
    Args:
        formula_str: String representation of the formula
        
    Returns:
        Proposition AST
        
    Raises:
        SyntaxError: If parsing fails
        
    Example:
        >>> parse_formula("P -> Q")
        ('implies', ('pred', 'P', []), ('pred', 'Q', []))
    """
    tokens = lex(formula_str)
    parser = Parser(tokens)
    return parser.parse()


def parse_term(term_str: str) -> Term:
    """Parse a term string into an AST.
    
    Args:
        term_str: String representation of the term
        
    Returns:
        Term AST
        
    Raises:
        SyntaxError: If parsing fails
        
    Example:
        >>> parse_term("Succ(x)")
        ('fun', 'Succ', [('var', 'x')])
    """
    tokens = lex(term_str)
    parser = Parser(tokens)
    return parser.parse_term()
