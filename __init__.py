"""
Interactive Proof Assistant
===========================

A formal theorem proving assistant with support for natural deduction,
export to Coq/Isabelle/Lean, and a Streamlit web interface.

Modules:
    core: Core data structures and proof state management
    tactics: Proof tactics implementation
    parser: Lexer and parser for logical formulas
    exporters: Export to various theorem prover formats
    utils: Utility functions and helpers
"""

__version__ = "2.0.0"
__author__ = "Proof Assistant Team"

from .core.terms import (
    Term, Prop, Context, Goal,
    var, const, fun, pred,
    implies, and_, or_, not_,
    forall, exists, bottom, eq, iff
)

from .core.proof_state import ProofState, ProofTree, ProofStep
from .core.parser import parse_formula, parse_term

__all__ = [
    # Types
    'Term', 'Prop', 'Context', 'Goal',
    # Constructors
    'var', 'const', 'fun', 'pred',
    'implies', 'and_', 'or_', 'not_',
    'forall', 'exists', 'bottom', 'eq', 'iff',
    # Proof state
    'ProofState', 'ProofTree', 'ProofStep',
    # Parser
    'parse_formula', 'parse_term',
]
