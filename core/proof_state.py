"""
Proof State Management
======================

This module manages the proof state, including:
    - Proof tree and step recording
    - Goal stack management
    - Undo/redo functionality
    - Export capabilities

Classes:
    ProofStep: Records a single proof step
    ProofTree: Manages the complete proof tree
    ProofState: Current state of an interactive proof
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from copy import deepcopy
from enum import Enum

from .terms import (
    Prop, Context, Goal,
    prop_repr, pretty_goal, free_vars, free_vars_term,
    fresh_var, substitute_var, subst_term_var, term_eq
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("ProofAssistant")


class ProofSystem(Enum):
    """Supported theorem prover systems for export."""
    COQ = "coq"
    ISABELLE = "isabelle"
    LEAN = "lean"


@dataclass
class ProofStep:
    """Records a single proof step.
    
    Attributes:
        tactic_name: Name of the tactic applied
        arguments: Arguments passed to the tactic
        subgoals_before: Goals before applying the tactic
        subgoals_after: Goals after applying the tactic
        timestamp: When the step was recorded
        success: Whether the tactic succeeded
        error_message: Error message if the tactic failed
    """
    tactic_name: str
    arguments: List[Any]
    subgoals_before: List[Goal]
    subgoals_after: List[Goal]
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None


ProofStateSnapshot = Tuple[List[Goal], List['ProofStep']]


class ProofTree:
    """Manages the complete proof tree.
    
    The proof tree records all steps in a proof and provides
    export functionality to various theorem prover formats.
    
    Attributes:
        steps: List of proof steps
        initial_goal: The original goal to prove
        theorem_name: Name of the theorem
        export_options: Configuration for each export system
    """
    
    def __init__(self):
        self.steps: List[ProofStep] = []
        self.initial_goal: Optional[Goal] = None
        self.theorem_name: str = "theorem"
        self.export_options: Dict[ProofSystem, Dict] = {
            ProofSystem.COQ: {
                "use_ssr": False,
                "indent": 2,
                "include_imports": True
            },
            ProofSystem.ISABELLE: {
                "theory_name": "My_Theory",
                "indent": 2,
                "include_headers": True
            },
            ProofSystem.LEAN: {
                "use_structured_proofs": True,
                "indent": 2,
                "include_imports": True
            }
        }
    
    def record_step(self, tactic_name: str, arguments: List[Any],
                   state_before: 'ProofState', state_after: 'ProofState',
                   success: bool = True, error_message: Optional[str] = None):
        """Record a proof step.
        
        Args:
            tactic_name: Name of the tactic
            arguments: Arguments to the tactic
            state_before: State before applying the tactic
            state_after: State after applying the tactic
            success: Whether the tactic succeeded
            error_message: Error message if failed
        """
        step = ProofStep(
            tactic_name=tactic_name,
            arguments=arguments,
            subgoals_before=deepcopy(state_before.goals),
            subgoals_after=deepcopy(state_after.goals),
            success=success,
            error_message=error_message
        )
        self.steps.append(step)
        logger.info(f"Recorded step: {tactic_name} with {len(arguments)} args. "
                   f"Goals: {len(state_before.goals)} → {len(state_after.goals)}")
    
    def set_initial_goal(self, goal: Goal, theorem_name: str = "theorem"):
        """Set the initial goal for the proof.
        
        Args:
            goal: The initial goal (context, proposition)
            theorem_name: Name of the theorem
        """
        self.initial_goal = deepcopy(goal)
        self.theorem_name = theorem_name
    
    def pretty_print(self) -> str:
        """Generate a pretty-printed representation of the proof.
        
        Returns:
            Formatted string of all proof steps
        """
        if not self.steps:
            return "No proof steps recorded"
        
        lines = ["Proof steps:"]
        for i, step in enumerate(self.steps):
            status = "✓" if step.success else "✗"
            lines.append(f"{i+1}. [{status}] {step.tactic_name} {step.arguments}")
            lines.append(f"   Goals: {len(step.subgoals_before)} → {len(step.subgoals_after)}")
            if not step.success and step.error_message:
                lines.append(f"   Error: {step.error_message}")
        
        return "\n".join(lines)
    
    def export_coq(self) -> str:
        """Export the proof to Coq syntax.
        
        Returns:
            Coq proof script
        """
        from ..exporters.coq import export_to_coq
        return export_to_coq(self)
    
    def export_isabelle(self) -> str:
        """Export the proof to Isabelle/HOL syntax.
        
        Returns:
            Isabelle theory file content
        """
        from ..exporters.isabelle import export_to_isabelle
        return export_to_isabelle(self)
    
    def export_lean(self) -> str:
        """Export the proof to Lean 4 syntax.
        
        Returns:
            Lean proof script
        """
        from ..exporters.lean import export_to_lean
        return export_to_lean(self)
    
    def export_all(self, directory: str = ".") -> Dict[str, str]:
        """Export to all supported theorem provers.
        
        Args:
            directory: Directory to save exported files
            
        Returns:
            Dictionary mapping system names to exported code
        """
        exports = {}
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Export to Coq
        coq_code = self.export_coq()
        exports["coq"] = coq_code
        if coq_code:
            coq_path = Path(directory) / f"{self.theorem_name}.v"
            with open(coq_path, "w") as f:
                f.write(coq_code)
            logger.info(f"Coq export saved to {coq_path}")
        
        # Export to Isabelle
        isabelle_code = self.export_isabelle()
        exports["isabelle"] = isabelle_code
        if isabelle_code:
            isabelle_path = Path(directory) / f"{self.theorem_name}.thy"
            with open(isabelle_path, "w") as f:
                f.write(isabelle_code)
            logger.info(f"Isabelle export saved to {isabelle_path}")
        
        # Export to Lean
        lean_code = self.export_lean()
        exports["lean"] = lean_code
        if lean_code:
            lean_path = Path(directory) / f"{self.theorem_name}.lean"
            with open(lean_path, "w") as f:
                f.write(lean_code)
            logger.info(f"Lean export saved to {lean_path}")
        
        return exports
    
    def save_proof_state(self, filename: str):
        """Save the proof state to a JSON file.
        
        Args:
            filename: Path to save the file
        """
        def serialize_goal(goal: Goal) -> Dict:
            ctx, prop = goal
            return {
                "context": [(name, prop) for name, prop in ctx],
                "goal": prop
            }
        
        state = {
            "theorem_name": self.theorem_name,
            "initial_goal": serialize_goal(self.initial_goal) if self.initial_goal else None,
            "steps": [
                {
                    "tactic_name": step.tactic_name,
                    "arguments": step.arguments,
                    "success": step.success,
                    "error_message": step.error_message,
                    "timestamp": step.timestamp.isoformat()
                }
                for step in self.steps
            ],
            "export_options": {str(k.value): v for k, v in self.export_options.items()}
        }
        
        with open(filename, "w") as f:
            json.dump(state, f, indent=2)
        logger.info(f"Proof state saved to {filename}")
    
    def load_proof_state(self, filename: str):
        """Load the proof state from a JSON file.
        
        Args:
            filename: Path to the saved file
        """
        with open(filename, "r") as f:
            state = json.load(f)
        
        self.theorem_name = state["theorem_name"]
        
        # Reconstruct initial goal
        if state["initial_goal"]:
            goal_data = state["initial_goal"]
            ctx = [(name, prop) for name, prop in goal_data["context"]]
            goal = goal_data["goal"]
            self.initial_goal = (ctx, goal)
        
        # Reconstruct steps
        self.steps = []
        for step_data in state["steps"]:
            step = ProofStep(
                tactic_name=step_data["tactic_name"],
                arguments=step_data["arguments"],
                subgoals_before=[],
                subgoals_after=[],
                success=step_data["success"],
                error_message=step_data["error_message"],
                timestamp=datetime.fromisoformat(step_data["timestamp"])
            )
            self.steps.append(step)
        
        # Restore export options
        for system_str, options in state["export_options"].items():
            try:
                system = next(s for s in ProofSystem if s.value == system_str)
                self.export_options[system] = options
            except StopIteration:
                logger.warning(f"Unknown proof system in saved state: {system_str}")
        
        logger.info(f"Proof state loaded from {filename}")


class ProofState:
    """Manages the current state of an interactive proof.
    
    The proof state maintains a stack of goals and tracks the
    proof tree. It supports undo/redo operations.
    
    Attributes:
        goals: Stack of remaining goals to prove
        proof_tree: The proof tree being constructed
        history: Stack of previous states for undo
        future: Stack of undone states for redo
    """
    
    def __init__(self, goals: List[Goal] = None, proof_tree: Optional[ProofTree] = None):
        self.goals = goals if goals is not None else []
        self.proof_tree = proof_tree or ProofTree()
        self.history: List[ProofStateSnapshot] = []
        self.future: List[ProofStateSnapshot] = []
    
    def current(self) -> Optional[Goal]:
        """Get the current goal.
        
        Returns:
            The current goal or None if proof is complete
        """
        return self.goals[-1] if self.goals else None
    
    def is_complete(self) -> bool:
        """Check if the proof is complete.
        
        Returns:
            True if there are no remaining goals
        """
        return not self.goals
    
    def add_subgoals(self, new_goals: List[Goal]) -> 'ProofState':
        """Add subgoals to the proof state.
        
        Replaces the current goal with new subgoals.
        
        Args:
            new_goals: New goals to add
            
        Returns:
            New proof state with updated goals
        """
        # Save current state to history
        self.history.append((deepcopy(self.goals), deepcopy(self.proof_tree.steps)))
        self.future.clear()
        
        # Create new state with updated goals and copy of history
        new_state = ProofState(self.goals[:-1] + new_goals, self.proof_tree)
        new_state.history = self.history.copy()
        new_state.future = self.future.copy()
        return new_state
    
    def undo(self) -> Optional['ProofState']:
        """Undo the last proof step.
        
        Returns:
            Previous proof state or None if no history
        """
        if not self.history:
            logger.warning("No actions to undo")
            return None
        
        self.future.append((deepcopy(self.goals), deepcopy(self.proof_tree.steps)))
        previous_goals, previous_steps = self.history.pop()
        new_state = ProofState(deepcopy(previous_goals), deepcopy(self.proof_tree))
        new_state.proof_tree.steps = deepcopy(previous_steps)
        new_state.history = self.history.copy()
        new_state.future = self.future.copy()
        logger.info("Undo successful")
        return new_state
    
    def redo(self) -> Optional['ProofState']:
        """Redo the last undone proof step.
        
        Returns:
            Next proof state or None if no future
        """
        if not self.future:
            logger.warning("No actions to redo")
            return None
        
        self.history.append((deepcopy(self.goals), deepcopy(self.proof_tree.steps)))
        next_goals, next_steps = self.future.pop()
        new_state = ProofState(deepcopy(next_goals), deepcopy(self.proof_tree))
        new_state.proof_tree.steps = deepcopy(next_steps)
        new_state.history = self.history.copy()
        new_state.future = self.future.copy()
        logger.info("Redo successful")
        return new_state
    
    def __str__(self) -> str:
        """Generate a string representation of the proof state.
        
        Returns:
            Formatted string showing all goals
        """
        if self.is_complete():
            return "✅ Proof complete."
        
        lines = [f"Proof state: {len(self.goals)} remaining goal(s)"]
        lines.append("=" * 50)
        
        for i, (ctx, goal) in enumerate(reversed(self.goals)):
            marker = ">>> " if i == 0 else "    "
            lines.append(f"{marker}Goal {len(self.goals)-i}:")
            lines.append(pretty_goal(ctx, goal))
            if i < len(self.goals) - 1:
                lines.append("-" * 50)
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the proof state to a dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "goals": [
                {
                    "context": [{"name": name, "formula": prop} for name, prop in ctx],
                    "proposition": goal
                }
                for ctx, goal in self.goals
            ],
            "is_complete": self.is_complete(),
            "theorem_name": self.proof_tree.theorem_name,
            "step_count": len(self.proof_tree.steps)
        }
