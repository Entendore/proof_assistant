"""
Term and Proposition Definitions
================================

This module defines the abstract syntax tree (AST) for terms and propositions
in our proof system. The design follows a minimalist approach using Python tuples
for efficient pattern matching.

Type Definitions:
    Term: First-order logic terms (variables, constants, functions, lambdas)
    Prop: Propositions (atomic predicates, logical connectives, quantifiers)
    Context: A list of named hypotheses
    Goal: A context paired with a proposition to prove

Example:
    >>> from proof_assistant.core.terms import *
    >>> # Create a simple proposition: P ∧ Q
    >>> p = pred("P", [])
    >>> q = pred("Q", [])
    >>> conjunction = and_(p, q)
    >>> # Create an implication: P → Q
    >>> implication = implies(p, q)
"""

from typing import List, Tuple, Union, Set, Optional
from dataclasses import dataclass

# === Type Aliases ===

Term = Union[
    Tuple[str, str],                         # ("var", name) - Variable
    Tuple[str, str],                         # ("const", name) - Constant
    Tuple[str, str, List['Term']],           # ("fun", name, args) - Function application
    Tuple[str, List[str], 'Term'],           # ("lambda", [params], body) - Lambda abstraction
    Tuple[str, 'Term', 'Term'],              # ("app", function, argument) - Application
]

Prop = Union[
    Tuple[str, str],                         # ("var", x) or ("const", c) - Atomic proposition
    Tuple[str],                              # ("bottom",) - Falsity
    Tuple[str, str, List[Term]],             # ("pred", name, args) - Predicate
    Tuple[str, 'Prop', 'Prop'],              # ("implies", p, q) | ("and", p, q) | ("or", p, q)
    Tuple[str, 'Prop'],                      # ("not", p) - Negation
    Tuple[str, str, 'Prop'],                 # ("forall", var, body) | ("exists", var, body)
]

Context = List[Tuple[str, Prop]]
Goal = Tuple[Context, Prop]


# === Term Constructors ===

def var(name: str) -> Term:
    """Create a variable term.
    
    Args:
        name: Variable name (typically lowercase)
        
    Returns:
        A term representing the variable
        
    Example:
        >>> x = var("x")
        >>> x
        ('var', 'x')
    """
    return ("var", name)


def const(name: str) -> Term:
    """Create a constant term.
    
    Args:
        name: Constant name (typically uppercase for predicates)
        
    Returns:
        A term representing the constant
        
    Example:
        >>> zero = const("Zero")
        >>> zero
        ('const', 'Zero')
    """
    return ("const", name)


def fun(name: str, args: List[Term]) -> Term:
    """Create a function application term.
    
    Args:
        name: Function name (capitalized)
        args: List of argument terms
        
    Returns:
        A term representing the function application
        
    Example:
        >>> succ = fun("Succ", [var("x")])
        >>> succ
        ('fun', 'Succ', [('var', 'x')])
    """
    return ("fun", name, args)


def lambda_term(params: List[str], body: Term) -> Term:
    """Create a lambda abstraction term.
    
    Args:
        params: List of parameter names
        body: Body term
        
    Returns:
        A term representing the lambda abstraction
        
    Example:
        >>> identity = lambda_term(["x"], var("x"))
        >>> identity
        ('lambda', ['x'], ('var', 'x'))
    """
    return ("lambda", params, body)


def app(func: Term, arg: Term) -> Term:
    """Create a term application.
    
    Args:
        func: Function term
        arg: Argument term
        
    Returns:
        A term representing the application
    """
    return ("app", func, arg)


# === Proposition Constructors ===

def pred(name: str, args: List[Term]) -> Prop:
    """Create a predicate application.
    
    Args:
        name: Predicate name
        args: List of argument terms
        
    Returns:
        A proposition representing the predicate
        
    Example:
        >>> # Create P(x)
        >>> p_of_x = pred("P", [var("x")])
        >>> p_of_x
        ('pred', 'P', [('var', 'x')])
    """
    return ("pred", name, args)


def implies(p: Prop, q: Prop) -> Prop:
    """Create an implication p → q.
    
    Args:
        p: Antecedent proposition
        q: Consequent proposition
        
    Returns:
        A proposition representing the implication
    """
    return ("implies", p, q)


def and_(p: Prop, q: Prop) -> Prop:
    """Create a conjunction p ∧ q.
    
    Args:
        p: Left proposition
        q: Right proposition
        
    Returns:
        A proposition representing the conjunction
    """
    return ("and", p, q)


