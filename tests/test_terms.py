"""
Unit Tests for Terms Module
===========================

Tests for term and proposition definitions, constructors,
pretty printing, substitution, and alpha equality.
"""

import pytest
from proof_assistant.core.terms import (
    # Constructors
    var, const, fun, pred,
    implies, and_, or_, not_,
    forall, exists, bottom, eq, iff, top,
    # Pretty printing
    term_repr, prop_repr,
    # Substitution
    fresh_var, free_vars, free_vars_term,
    substitute_var, substitute, subst_term, subst_term_var,
    beta_reduce,
    # Equality
    alpha_eq, term_eq,
)


class TestTermConstructors:
    """Tests for term constructors."""
    
    def test_var(self):
        """Test variable creation."""
        x = var("x")
        assert x == ("var", "x")
    
    def test_const(self):
        """Test constant creation."""
        zero = const("Zero")
        assert zero == ("const", "Zero")
    
    def test_fun(self):
        """Test function application creation."""
        succ = fun("Succ", [var("x")])
        assert succ == ("fun", "Succ", [("var", "x")])
        
        # Nested function
        add = fun("Add", [var("x"), var("y")])
        assert add == ("fun", "Add", [("var", "x"), ("var", "y")])
    
    def test_lambda(self):
        """Test lambda abstraction creation."""
        lam = ("lambda", ["x"], var("x"))
        assert lam[0] == "lambda"
        assert lam[1] == ["x"]
        assert lam[2] == ("var", "x")


class TestPropConstructors:
    """Tests for proposition constructors."""
    
    def test_pred(self):
        """Test predicate creation."""
        p = pred("P", [])
        assert p == ("pred", "P", [])
        
        p_of_x = pred("P", [var("x")])
        assert p_of_x == ("pred", "P", [("var", "x")])
    
    def test_implies(self):
        """Test implication creation."""
        p = pred("P", [])
        q = pred("Q", [])
        imp = implies(p, q)
        assert imp == ("implies", ("pred", "P", []), ("pred", "Q", []))
    
    def test_and(self):
        """Test conjunction creation."""
        p = pred("P", [])
        q = pred("Q", [])
        conj = and_(p, q)
        assert conj == ("and", ("pred", "P", []), ("pred", "Q", []))
    
    def test_or(self):
        """Test disjunction creation."""
        p = pred("P", [])
        q = pred("Q", [])
        disj = or_(p, q)
        assert disj == ("or", ("pred", "P", []), ("pred", "Q", []))
    
    def test_not(self):
        """Test negation creation."""
        p = pred("P", [])
        neg = not_(p)
        assert neg == ("not", ("pred", "P", []))
    
    def test_forall(self):
        """Test universal quantification creation."""
        formula = forall("x", pred("P", [var("x")]))
        assert formula == ("forall", "x", ("pred", "P", [("var", "x")]))
    
    def test_exists(self):
        """Test existential quantification creation."""
        formula = exists("x", pred("P", [var("x")]))
        assert formula == ("exists", "x", ("pred", "P", [("var", "x")]))
    
    def test_bottom(self):
        """Test bottom creation."""
        bot = bottom()
        assert bot == ("bottom",)
    
    def test_eq(self):
        """Test equality creation."""
        eq_prop = eq(var("x"), var("y"))
        assert eq_prop == ("pred", "=", [("var", "x"), ("var", "y")])
    
    def test_iff(self):
        """Test biconditional creation."""
        p = pred("P", [])
        q = pred("Q", [])
        bicond = iff(p, q)
        # iff should be P -> Q ∧ Q -> P
        assert bicond[0] == "and"
    
    def test_top(self):
        """Test top (true) creation."""
        t = top()
        assert t == ("not", ("bottom",))


class TestPrettyPrinting:
    """Tests for pretty printing functions."""
    
    def test_term_repr_var(self):
        """Test variable representation."""
        assert term_repr(var("x")) == "x"
    
    def test_term_repr_const(self):
        """Test constant representation."""
        assert term_repr(const("Zero")) == "Zero"
    
    def test_term_repr_fun(self):
        """Test function representation."""
        succ = fun("Succ", [var("x")])
        assert term_repr(succ) == "Succ(x)"
    
    def test_prop_repr_pred(self):
        """Test predicate representation."""
        assert prop_repr(pred("P", [])) == "P"
        assert prop_repr(pred("P", [var("x")])) == "P(x)"
    
    def test_prop_repr_connectives(self):
        """Test connective representation."""
        p = pred("P", [])
        q = pred("Q", [])
        
        assert prop_repr(and_(p, q)) == "P ∧ Q"
        assert prop_repr(or_(p, q)) == "P ∨ Q"
        assert prop_repr(implies(p, q)) == "P → Q"
        assert prop_repr(not_(p)) == "¬P"
    
    def test_prop_repr_quantifiers(self):
        """Test quantifier representation."""
        assert prop_repr(forall("x", pred("P", [var("x")]))) == "∀x. P(x)"
        assert prop_repr(exists("x", pred("P", [var("x")]))) == "∃x. P(x)"
    
    def test_prop_repr_bottom(self):
        """Test bottom representation."""
        assert prop_repr(bottom()) == "⊥"
    
    def test_prop_repr_eq(self):
        """Test equality representation."""
        assert prop_repr(eq(var("x"), var("y"))) == "x = y"


