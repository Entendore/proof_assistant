# Interactive Proof Assistant

A formal theorem proving assistant supporting natural deduction with export capabilities to Coq, Isabelle, and Lean.

## Features

- 🎯 **Interactive Proof Construction**: Step-by-step proof building with intuitive tactics
- 🔄 **Undo/Redo Support**: Full history management for proof exploration
- 📤 **Multi-Format Export**: Export proofs to Coq, Isabelle/HOL, and Lean 4
- 🌐 **Streamlit Web Interface**: Modern web-based UI for proof development
- 📝 **Rich Syntax Support**: Unicode and ASCII notation for logical formulas
- 🧪 **Comprehensive Testing**: Full test suite with pytest

## Installation

```bash
# Clone the repository
git clone https://github.com/example/proof_assistant.git
cd proof_assistant

# Install dependencies
pip install -r requirements.txt

# Optional: Install development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Command Line Interface

```python
from proof_assistant.core.parser import parse_formula
from proof_assistant.core.proof_state import ProofState
from proof_assistant.tactics import process_command

# Start a proof
state, _ = process_command(None, "goal P -> P")

# Apply tactics
state, _ = process_command(state, "intro H")
state, _ = process_command(state, "exact H")

# Check if complete
print(state.is_complete())  # True
```

### Streamlit Web Interface

```bash
cd proof_assistant
streamlit run streamlit_app.py
```

## Supported Syntax

### Logical Connectives

| Connective | Symbol | ASCII |
|------------|--------|-------|
| And | ∧ | `and`, `&&` |
| Or | ∨ | `or`, \|\| |
| Implies | → | `->`, `=>` |
| Not | ¬ | `not`, `~` |
| Iff | ↔ | `<=>` |

### Quantifiers

| Quantifier | Symbol | ASCII |
|------------|--------|-------|
| Forall | ∀ | `forall` |
| Exists | ∃ | `exists` |

### Examples

```python
# Propositional logic
"P -> Q"
"P and Q"
"P or Q"
"not P"

# First-order logic
"forall x. P(x)"
"exists x. P(x)"
"forall x. exists y. R(x, y)"

# Predicates
"P(x)"
"Q(x, y)"
"x = y"
```

## Available Tactics

| Tactic | Description |
|--------|-------------|
| `intro [name]` | Introduce implication or universal quantifier |
| `exact H` | Solve goal with exact hypothesis match |
| `assumption` | Solve goal if it matches any hypothesis |
| `split` | Split conjunction into two subgoals |
| `destruct H` | Case analysis on hypothesis |
| `left` | Prove left disjunct of disjunction |
| `right` | Prove right disjunct of disjunction |
| `exists_intro t` | Provide witness for existential |
| `contradiction` | Solve with contradiction |
| `reflexivity` | Solve reflexive equality |
| `apply H` | Apply implication hypothesis |
| `auto` | Automatic proof search |
| `undo` | Undo last step |
| `redo` | Redo undone step |

## Example Proofs

### Identity: P → P

```
goal P -> P
intro H
exact H
```

### And Elimination: P ∧ Q → P

```
goal P and Q -> P
intro H
destruct H
exact H_left
```

### Or Introduction: P → P ∨ Q

```
goal P -> P or Q
intro H
left
exact H
```

### Modus Ponens: (P → Q) → P → Q

```
goal (P -> Q) -> P -> Q
intro H1
intro H2
apply H1
exact H2
```

## Running Tests

```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py -vv

# Run specific test file
python run_tests.py --single test_tactics

# Run with coverage
python run_tests.py --coverage

# Run only last failed tests
python run_tests.py --lf
```

## Project Structure

```
proof_assistant/
├── __init__.py              # Package initialization
├── core/
│   ├── __init__.py
│   ├── terms.py             # Term and proposition definitions
│   ├── proof_state.py       # Proof state management
│   └── parser.py            # Lexer and parser
├── exporters/
│   ├── __init__.py
│   ├── coq.py               # Coq exporter
│   ├── isabelle.py          # Isabelle exporter
│   └── lean.py              # Lean exporter
├── tests/
│   ├── __init__.py
│   ├── test_terms.py        # Term tests
│   ├── test_parser.py       # Parser tests
│   ├── test_tactics.py      # Tactics tests
│   └── test_proof_state.py  # Proof state tests
├── tactics.py               # Proof tactics
├── streamlit_app.py         # Streamlit web interface
├── run_tests.py             # Test runner
├── conftest.py              # Pytest configuration
├── pyproject.toml           # Project configuration
├── requirements.txt         # Dependencies
└── README.md                # This file
```

## API Reference

### Core Module

```python
from proof_assistant.core.terms import (
    var, const, fun, pred,           # Term constructors
    implies, and_, or_, not_,        # Connective constructors
    forall, exists, bottom, eq,      # Quantifier constructors
    prop_repr, term_repr,            # Pretty printing
    alpha_eq,                        # Alpha equality
)

from proof_assistant.core.parser import (
    parse_formula,                   # Parse formula string
    parse_term,                      # Parse term string
)

from proof_assistant.core.proof_state import (
    ProofState,                      # Proof state manager
    ProofTree,                       # Proof tree recorder
)
```

### Tactics Module

```python
from proof_assistant.tactics import (
    tactic_intro,                    # Introduction tactic
    tactic_exact,                    # Exact match tactic
    tactic_assumption,               # Assumption tactic
    tactic_split,                    # Split tactic
    tactic_destruct,                 # Destruct tactic
    process_command,                 # Command processor
)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