def or_(p: Prop, q: Prop) -> Prop:
    """Create a disjunction p ∨ q.
    
    Args:
        p: Left proposition
        q: Right proposition
        
    Returns:
        A proposition representing the disjunction
    """
    return ("or", p, q)


def not_(p: Prop) -> Prop:
    """Create a negation ¬p.
    
    Args:
        p: Proposition to negate
        
    Returns:
        A proposition representing the negation
    """
    return ("not", p)


def forall(varname: str, body: Prop) -> Prop:
    """Create a universal quantification ∀x. P(x).
    
    Args:
        varname: Variable name
        body: Body proposition
        
    Returns:
        A proposition representing universal quantification
    """
    return ("forall", varname, body)


def exists(varname: str, body: Prop) -> Prop:
    """Create an existential quantification ∃x. P(x).
    
    Args:
        varname: Variable name
        body: Body proposition
        
    Returns:
        A proposition representing existential quantification
    """
    return ("exists", varname, body)


def bottom() -> Prop:
    """Create the falsity proposition ⊥.
    
    Returns:
        The bottom/false proposition
    """
    return ("bottom",)


def eq(t1: Term, t2: Term) -> Prop:
    """Create an equality proposition t1 = t2.
    
    Args:
        t1: Left term
        t2: Right term
        
    Returns:
        A proposition representing equality
    """
    return ("pred", "=", [t1, t2])


def iff(p: Prop, q: Prop) -> Prop:
    """Create a biconditional p ↔ q (p → q ∧ q → p).
    
    Args:
        p: Left proposition
        q: Right proposition
        
    Returns:
        A proposition representing the biconditional
    """
    return and_(implies(p, q), implies(q, p))


def top() -> Prop:
    """Create the truth proposition ⊤ (¬⊥).
    
    Returns:
        The top/true proposition
    """
    return not_(bottom())


# === Pretty Printing ===

def term_repr(t: Term) -> str:
    """Convert a term to a human-readable string representation.
    
    Args:
        t: Term to convert
        
    Returns:
        String representation
    """
    match t:
        case ("var", x):
            return x
        case ("const", c):
            return c
        case ("fun", name, args):
            args_str = ', '.join(term_repr(a) for a in args)
            return f"{name}({args_str})"
        case ("lambda", params, body):
            return f"(λ{','.join(params)}. {term_repr(body)})"
        case ("app", f, a):
            return f"({term_repr(f)} {term_repr(a)})"
        case _:
            return str(t)


def prop_repr(f: Prop) -> str:
    """Convert a proposition to a human-readable string representation.
    
    Args:
        f: Proposition to convert
        
    Returns:
        String representation with Unicode symbols
    """
    match f:
        case ('not', p):
            return f"¬{prop_repr_paren(p)}"
        case ('and', p, q):
            return f"{prop_repr_paren(p)} ∧ {prop_repr_paren(q)}"
        case ('or', p, q):
            return f"{prop_repr_paren(p)} ∨ {prop_repr_paren(q)}"
        case ('implies', p, q):
            return f"{prop_repr_paren(p)} → {prop_repr(q)}"
        case ('forall', v, body):
            return f"∀{v}. {prop_repr(body)}"
        case ('exists', v, body):
            return f"∃{v}. {prop_repr(body)}"
        case ('bottom',):
            return "⊥"
        case ('pred', name, args):
            if name == "=" and len(args) == 2:
                return f"{term_repr(args[0])} = {term_repr(args[1])}"
            args_str = ', '.join(term_repr(a) for a in args)
            return f"{name}({args_str})" if args else name
        case ('var', x):
            return x
        case ('const', c):
            return c
        case _:
            return str(f)


def prop_repr_paren(f: Prop) -> str:
    """Add parentheses around compound propositions when needed.
    
    Args:
        f: Proposition to convert
        
    Returns:
        String representation with parentheses if needed
    """
    if isinstance(f, tuple) and f[0] in {"and", "or", "implies"}:
        return f"({prop_repr(f)})"
    return prop_repr(f)


def pretty_context(ctx: Context) -> str:
    """Format a context for display.
    
    Args:
        ctx: Context to format
        
    Returns:
        Formatted string representation
    """
    if not ctx:
        return "  Context: ∅"
    maxlen = max(len(name) for name, _ in ctx) if ctx else 0
    lines = [f"  {name.ljust(maxlen)} : {prop_repr(formula)}" for name, formula in ctx]
    return "  Context:\n" + "\n".join(lines)


def pretty_goal(ctx: Context, goal: Prop) -> str:
    """Format a goal for display.
    
    Args:
        ctx: Context
        goal: Goal proposition
        
    Returns:
        Formatted string representation
    """
    return f"{pretty_context(ctx)}\n  Goal: {prop_repr(goal)}"


