"""
Lean Exporter
=============

Exports proofs to Lean 4 syntax.
"""

from datetime import datetime
from typing import List, Any

from ..core.terms import Prop, Term


def prop_to_lean(prop: Prop) -> str:
    """Convert a proposition to Lean syntax.
    
    Args:
        prop: Proposition to convert
        
    Returns:
        Lean syntax string
    """
    match prop:
        case ('not', p):
            return f"¬({prop_to_lean(p)})"
        case ('and', p, q):
            return f"({prop_to_lean(p)} ∧ {prop_to_lean(q)})"
        case ('or', p, q):
            return f"({prop_to_lean(p)} ∨ {prop_to_lean(q)})"
        case ('implies', p, q):
            return f"({prop_to_lean(p)} → {prop_to_lean(q)})"
        case ('forall', v, body):
            return f"(∀ ({v} : _), {prop_to_lean(body)})"
        case ('exists', v, body):
            return f"(∃ ({v} : _), {prop_to_lean(body)})"
        case ('bottom',):
            return "False"
        case ('pred', name, args):
            if name == "=" and len(args) == 2:
                return f"({term_to_lean(args[0])} = {term_to_lean(args[1])})"
            if args:
                return f"{name} {' '.join(term_to_lean(a) for a in args)}"
            return name
        case ('var', x):
            return x
        case ('const', c):
            return c
        case _:
            return str(prop)


def term_to_lean(t: Term) -> str:
    """Convert a term to Lean syntax.
    
    Args:
        t: Term to convert
        
    Returns:
        Lean syntax string
    """
    match t:
        case ("var", x):
            return x
        case ("const", c):
            return c
        case ("fun", name, args):
            if args:
                return f"({name} {' '.join(term_to_lean(a) for a in args)})"
            return name
        case ("lambda", params, body):
            return f"(fun {' '.join(params)} => {term_to_lean(body)})"
        case ("app", f, a):
            return f"({term_to_lean(f)} {term_to_lean(a)})"
        case _:
            return str(t)


def tactic_to_lean(tactic_name: str, arguments: List[Any]) -> str:
    """Convert a tactic to Lean syntax.
    
    Args:
        tactic_name: Name of the tactic
        arguments: Arguments to the tactic
        
    Returns:
        Lean tactic string
    """
    mapping = {
        "intro": "intro",
        "exact": "exact",
        "split": "constructor",
        "left": "left",
        "right": "right",
        "destruct": "cases",
        "contradiction": "contradiction",
        "assumption": "assumption",
        "reflexivity": "rfl",
        "exists_intro": "use",
        "apply": "apply",
        "auto": "simp?; tauto?",
        "forall_elim": "specialize",
    }
    
    base = mapping.get(tactic_name, tactic_name)
    
    if arguments:
        args_str = " ".join(str(arg) for arg in arguments)
        return f"{base} {args_str}"
    
    return base


def export_to_lean(proof_tree) -> str:
    """Export a proof tree to Lean syntax.
    
    Args:
        proof_tree: The proof tree to export
        
    Returns:
        Lean proof script
    """
    if not proof_tree.initial_goal or not proof_tree.steps:
        return ""
    
    options = proof_tree.export_options.get(type('ProofSystem', (), {'LEAN': 'lean'})().LEAN,
                                           {"use_structured_proofs": True, "indent": 2, "include_imports": True})
    indent = " " * options.get("indent", 2)
    
    lean_lines = []
    
    # Add imports if needed
    if options.get("include_imports", True):
        lean_lines.extend([
            "import Mathlib",
            "import Mathlib.Tactic",
            ""
        ])
    
    # Process initial goal
    ctx, goal = proof_tree.initial_goal
    
    # Generate hypotheses from context
    hypotheses = []
    for name, formula in ctx:
        hypotheses.append(f"({name} : {prop_to_lean(formula)})")
    
    # Theorem statement
    theorem_header = f"theorem {proof_tree.theorem_name}"
    if hypotheses:
        theorem_header += f" {' '.join(hypotheses)}"
    theorem_header += f" : {prop_to_lean(goal)}"
    
    if options.get("use_structured_proofs", True):
        # Structured proof style
        lean_lines.append(theorem_header + " := by")
        
        # Process tactics
        has_failed_step = False
        for step in proof_tree.steps:
            if not step.success:
                lean_lines.append(f"{indent}-- Failed tactic: {step.tactic_name} {step.arguments}")
                has_failed_step = True
                continue
            lean_cmd = tactic_to_lean(step.tactic_name, step.arguments)
            if lean_cmd:
                lean_lines.append(f"{indent}{lean_cmd}")
            else:
                lean_lines.append(f"{indent}-- No direct Lean equivalent for {step.tactic_name} {step.arguments}")
        
        if has_failed_step:
            lean_lines.append(f"{indent}exact sorry")
    else:
        # Term mode proof
        lean_lines.append(theorem_header + " :=")
        lean_lines.append(f"{indent}by sorry -- Term mode proof export not fully implemented")
    
    lean_lines.append(f"\n-- Proof exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(lean_lines)