class TestFreshVar:
    """Tests for fresh variable generation."""
    
    def test_fresh_var_empty(self):
        """Test fresh variable with empty set."""
        assert fresh_var(set()) == "x1"
    
    def test_fresh_var_existing(self):
        """Test fresh variable with existing names."""
        existing = {"x", "x1", "x2"}
        assert fresh_var(existing) == "x3"
    
    def test_fresh_var_custom_base(self):
        """Test fresh variable with custom base."""
        assert fresh_var({"y"}, "y") == "y1"


class TestFreeVars:
    """Tests for free variable computation."""
    
    def test_free_vars_var(self):
        """Test free variables in variable."""
        assert free_vars(var("x")) == {"x"}
    
    def test_free_vars_pred(self):
        """Test free variables in predicate."""
        p = pred("P", [var("x"), var("y")])
        assert free_vars(p) == {"x", "y"}
    
    def test_free_vars_forall(self):
        """Test free variables in universal quantification."""
        formula = forall("x", implies(pred("P", [var("x")]), pred("Q", [var("y")])))
        # x is bound, y is free
        assert free_vars(formula) == {"y"}
    
    def test_free_vars_exists(self):
        """Test free variables in existential quantification."""
        formula = exists("x", and_(pred("P", [var("x")]), pred("Q", [var("z")])))
        # x is bound, z is free
        assert free_vars(formula) == {"z"}
    
    def test_free_vars_nested(self):
        """Test free variables in nested quantifiers."""
        formula = forall("x", exists("y", pred("R", [var("x"), var("y"), var("z")])))
        # x and y are bound, z is free
        assert free_vars(formula) == {"z"}


class TestSubstitution:
    """Tests for substitution functions."""
    
    def test_substitute_var_simple(self):
        """Test simple variable substitution in proposition."""
        p = pred("P", [var("x")])
        result = substitute(p, "x", var("y"))
        assert result == ("pred", "P", [("var", "y")])
    
    def test_substitute_forall(self):
        """Test substitution under universal quantifier."""
        formula = forall("x", pred("P", [var("x"), var("y")]))
        # Substitute y with z - should work because y is free
        result = substitute(formula, "y", var("z"))
        # x should remain bound, y should become z
        assert result[1] == "x"
        assert result[2] == ("pred", "P", [("var", "x"), ("var", "z")])
    
    def test_substitute_forall_capture_avoidance(self):
        """Test that substitution avoids variable capture."""
        # ∀x. P(x, y) with substitution y -> x should rename bound variable
        formula = forall("x", pred("P", [var("x"), var("y")]))
        result = substitute(formula, "y", var("x"))
        # The bound variable should be renamed to avoid capture
        assert result[0] == "forall"
        # The new bound variable should be fresh
        assert result[1] != "x"
    
    def test_substitute_term(self):
        """Test term substitution."""
        t = fun("f", [var("x"), var("y")])
        result = subst_term(t, "x", const("A"))
        assert result == ("fun", "f", [("const", "A"), ("var", "y")])


class TestAlphaEquality:
    """Tests for alpha equality."""
    
    def test_alpha_eq_same(self):
        """Test alpha equality of identical propositions."""
        p = pred("P", [var("x")])
        assert alpha_eq(p, p)
    
    def test_alpha_eq_forall(self):
        """Test alpha equality of universally quantified propositions."""
        p1 = forall("x", pred("P", [var("x")]))
        p2 = forall("y", pred("P", [var("y")]))
        assert alpha_eq(p1, p2)
    
    def test_alpha_eq_exists(self):
        """Test alpha equality of existentially quantified propositions."""
        p1 = exists("x", pred("P", [var("x")]))
        p2 = exists("y", pred("P", [var("y")]))
        assert alpha_eq(p1, p2)
    
    def test_alpha_eq_different(self):
        """Test alpha equality of different propositions."""
        p1 = pred("P", [var("x")])
        p2 = pred("Q", [var("x")])
        assert not alpha_eq(p1, p2)
    
    def test_alpha_eq_nested(self):
        """Test alpha equality of nested quantifiers."""
        p1 = forall("x", forall("y", pred("R", [var("x"), var("y")])))
        p2 = forall("a", forall("b", pred("R", [var("a"), var("b")])))
        assert alpha_eq(p1, p2)


class TestTermEquality:
    """Tests for term equality."""
    
    def test_term_eq_var(self):
        """Test variable equality."""
        assert term_eq(var("x"), var("x"))
        assert not term_eq(var("x"), var("y"))
    
    def test_term_eq_const(self):
        """Test constant equality."""
        assert term_eq(const("Zero"), const("Zero"))
        assert not term_eq(const("Zero"), const("One"))
    
    def test_term_eq_fun(self):
        """Test function equality."""
        f1 = fun("Succ", [var("x")])
        f2 = fun("Succ", [var("x")])
        assert term_eq(f1, f2)
    
    def test_term_eq_lambda(self):
        """Test lambda equality (alpha equivalence)."""
        l1 = ("lambda", ["x"], var("x"))
        l2 = ("lambda", ["y"], var("y"))
        assert term_eq(l1, l2)


class TestBetaReduce:
    """Tests for beta reduction."""
    
    def test_beta_reduce_simple(self):
        """Test simple beta reduction."""
        # (λx. x) applied to a
        app = ("app", ("lambda", ["x"], var("x")), const("a"))
        result = beta_reduce(app)
        assert result == ("const", "a")
    
    def test_beta_reduce_nested(self):
        """Test nested beta reduction."""
        # (λx. (λy. x)) applied to a, then b
        inner = ("lambda", ["y"], var("x"))
        outer = ("lambda", ["x"], inner)
        app1 = ("app", outer, const("a"))
        app2 = ("app", app1, const("b"))
        result = beta_reduce(app2)
        assert result == ("const", "a")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