# === Substitution and Free Variables ===

def fresh_var(existing: Set[str], base: str = "x") -> str:
    """Generate a fresh variable name not in the existing set.
    
    Args:
        existing: Set of already-used variable names
        base: Base name for the fresh variable
        
    Returns:
        A fresh variable name
    """
    i = 1
    while f"{base}{i}" in existing:
        i += 1
    return f"{base}{i}"


def free_vars(prop: Prop) -> Set[str]:
    """Compute the free variables in a proposition.
    
    Args:
        prop: Proposition to analyze
        
    Returns:
        Set of free variable names
    """
    match prop:
        case ('var', x):
            return {x}
        case ('const', _):
            return set()
        case ('pred', _, args):
            return set().union(*(free_vars_term(a) for a in args))
        case ('not', p):
            return free_vars(p)
        case ('and' | 'or' | 'implies', p, q):
            return free_vars(p) | free_vars(q)
        case ('forall' | 'exists', v, body):
            return free_vars(body) - {v}
        case ('bottom',):
            return set()
        case _:
            return set()


def free_vars_term(t: Term) -> Set[str]:
    """Compute the free variables in a term.
    
    Args:
        t: Term to analyze
        
    Returns:
        Set of free variable names
    """
    match t:
        case ('var', x):
            return {x}
        case ('const', _):
            return set()
        case ('fun', _, args):
            return set().union(*(free_vars_term(a) for a in args))
        case ('lambda', params, body):
            return free_vars_term(body) - set(params)
        case ('app', f, a):
            return free_vars_term(f) | free_vars_term(a)
        case _:
            return set()


def substitute_var(prop: Prop, old: str, new: str) -> Prop:
    """Substitute a variable name with another in a proposition.
    
    Args:
        prop: Proposition to transform
        old: Variable name to replace
        new: New variable name
        
    Returns:
        Transformed proposition
    """
    match prop:
        case ('var', x):
            return ('var', new) if x == old else prop
        case ('const', _):
            return prop
        case ('pred', name, args):
            return ('pred', name, [subst_term_var(a, old, new) for a in args])
        case ('not', p):
            return ('not', substitute_var(p, old, new))
        case ('and' | 'or' | 'implies' as tag, p, q):
            return (tag, substitute_var(p, old, new), substitute_var(q, old, new))
        case ('forall' | 'exists' as tag, v, body):
            if v == old:
                return (tag, v, body)
            elif v == new:
                fresh = fresh_var(free_vars(prop) | {new})
                renamed_body = substitute_var(body, v, fresh)
                return (tag, fresh, substitute_var(renamed_body, old, new))
            else:
                return (tag, v, substitute_var(body, old, new))
        case ('bottom',):
            return prop
        case _:
            return prop


def subst_term_var(t: Term, old: str, new: str) -> Term:
    """Substitute a variable name with another in a term.
    
    Args:
        t: Term to transform
        old: Variable name to replace
        new: New variable name
        
    Returns:
        Transformed term
    """
    match t:
        case ('var', x):
            return ('var', new) if x == old else t
        case ('const', _):
            return t
        case ('fun', f, args):
            return ('fun', f, [subst_term_var(a, old, new) for a in args])
        case ('lambda', params, body):
            if old in params:
                return t
            elif new in params:
                fresh_params = [fresh_var(set(params)) if p == new else p for p in params]
                body = substitute_var(body, new, fresh_params[params.index(new)])
                return ('lambda', fresh_params, subst_term_var(body, old, new))
            else:
                return ('lambda', params, subst_term_var(body, old, new))
        case ('app', f, a):
            return ('app', subst_term_var(f, old, new), subst_term_var(a, old, new))
        case _:
            return t


def subst_term(t: Term, varname: str, replacement: Term) -> Term:
    """Substitute a variable with a term in a term.
    
    Args:
        t: Term to transform
        varname: Variable name to replace
        replacement: Replacement term
        
    Returns:
        Transformed term
    """
    match t:
        case ('var', x):
            return replacement if x == varname else t
        case ('const', _):
            return t
        case ('fun', name, args):
            return ('fun', name, [subst_term(a, varname, replacement) for a in args])
        case ('lambda', params, body):
            if varname in params:
                return t
            elif any(p in free_vars_term(replacement) for p in params):
                fresh_params = [fresh_var(free_vars_term(body) | free_vars_term(replacement)) for _ in params]
                renamed_body = body
                for old, new in zip(params, fresh_params):
                    renamed_body = subst_term_var(renamed_body, old, new)
                return ('lambda', fresh_params, subst_term(renamed_body, varname, replacement))
            else:
                return ('lambda', params, subst_term(body, varname, replacement))
        case ('app', f, a):
            return ('app', subst_term(f, varname, replacement), subst_term(a, varname, replacement))
        case _:
            return t


