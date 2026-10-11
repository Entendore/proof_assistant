"""
Unit Tests for Proof State Module
=================================

Tests for proof state management, undo/redo, and export.
"""

import pytest
import tempfile
import os
from pathlib import Path

from proof_assistant.core.terms import (
    var, pred, implies, and_, forall,
    prop_repr
)
from proof_assistant.core.proof_state import ProofState, ProofTree, ProofStep, ProofSystem
from proof_assistant.core.parser import parse_formula
from proof_assistant.tactics import tactic_intro, tactic_split


class TestProofStep:
    """Tests for ProofStep dataclass."""
    
    def test_proof_step_creation(self):
        """Test creating a proof step."""
        step = ProofStep(
            tactic_name="intro",
            arguments=["H"],
            subgoals_before=[([], parse_formula("P -> Q"))],
            subgoals_after=[([("H", ("pred", "P", []))], ("pred", "Q", []))]
        )
        
        assert step.tactic_name == "intro"
        assert step.arguments == ["H"]
        assert step.success is True
        assert step.error_message is None
    
    def test_proof_step_with_error(self):
        """Test creating a failed proof step."""
        step = ProofStep(
            tactic_name="intro",
            arguments=[],
            subgoals_before=[([], parse_formula("P"))],
            subgoals_after=[([], parse_formula("P"))],
            success=False,
            error_message="Goal is not implication"
        )
        
        assert step.success is False
        assert step.error_message == "Goal is not implication"


class TestProofTree:
    """Tests for ProofTree class."""
    
    def test_proof_tree_creation(self):
        """Test creating a proof tree."""
        tree = ProofTree()
        
        assert tree.steps == []
        assert tree.initial_goal is None
        assert tree.theorem_name == "theorem"
    
    def test_set_initial_goal(self):
        """Test setting initial goal."""
        tree = ProofTree()
        goal = ([], parse_formula("P -> P"))
        tree.set_initial_goal(goal, "identity")
        
        assert tree.theorem_name == "identity"
        assert tree.initial_goal is not None
    
    def test_record_step(self):
        """Test recording a proof step."""
        tree = ProofTree()
        state_before = ProofState([([], parse_formula("P -> P"))], tree)
        state_after = ProofState([([("H", ("pred", "P", []))], ("pred", "P", []))], tree)
        
        tree.record_step("intro", ["H"], state_before, state_after)
        
        assert len(tree.steps) == 1
        assert tree.steps[0].tactic_name == "intro"
    
    def test_pretty_print(self):
        """Test pretty printing proof tree."""
        tree = ProofTree()
        
        # Empty tree
        output = tree.pretty_print()
        assert "No proof steps" in output
        
        # With steps
        state_before = ProofState([([], parse_formula("P -> P"))], tree)
        state_after = ProofState([([("H", ("pred", "P", []))], ("pred", "P", []))], tree)
        tree.record_step("intro", ["H"], state_before, state_after)
        
        output = tree.pretty_print()
        assert "intro" in output


class TestProofTreeExport:
    """Tests for proof tree export functionality."""
    
    def test_export_coq(self):
        """Test exporting to Coq."""
        tree = ProofTree()
        goal = ([], parse_formula("P -> P"))
        tree.set_initial_goal(goal, "identity")
        
        state_before = ProofState([([], parse_formula("P -> P"))], tree)
        state_after = ProofState([([("H", ("pred", "P", []))], ("pred", "P", []))], tree)
        tree.record_step("intro", ["H"], state_before, state_after)
        tree.record_step("exact", ["H"], state_after, ProofState([], tree))
        
        coq_code = tree.export_coq()
        
        assert "Theorem" in coq_code
        assert "Proof" in coq_code
        assert "Qed" in coq_code
    
    def test_export_isabelle(self):
        """Test exporting to Isabelle."""
        tree = ProofTree()
        goal = ([], parse_formula("P -> P"))
        tree.set_initial_goal(goal, "identity")
        
        state_before = ProofState([([], parse_formula("P -> P"))], tree)
        state_after = ProofState([([("H", ("pred", "P", []))], ("pred", "P", []))], tree)
        tree.record_step("intro", ["H"], state_before, state_after)
        tree.record_step("exact", ["H"], state_after, ProofState([], tree))
        
        isabelle_code = tree.export_isabelle()
        
        assert "theorem" in isabelle_code
        assert "proof" in isabelle_code
    
    def test_export_lean(self):
        """Test exporting to Lean."""
        tree = ProofTree()
        goal = ([], parse_formula("P -> P"))
        tree.set_initial_goal(goal, "identity")
        
        state_before = ProofState([([], parse_formula("P -> P"))], tree)
        state_after = ProofState([([("H", ("pred", "P", []))], ("pred", "P", []))], tree)
        tree.record_step("intro", ["H"], state_before, state_after)
        tree.record_step("exact", ["H"], state_after, ProofState([], tree))
        
        lean_code = tree.export_lean()
        
        assert "theorem" in lean_code
        assert "by" in lean_code
    
    def test_export_all(self):
        """Test exporting to all systems."""
        tree = ProofTree()
        goal = ([], parse_formula("P -> P"))
        tree.set_initial_goal(goal, "identity")
        
        state_before = ProofState([([], parse_formula("P -> P"))], tree)
        state_after = ProofState([([("H", ("pred", "P", []))], ("pred", "P", []))], tree)
        tree.record_step("intro", ["H"], state_before, state_after)
        tree.record_step("exact", ["H"], state_after, ProofState([], tree))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exports = tree.export_all(tmpdir)
            
            assert "coq" in exports
            assert "isabelle" in exports
            assert "lean" in exports
            
            # Check files were created
            assert os.path.exists(os.path.join(tmpdir, "identity.v"))
            assert os.path.exists(os.path.join(tmpdir, "identity.thy"))
            assert os.path.exists(os.path.join(tmpdir, "identity.lean"))


