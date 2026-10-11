"""
Unit Tests for Tactics Module
=============================

Tests for proof tactics and command processing.
"""

import pytest
from proof_assistant.core.terms import (
    var, const, fun, pred,
    implies, and_, or_, not_,
    forall, exists, bottom, eq,
    prop_repr, alpha_eq
)
from proof_assistant.core.proof_state import ProofState, ProofTree
from proof_assistant.core.parser import parse_formula
from proof_assistant.tactics import (
    TacticError,
    tactic_intro, tactic_exact, tactic_assumption,
    tactic_split, tactic_destruct, tactic_left, tactic_right,
    tactic_forall_elim, tactic_exists_intro,
    tactic_contradiction, tactic_reflexivity,
    tactic_not_intro, tactic_not_elim, tactic_apply, tactic_auto,
    tactic_hint, process_command, explain_tactic,
)


class TestTacticIntro:
    """Tests for the intro tactic."""
    
    def test_intro_implication(self):
        """Test intro on implication goal."""
        state = ProofState([([], parse_formula("P -> Q"))])
        new_state = tactic_intro(state, "H")
        
        assert not new_state.is_complete()
        current = new_state.current()
        assert current is not None
        ctx, goal = current
        
        # Context should contain P as H
        assert ("H", ("pred", "P", [])) in ctx
        # Goal should be Q
        assert alpha_eq(goal, ("pred", "Q", []))
    
    def test_intro_forall(self):
        """Test intro on universal quantification goal."""
        state = ProofState([([], parse_formula("forall x. P(x)"))])
        new_state = tactic_intro(state)
        
        assert not new_state.is_complete()
        current = new_state.current()
        ctx, goal = current
        
        # Goal should be P applied to some fresh variable
        assert goal[0] == "pred"
        assert goal[1] == "P"
    
    def test_intro_wrong_goal(self):
        """Test intro on wrong goal type."""
        state = ProofState([([], parse_formula("P and Q"))])
        with pytest.raises(TacticError):
            tactic_intro(state)


class TestTacticExact:
    """Tests for the exact tactic."""
    
    def test_exact_hypothesis(self):
        """Test exact with hypothesis name."""
        state = ProofState([([("H", ("pred", "P", []))], ("pred", "P", []))])
        new_state = tactic_exact(state, "H")
        
        assert new_state.is_complete()
    
    def test_exact_wrong_hypothesis(self):
        """Test exact with wrong hypothesis."""
        state = ProofState([([("H", ("pred", "P", []))], ("pred", "Q", []))])
        with pytest.raises(TacticError):
            tactic_exact(state, "H")
    
    def test_exact_missing_hypothesis(self):
        """Test exact with missing hypothesis."""
        state = ProofState([([], ("pred", "P", []))])
        with pytest.raises(TacticError):
            tactic_exact(state, "H")


class TestTacticAssumption:
    """Tests for the assumption tactic."""
    
    def test_assumption_matches(self):
        """Test assumption when hypothesis matches."""
        state = ProofState([([("H", ("pred", "P", []))], ("pred", "P", []))])
        new_state = tactic_assumption(state)
        
        assert new_state.is_complete()
    
    def test_assumption_no_match(self):
        """Test assumption when no match."""
        state = ProofState([([("H", ("pred", "P", []))], ("pred", "Q", []))])
        with pytest.raises(TacticError):
            tactic_assumption(state)


class TestTacticSplit:
    """Tests for the split tactic."""
    
    def test_split_conjunction(self):
        """Test split on conjunction goal."""
        state = ProofState([([], parse_formula("P and Q"))])
        new_state = tactic_split(state)
        
        assert len(new_state.goals) == 2
        
    def test_split_wrong_goal(self):
        """Test split on wrong goal type."""
        state = ProofState([([], parse_formula("P -> Q"))])
        with pytest.raises(TacticError):
            tactic_split(state)


class TestTacticDestruct:
    """Tests for the destruct tactic."""
    
    def test_destruct_conjunction(self):
        """Test destruct on conjunction hypothesis."""
        state = ProofState([([("H", ("and", ("pred", "P", []), ("pred", "Q", [])))],
                            ("pred", "R", []))])
        new_state = tactic_destruct(state, "H")
        
        current = new_state.current()
        ctx, _ = current
        
        # Should have H_left and H_right in context
        assert any(name == "H_left" for name, _ in ctx)
        assert any(name == "H_right" for name, _ in ctx)
    
    def test_destruct_disjunction(self):
        """Test destruct on disjunction hypothesis."""
        state = ProofState([([("H", ("or", ("pred", "P", []), ("pred", "Q", [])))],
                            ("pred", "R", []))])
        new_state = tactic_destruct(state, "H")
        
        # Should create two subgoals
        assert len(new_state.goals) == 2
    
    def test_destruct_missing(self):
        """Test destruct on missing hypothesis."""
        state = ProofState([([], ("pred", "P", []))])
        with pytest.raises(TacticError):
            tactic_destruct(state, "H")


class TestTacticLeftRight:
    """Tests for left and right tactics."""
    
    def test_left_disjunction(self):
        """Test left on disjunction goal."""
        state = ProofState([([], parse_formula("P or Q"))])
        new_state = tactic_left(state)
        
        current = new_state.current()
        _, goal = current
        assert alpha_eq(goal, ("pred", "P", []))
    
    def test_right_disjunction(self):
        """Test right on disjunction goal."""
        state = ProofState([([], parse_formula("P or Q"))])
        new_state = tactic_right(state)
        
        current = new_state.current()
        _, goal = current
        assert alpha_eq(goal, ("pred", "Q", []))
    
    def test_left_wrong_goal(self):
        """Test left on wrong goal type."""
        state = ProofState([([], parse_formula("P and Q"))])
        with pytest.raises(TacticError):
            tactic_left(state)


