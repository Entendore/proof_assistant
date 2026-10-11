"""
Isabelle Exporter
=================

Exports proofs to Isabelle/HOL syntax.
"""

from datetime import datetime
from typing import List, Any

from ..core.terms import Prop, Term


def prop_to_isabelle(prop: Prop) -> str:
    """Convert a proposition to Isabelle syntax.
    
    Args:
        prop: Proposition to convert
        
    Returns:
        Isabelle syntax string
    """
    match prop:
        case ('not', p):
            return f"\\<not>({prop_to_isabelle(p)})"
        case ('and', p, q):
            return f"({prop_to_isabelle(p)} \\<and> {prop_to_isabelle(q)})"
        case ('or', p, q):
            return f"({prop_to_isabelle(p)} \\<or> {prop_to_isabelle(q)})"
        case ('implies', p, q):
            return f"({prop_to_isabelle(p)} \\<longrightarrow> {prop_to_isabelle(q)})"
        case ('forall', v, body):
            return f"(\\<forall>{v}. {prop_to_isabelle(body)})"
        case ('exists', v, body):
            return f"(\\<exists>{v}. {prop_to_isabelle(body)})"
        case ('bottom',):
            return "False"
        case ('pred', name, args):
            if name == "=" and len(args) == 2:
                return f"({term_to_isabelle(args[0])} = {term_to_isabelle(args[1])})"
            if args:
                return f"({name} {' '.join(term_to_isabelle(a) for a in args)})"
            return name
        case ('var', x):
            return x
        case ('const', c):
            return c
        case _:
            return str(prop)


def term_to_isabelle(t: Term) -> str:
    """Convert a term to Isabelle syntax.
    
    Args:
        t: Term to convert
        
    Returns:
        Isabelle syntax string
    """
    match t:
        case ("var", x):
            return x
        case ("const", c):
            return c
        case ("fun", name, args):
            if args:
                return f"({name} {' '.join(term_to_isabelle(a) for a in args)})"
            return name
        case ("lambda", params, body):
            return f"(\\<lambda>{' '.join(params)}. {term_to_isabelle(body)})"
        case ("app", f, a):
            return f"({term_to_isabelle(f)} {term_to_isabelle(a)})"
        case _:
            return str(t)


def tactic_to_isabelle(tactic_name: str, arguments: List[Any]) -> str:
    """Convert a tactic to Isabelle syntax.
    
    Args:
        tactic_name: Name of the tactic
        arguments: Arguments to the tactic
        
    Returns:
        Isabelle tactic string
    """
    mapping = {
        "intro": "intro",
        "exact": "erule",
        "split": "rule conjI",
        "left": "rule disjI1",
        "right": "rule disjI2",
        "destruct": "elim",
        "contradiction": "contradiction",
        "assumption": "assumption",
        "reflexivity": "rule refl",
        "exists_intro": "rule exI",
        "apply": "erule",
        "auto": "auto",
        "forall_elim": "spec",
    }
    
    base = mapping.get(tactic_name, tactic_name)
    
    if arguments:
        args_str = " ".join(str(arg) for arg in arguments)
        return f"apply ({base} {args_str})"
    
    return f"apply ({base})"


def export_to_isabelle(proof_tree) -> str:
    """Export a proof tree to Isabelle syntax.
    
    Args:
        proof_tree: The proof tree to export
        
    Returns:
        Isabelle theory file content
    """
    if not proof_tree.initial_goal or not proof_tree.steps:
        return ""
    
    options = proof_tree.export_options.get(type('ProofSystem', (), {'ISABELLE': 'isabelle'})().ISABELLE,
                                           {"theory_name": "My_Theory", "indent": 2, "include_headers": True})
    indent = " " * options.get("indent", 2)
    
    isabelle_lines = []
    
    # Add theory header if needed
    if options.get("include_headers", True):
        theory_name = options.get("theory_name", "My_Theory")
        isabelle_lines.extend([
            f"theory {theory_name}",
            "  imports Main",
            "begin",
            ""
        ])
    
    # Process initial goal
    ctx, goal = proof_tree.initial_goal
    
    # Generate assumptions from context
    theorem_header = f"theorem {proof_tree.theorem_name}"
    
    if ctx:
        assumptions = []
        for i, (name, formula) in enumerate(ctx):
            assumptions.append(f"assumes {name}: \"{prop_to_isabelle(formula)}\"")
        theorem_header += ":\n" + f"\n{indent}".join(assumptions)
        theorem_header += f"\n{indent}shows \"{prop_to_isabelle(goal)}\""
    else:
        theorem_header += f": \"{prop_to_isabelle(goal)}\""
    
    isabelle_lines.append(theorem_header)
    isabelle_lines.append("proof -")
    
    # Process tactics
    has_failed_step = False
    for step in proof_tree.steps:
        if not step.success:
            isabelle_lines.append(f"{indent}(* Failed tactic: {step.tactic_name} {step.arguments} *)")
            has_failed_step = True
            continue
        isabelle_cmd = tactic_to_isabelle(step.tactic_name, step.arguments)
        if isabelle_cmd:
            isabelle_lines.append(f"{indent}{isabelle_cmd}")
        else:
            isabelle_lines.append(f"{indent}(* No direct Isabelle equivalent for {step.tactic_name} *)")
    
    # Complete the proof
    if not has_failed_step:
        isabelle_lines.append(f"{indent}qed")
    else:
        isabelle_lines.append(f"{indent}oops (* Proof incomplete due to failed tactics *)")
    
    # Add theory footer if needed
    if options.get("include_headers", True):
        isabelle_lines.extend([
            "",
            "end"
        ])
    
    return "\n".join(isabelle_lines)