class TestProofTreeSaveLoad:
    """Tests for saving and loading proof state."""
    
    def test_save_and_load(self):
        """Test saving and loading proof state."""
        tree = ProofTree()
        goal = ([], parse_formula("P -> P"))
        tree.set_initial_goal(goal, "identity")
        
        state_before = ProofState([([], parse_formula("P -> P"))], tree)
        state_after = ProofState([([("H", ("pred", "P", []))], ("pred", "P", []))], tree)
        tree.record_step("intro", ["H"], state_before, state_after)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "proof_state.json")
            tree.save_proof_state(filepath)
            
            # Load into new tree
            new_tree = ProofTree()
            new_tree.load_proof_state(filepath)
            
            assert new_tree.theorem_name == "identity"
            assert len(new_tree.steps) == 1


class TestProofState:
    """Tests for ProofState class."""
    
    def test_proof_state_creation(self):
        """Test creating proof state."""
        state = ProofState([([], parse_formula("P -> Q"))])
        
        assert not state.is_complete()
        assert state.current() is not None
    
    def test_proof_state_empty(self):
        """Test empty proof state."""
        state = ProofState([])
        
        assert state.is_complete()
        assert state.current() is None
    
    def test_add_subgoals(self):
        """Test adding subgoals."""
        state = ProofState([([], parse_formula("P and Q"))])
        new_state = state.add_subgoals([
            ([], ("pred", "P", [])),
            ([], ("pred", "Q", []))
        ])
        
        assert len(new_state.goals) == 2
    
    def test_str_representation(self):
        """Test string representation."""
        state = ProofState([([], parse_formula("P -> Q"))])
        s = str(state)
        
        assert "Goal" in s
        assert "P → Q" in s
    
    def test_str_complete(self):
        """Test string representation of complete proof."""
        state = ProofState([])
        s = str(state)
        
        assert "complete" in s


class TestProofStateUndoRedo:
    """Tests for undo/redo functionality."""
    
    def test_undo_via_add_subgoals(self):
        """Test undo functionality via add_subgoals."""
        state = ProofState([([], parse_formula("P -> Q"))])
        # add_subgoals saves state to history before returning new state
        new_state = state.add_subgoals([([("H", ("pred", "P", []))], ("pred", "Q", []))])
        
        # The history is in the original state, but new_state has reference to it
        # Calling undo on new_state should work because it has the history from state
        undone = new_state.undo()
        assert undone is not None
        assert len(undone.goals) == 1
        assert undone.current()[0] == []  # Empty context
    
    def test_undo_empty(self):
        """Test undo with no history."""
        state = ProofState([([], parse_formula("P -> Q"))])
        result = state.undo()
        
        assert result is None
    
    def test_redo(self):
        """Test redo functionality."""
        state = ProofState([([], parse_formula("P -> Q"))])
        new_state = state.add_subgoals([([("H", ("pred", "P", []))], ("pred", "Q", []))])
        
        # Undo from new_state
        undone = new_state.undo()
        assert undone is not None
        assert len(undone.goals) == 1
        assert undone.current()[0] == []  # Empty context
        
        # Redo
        redone = undone.redo()
        assert redone is not None
        assert len(redone.goals) == 1
        assert len(redone.current()[0]) == 1  # Has hypothesis
    
    def test_redo_empty(self):
        """Test redo with no future."""
        state = ProofState([([], parse_formula("P -> Q"))])
        result = state.redo()
        
        assert result is None


class TestProofStateToDict:
    """Tests for to_dict functionality."""
    
    def test_to_dict(self):
        """Test converting proof state to dictionary."""
        tree = ProofTree()
        tree.theorem_name = "test_theorem"
        state = ProofState([([], parse_formula("P -> Q"))], tree)
        
        d = state.to_dict()
        
        assert "goals" in d
        assert "is_complete" in d
        assert "theorem_name" in d
        assert d["theorem_name"] == "test_theorem"
        assert d["is_complete"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