class TestTacticExistsIntro:
    """Tests for exists_intro tactic."""
    
    def test_exists_intro(self):
        """Test exists introduction."""
        state = ProofState([([], parse_formula("exists x. P(x)"))])
        new_state = tactic_exists_intro(state, "y")
        
        current = new_state.current()
        _, goal = current
        
        # Goal should now be P(y)
        assert alpha_eq(goal, ("pred", "P", [("var", "y")]))
    
    def test_exists_intro_wrong_goal(self):
        """Test exists_intro on wrong goal type."""
        state = ProofState([([], parse_formula("P"))])
        with pytest.raises(TacticError):
            tactic_exists_intro(state, "y")


class TestTacticContradiction:
    """Tests for the contradiction tactic."""
    
    def test_contradiction_bottom(self):
        """Test contradiction with bottom in context."""
        state = ProofState([([("H", ("bottom",))], ("pred", "P", []))])
        new_state = tactic_contradiction(state)
        
        assert new_state.is_complete()
    
    def test_contradiction_p_and_not_p(self):
        """Test contradiction with P and not P."""
        state = ProofState([([
            ("H1", ("pred", "P", [])),
            ("H2", ("not", ("pred", "P", [])))
        ], ("pred", "Q", []))])
        new_state = tactic_contradiction(state)
        
        assert new_state.is_complete()
    
    def test_contradiction_none(self):
        """Test contradiction when none found."""
        state = ProofState([([("H", ("pred", "P", []))], ("pred", "Q", []))])
        with pytest.raises(TacticError):
            tactic_contradiction(state)


class TestTacticReflexivity:
    """Tests for the reflexivity tactic."""
    
    def test_reflexivity_same_term(self):
        """Test reflexivity on t = t."""
        state = ProofState([([], parse_formula("x = x"))])
        new_state = tactic_reflexivity(state)
        
        assert new_state.is_complete()
    
    def test_reflexivity_different_terms(self):
        """Test reflexivity on different terms."""
        state = ProofState([([], parse_formula("x = y"))])
        with pytest.raises(TacticError):
            tactic_reflexivity(state)


class TestTacticNotIntro:
    """Tests for not_intro tactic."""
    
    def test_not_intro(self):
        """Test not_intro on negation goal."""
        state = ProofState([([], parse_formula("not P"))])
        new_state = tactic_not_intro(state, "H")
        
        current = new_state.current()
        ctx, goal = current
        
        # Should have P in context
        assert ("H", ("pred", "P", [])) in ctx
        # Goal should be bottom
        assert goal == ("bottom",)


class TestTacticApply:
    """Tests for apply tactic."""
    
    def test_apply_implication(self):
        """Test apply on implication hypothesis."""
        state = ProofState([([
            ("H", ("implies", ("pred", "P", []), ("pred", "Q", [])))
        ], ("pred", "Q", []))])
        new_state = tactic_apply(state, "H")
        
        current = new_state.current()
        _, goal = current
        
        # Goal should now be P
        assert alpha_eq(goal, ("pred", "P", []))


class TestTacticAuto:
    """Tests for auto tactic."""
    
    def test_auto_assumption(self):
        """Test auto with matching assumption."""
        state = ProofState([([("H", ("pred", "P", []))], ("pred", "P", []))])
        new_state = tactic_auto(state)
        
        assert new_state.is_complete()
    
    def test_auto_contradiction(self):
        """Test auto with contradiction."""
        state = ProofState([([("H", ("bottom",))], ("pred", "P", []))])
        new_state = tactic_auto(state)
        
        assert new_state.is_complete()


class TestProcessCommand:
    """Tests for command processing."""
    
    def test_process_goal(self):
        """Test processing goal command."""
        state, msg = process_command(None, "goal P -> Q")
        
        assert state is not None
        assert not state.is_complete()
    
    def test_process_intro(self):
        """Test processing intro command."""
        state, _ = process_command(None, "goal P -> Q")
        state, msg = process_command(state, "intro H")
        
        assert state is not None
    
    def test_process_exact(self):
        """Test processing exact command."""
        state, _ = process_command(None, "goal P -> P")
        state, _ = process_command(state, "intro H")
        state, msg = process_command(state, "exact H")
        
        assert state.is_complete()
    
    def test_process_help(self):
        """Test processing help command."""
        state, msg = process_command(None, "help")
        
        assert "Available commands" in msg
    
    def test_process_undo(self):
        """Test processing undo command."""
        state, _ = process_command(None, "goal P -> Q")
        state, _ = process_command(state, "intro H")
        state, msg = process_command(state, "undo")
        
        # Should be back to original goal
        assert len(state.goals) == 1
    
    def test_process_unknown(self):
        """Test processing unknown command."""
        # Set a goal first so we have an active proof
        state, _ = process_command(None, "goal P")
        state, msg = process_command(state, "unknown")
        
        assert "Unknown command" in msg


class TestExplainTactic:
    """Tests for explain_tactic function."""
    
    def test_explain_intro(self):
        """Test explaining intro tactic."""
        explanation = explain_tactic("intro")
        assert "implication" in explanation.lower()
    
    def test_explain_split(self):
        """Test explaining split tactic."""
        explanation = explain_tactic("split")
        assert "conjunction" in explanation.lower()
    
    def test_explain_unknown(self):
        """Test explaining unknown tactic."""
        explanation = explain_tactic("unknown")
        assert "No explanation" in explanation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
