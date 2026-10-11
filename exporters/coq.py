"""
Coq Exporter
============

Exports proofs to Coq proof assistant syntax.
"""

from datetime import datetime
from typing import List, Any

from ..core.terms import Prop, Term, prop_repr, term_repr


def prop_to_coq(prop: Prop) -> str:
    """Convert a proposition to Coq syntax.
    
    Args:
        prop: Proposition to convert
        
    Returns:
        Coq syntax string
    """
    match prop:
        case ('not', p):
            return f"~({prop_to_coq(p)})"
        case ('and', p, q):
            return f"({prop_to_coq(p)} /\\ {prop_to_coq(q)})"
        case ('or', p, q):
            return f"({prop_to_coq(p)} \\/ {prop_to_coq(q)})"
        case ('implies', p, q):
            return f"({prop_to_coq(p)} -> {prop_to_coq(q)})"
        case ('forall', v, body):
            return f"(forall {v}, {prop_to_coq(body)})"
        case ('exists', v, body):
            return f"(exists {v}, {prop_to_coq(body)})"
        case ('bottom',):
            return "False"
        case ('pred', name, args):
            if name == "=" and len(args) == 2:
                return f"({term_to_coq(args[0])} = {term_to_coq(args[1])})"
            if args:
                return f"{name} {' '.join(term_to_coq(a) for a in args)}"
            return name
        case ('var', x):
            return x
        case ('const', c):
            return c
        case _:
            return str(prop)


def term_to_coq(t: Term) -> str:
    """Convert a term to Coq syntax.
    
    Args:
        t: Term to convert
        
    Returns:
        Coq syntax string
    """
    match t:
        case ("var", x):
            return x
        case ("const", c):
            return c
        case ("fun", name, args):
            if args:
                return f"({name} {' '.join(term_to_coq(a) for a in args)})"
            return name
        case ("lambda", params, body):
            return f"(fun {', '.join(params)} => {term_to_coq(body)})"
        case ("app", f, a):
            return f"({term_to_coq(f)} {term_to_coq(a)})"
        case _:
            return str(t)


def tactic_to_coq(tactic_name: str, arguments: List[Any]) -> str:
    """Convert a tactic to Coq syntax.
    
    Args:
        tactic_name: Name of the tactic
        arguments: Arguments to the tactic
        
    Returns:
        Coq tactic string
    """
    mapping = {
        "intro": "intros",
        "exact": "exact",
        "split": "split",
        "left": "left",
        "right": "right",
        "destruct": "destruct",
        "contradiction": "contradiction",
        "assumption": "assumption",
        "reflexivity": "reflexivity",
        "exists_intro": "exists",
        "apply": "apply",
        "auto": "auto",
        "forall_elim": "specialize",
    }
    
    base = mapping.get(tactic_name, tactic_name)
    
    if tactic_name == "forall_elim" and len(arguments) >= 2:
        return f"{base} ({arguments[0]} {arguments[1]})"
    
    if arguments:
        args_str = " ".join(str(arg) for arg in arguments)
        return f"{base} {args_str}"
    
    return base


def export_to_coq(proof_tree) -> str:
    """Export a proof tree to Coq syntax.
    
    Args:
        proof_tree: The proof tree to export
        
    Returns:
        Coq proof script
    """
    if not proof_tree.initial_goal or not proof_tree.steps:
        return ""
    
    options = proof_tree.export_options.get(type('ProofSystem', (), {'COQ': 'coq'})().COQ, 
                                           {"indent": 2, "include_imports": True})
    indent = " " * options.get("indent", 2)
    
    coq_lines = []
    
    # Add imports if needed
    if options.get("include_imports", True):
        coq_lines.extend([
            "Require Import Coq.Logic.Classical_Prop.",
            "Require Import Coq.Setoids.Setoid.",
            ""
        ])
    
    # Process initial goal
    ctx, goal = proof_tree.initial_goal
    
    # Generate hypotheses from context
    hypotheses = []
    for name, formula in ctx:
        hypotheses.append(f"({name} : {prop_to_coq(formula)})")
    
    # Theorem statement
    if hypotheses:
        coq_lines.append(f"Theorem {proof_tree.theorem_name} {' '.join(hypotheses)} : {prop_to_coq(goal)}.")
    else:
        coq_lines.append(f"Theorem {proof_tree.theorem_name} : {prop_to_coq(goal)}.")
    
    coq_lines.append("Proof.")
    
    # Process tactics
    for step in proof_tree.steps:
        if not step.success:
            coq_lines.append(f"{indent}(* Failed tactic: {step.tactic_name} {step.arguments} *)")
            continue
        coq_cmd = tactic_to_coq(step.tactic_name, step.arguments)
        if coq_cmd:
            coq_lines.append(f"{indent}{coq_cmd}.")
        else:
            coq_lines.append(f"{indent}(* No direct Coq equivalent for {step.tactic_name} *)")
    
    coq_lines.append("Qed.")
    coq_lines.append(f"(* Proof completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} *)")
    
    return "\n".join(coq_lines)
