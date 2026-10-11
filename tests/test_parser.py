"""
Unit Tests for Parser Module
============================

Tests for the lexer and parser functions.
"""

import pytest
from proof_assistant.core.parser import lex, parse_formula, parse_term, Parser
from proof_assistant.core.terms import (
    var, const, fun, pred,
    implies, and_, or_, not_,
    forall, exists, bottom, eq,
)


class TestLexer:
    """Tests for the lexer."""
    
    def test_lex_var(self):
        """Test tokenization of variables."""
        tokens = lex("x")
        assert len(tokens) == 1
        assert tokens[0][0] == "VAR"
        assert tokens[0][1] == "x"
    
    def test_lex_const(self):
        """Test tokenization of constants."""
        tokens = lex("Zero")
        assert len(tokens) == 1
        assert tokens[0][0] == "CONST"
        assert tokens[0][1] == "Zero"
    
    def test_lex_connectives(self):
        """Test tokenization of logical connectives."""
        # Unicode
        tokens = lex("∧ ∨ → ¬")
        kinds = [t[0] for t in tokens]
        assert kinds == ["AND", "OR", "IMPLIES", "NOT"]
        
        # ASCII alternatives
        tokens = lex("and or implies not")
        kinds = [t[0] for t in tokens]
        assert kinds == ["AND", "OR", "IMPLIES", "NOT"]
    
    def test_lex_quantifiers(self):
        """Test tokenization of quantifiers."""
        # Unicode
        tokens = lex("∀ ∃")
        kinds = [t[0] for t in tokens]
        assert kinds == ["FORALL", "EXISTS"]
        
        # ASCII alternatives
        tokens = lex("forall exists")
        kinds = [t[0] for t in tokens]
        assert kinds == ["FORALL", "EXISTS"]
    
    def test_lex_bottom(self):
        """Test tokenization of bottom."""
        tokens = lex("⊥")
        assert tokens[0][0] == "BOTTOM"
        
        tokens = lex("False")
        assert tokens[0][0] == "BOTTOM"
    
    def test_lex_punctuation(self):
        """Test tokenization of punctuation."""
        tokens = lex("( ) , .")
        kinds = [t[0] for t in tokens]
        assert kinds == ["LPAREN", "RPAREN", "COMMA", "DOT"]


class TestParseFormula:
    """Tests for formula parsing."""
    
    def test_parse_propositional_constant(self):
        """Test parsing propositional constants."""
        p = parse_formula("P")
        assert p == ("pred", "P", [])
    
    def test_parse_predicate(self):
        """Test parsing predicate application."""
        p = parse_formula("P(x)")
        assert p == ("pred", "P", [("var", "x")])
    
    def test_parse_implication(self):
        """Test parsing implication."""
        p = parse_formula("P -> Q")
        assert p == ("implies", ("pred", "P", []), ("pred", "Q", []))
    
    def test_parse_implication_unicode(self):
        """Test parsing implication with Unicode."""
        p = parse_formula("P → Q")
        assert p == ("implies", ("pred", "P", []), ("pred", "Q", []))
    
    def test_parse_conjunction(self):
        """Test parsing conjunction."""
        p = parse_formula("P and Q")
        assert p == ("and", ("pred", "P", []), ("pred", "Q", []))
    
    def test_parse_disjunction(self):
        """Test parsing disjunction."""
        p = parse_formula("P or Q")
        assert p == ("or", ("pred", "P", []), ("pred", "Q", []))
    
    def test_parse_negation(self):
        """Test parsing negation."""
        p = parse_formula("not P")
        assert p == ("not", ("pred", "P", []))
    
    def test_parse_forall(self):
        """Test parsing universal quantification."""
        p = parse_formula("forall x. P(x)")
        assert p == ("forall", "x", ("pred", "P", [("var", "x")]))
    
    def test_parse_exists(self):
        """Test parsing existential quantification."""
        p = parse_formula("exists x. P(x)")
        assert p == ("exists", "x", ("pred", "P", [("var", "x")]))
    
    def test_parse_bottom(self):
        """Test parsing bottom."""
        p = parse_formula("False")
        assert p == ("bottom",)
    
    def test_parse_equality(self):
        """Test parsing equality."""
        p = parse_formula("x = y")
        assert p == ("pred", "=", [("var", "x"), ("var", "y")])
    
    def test_parse_parentheses(self):
        """Test parsing parenthesized formulas."""
        p = parse_formula("(P -> Q) and R")
        assert p[0] == "and"
        assert p[1] == ("implies", ("pred", "P", []), ("pred", "Q", []))
        assert p[2] == ("pred", "R", [])
    
    def test_parse_complex(self):
        """Test parsing complex formulas."""
        # ∀x. P(x) → Q(x)
        p = parse_formula("forall x. P(x) -> Q(x)")
        assert p[0] == "forall"
        assert p[1] == "x"
        assert p[2][0] == "implies"
    
    def test_parse_nested_quantifiers(self):
        """Test parsing nested quantifiers."""
        # ∀x. ∀y. R(x, y)
        p = parse_formula("forall x. forall y. R(x, y)")
        assert p[0] == "forall"
        assert p[2][0] == "forall"
    
    def test_parse_operator_precedence(self):
        """Test operator precedence."""
        # and binds tighter than or
        p = parse_formula("P and Q or R")
        assert p[0] == "or"
        assert p[1] == ("and", ("pred", "P", []), ("pred", "Q", []))
        
        # implies binds loosely
        p = parse_formula("P and Q -> R")
        assert p[0] == "implies"


class TestParseTerm:
    """Tests for term parsing."""
    
    def test_parse_var(self):
        """Test parsing variable."""
        t = parse_term("x")
        assert t == ("var", "x")
    
    def test_parse_const(self):
        """Test parsing constant."""
        t = parse_term("Zero")
        assert t == ("const", "Zero")
    
    def test_parse_function(self):
        """Test parsing function application."""
        t = parse_term("Succ(x)")
        assert t == ("fun", "Succ", [("var", "x")])
    
    def test_parse_nested_function(self):
        """Test parsing nested function application."""
        t = parse_term("Add(x, y)")
        assert t == ("fun", "Add", [("var", "x"), ("var", "y")])
    
    def test_parse_lambda(self):
        """Test parsing lambda abstraction."""
        t = parse_term("lambda x. x")
        assert t == ("lambda", ["x"], ("var", "x"))


class TestParserErrors:
    """Tests for parser error handling."""
    
    def test_parse_empty(self):
        """Test parsing empty string."""
        with pytest.raises(Exception):
            parse_formula("")
    
    def test_parse_unexpected_token(self):
        """Test parsing with unexpected token."""
        with pytest.raises(Exception):
            parse_formula("P ->")
    
    def test_parse_mismatched_parens(self):
        """Test parsing with mismatched parentheses."""
        with pytest.raises(Exception):
            parse_formula("(P -> Q")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