def substitute(prop: Prop, varname: str, term: Term) -> Prop:
    """Substitute a variable with a term in a proposition.
    
    Args:
        prop: Proposition to transform
        varname: Variable name to replace
        term: Replacement term
        
    Returns:
        Transformed proposition
    """
    match prop:
        case ('var', x):
            return prop
        case ('const', _):
            return prop
        case ('pred', name, args):
            return ('pred', name, [subst_term(a, varname, term) for a in args])
        case ('not', p):
            return ('not', substitute(p, varname, term))
        case ('and' | 'or' | 'implies' as tag, p, q):
            return (tag, substitute(p, varname, term), substitute(q, varname, term))
        case ('forall' | 'exists' as tag, v, body):
            if v == varname:
                return (tag, v, body)
            elif v in free_vars_term(term):
                fresh = fresh_var(free_vars(body) | free_vars_term(term))
                renamed = substitute_var(body, v, fresh)
                return (tag, fresh, substitute(renamed, varname, term))
            else:
                return (tag, v, substitute(body, varname, term))
        case ('bottom',):
            return prop
        case _:
            return prop


def beta_reduce(term: Term) -> Term:
    """Perform beta reduction on a term.
    
    Args:
        term: Term to reduce
        
    Returns:
        Reduced term
    """
    match term:
        case ("app", ("lambda", [x], body), arg):
            return beta_reduce(subst_term(body, x, arg))
        case ("app", f, a):
            f_red = beta_reduce(f)
            a_red = beta_reduce(a)
            if f_red != f or a_red != a:
                return beta_reduce(("app", f_red, a_red))
            return ("app", f_red, a_red)
        case ("lambda", params, body):
            body_red = beta_reduce(body)
            if body_red != body:
                return ("lambda", params, body_red)
            return term
        case ("fun", name, args):
            new_args = [beta_reduce(arg) for arg in args]
            if new_args != args:
                return ("fun", name, new_args)
            return term
        case _:
            return term


# === Equality ===

def alpha_eq(p1: Prop, p2: Prop) -> bool:
    """Check if two propositions are alpha-equivalent.
    
    Args:
        p1: First proposition
        p2: Second proposition
        
    Returns:
        True if the propositions are alpha-equivalent
    """
    match p1, p2:
        case ("forall", v1, b1), ("forall", v2, b2):
            fresh = fresh_var(free_vars(b1) | free_vars(b2))
            return alpha_eq(substitute_var(b1, v1, fresh), substitute_var(b2, v2, fresh))
        case ("exists", v1, b1), ("exists", v2, b2):
            fresh = fresh_var(free_vars(b1) | free_vars(b2))
            return alpha_eq(substitute_var(b1, v1, fresh), substitute_var(b2, v2, fresh))
        case (tag1, *args1), (tag2, *args2) if tag1 == tag2:
            return all(alpha_eq(x, y) for x, y in zip(args1, args2))
        case _:
            return p1 == p2


def term_eq(t1: Term, t2: Term) -> bool:
    """Check if two terms are syntactically equal.
    
    Args:
        t1: First term
        t2: Second term
        
    Returns:
        True if the terms are equal
    """
    match t1, t2:
        case ('var', x1), ('var', x2):
            return x1 == x2
        case ('const', c1), ('const', c2):
            return c1 == c2
        case ('fun', n1, args1), ('fun', n2, args2):
            if n1 != n2 or len(args1) != len(args2):
                return False
            return all(term_eq(a1, a2) for a1, a2 in zip(args1, args2))
        case ('lambda', params1, body1), ('lambda', params2, body2):
            if len(params1) != len(params2):
                return False
            fresh_params = [fresh_var(free_vars_term(body1) | free_vars_term(body2) | set(params1) | set(params2)) 
                           for _ in params1]
            body1_renamed = body1
            body2_renamed = body2
            for old1, old2, new in zip(params1, params2, fresh_params):
                body1_renamed = subst_term_var(body1_renamed, old1, new)
                body2_renamed = subst_term_var(body2_renamed, old2, new)
            return term_eq(body1_renamed, body2_renamed)
        case ('app', f1, a1), ('app', f2, a2):
            return term_eq(f1, f2) and term_eq(a1, a2)
        case _:
            return False
