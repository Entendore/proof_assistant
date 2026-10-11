"""
Pytest Configuration and Fixtures
=================================

This file provides shared fixtures and configuration for all tests.
"""

import pytest
import tempfile
import os
from pathlib import Path

# Add the parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def simple_goal():
    """Provide a simple goal for testing."""
    from proof_assistant.core.terms import pred
    return ([], pred("P", []))


@pytest.fixture
def implication_goal():
    """Provide an implication goal for testing."""
    from proof_assistant.core.parser import parse_formula
    return ([], parse_formula("P -> Q"))


@pytest.fixture
def conjunction_goal():
    """Provide a conjunction goal for testing."""
    from proof_assistant.core.parser import parse_formula
    return ([], parse_formula("P and Q"))


@pytest.fixture
def disjunction_goal():
    """Provide a disjunction goal for testing."""
    from proof_assistant.core.parser import parse_formula
    return ([], parse_formula("P or Q"))


@pytest.fixture
def forall_goal():
    """Provide a universally quantified goal for testing."""
    from proof_assistant.core.parser import parse_formula
    return ([], parse_formula("forall x. P(x)"))


@pytest.fixture
def exists_goal():
    """Provide an existentially quantified goal for testing."""
    from proof_assistant.core.parser import parse_formula
    return ([], parse_formula("exists x. P(x)"))


@pytest.fixture
def proof_state_with_hypothesis():
    """Provide a proof state with a hypothesis."""
    from proof_assistant.core.proof_state import ProofState
    from proof_assistant.core.terms import pred
    
    ctx = [("H", pred("P", []))]
    goal = pred("P", [])
    return ProofState([(ctx, goal)])


@pytest.fixture
def complete_proof_state():
    """Provide a complete (empty) proof state."""
    from proof_assistant.core.proof_state import ProofState
    return ProofState([])


@pytest.fixture
def proof_tree_with_steps():
    """Provide a proof tree with some steps."""
    from proof_assistant.core.proof_state import ProofTree, ProofState
    from proof_assistant.core.parser import parse_formula
    
    tree = ProofTree()
    goal = ([], parse_formula("P -> P"))
    tree.set_initial_goal(goal, "identity")
    
    state_before = ProofState([goal], tree)
    state_after = ProofState([([("H", ("pred", "P", []))], ("pred", "P", []))], tree)
    tree.record_step("intro", ["H"], state_before, state_after)
    tree.record_step("exact", ["H"], state_after, ProofState([], tree))
    
    return tree


# ============================================================================
# Configuration
# ============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Add marker to slow tests automatically."""
    for item in items:
        if "stress" in item.nodeid or "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.slow)
