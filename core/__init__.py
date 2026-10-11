"""
Core module for the proof assistant.

Contains:
    - Terms: Term and proposition type definitions
    - Proof state management
    - Parser and lexer
    - Substitution and free variables
"""

from .terms import *
from .proof_state import ProofState, ProofTree, ProofStep
from .parser import parse_formula, parse_term, lex

__all__ = [
    'ProofState', 'ProofTree', 'ProofStep',
    'parse_formula', 'parse_term', 'lex',
]
