"""
Proof Tactics
=============

This module implements the proof tactics for natural deduction.
Each tactic transforms the proof state by modifying the goal stack.

Available Tactics:
    - intro: Introduce implication or universal quantifier
    - exact: Solve goal with exact hypothesis match
    - assumption: Solve goal if it matches a hypothesis
    - split: Split conjunction into two subgoals
    - destruct: Case analysis on a hypothesis
    - left/right: Solve disjunction by proving one side
    - exists_intro: Provide witness for existential
    - forall_elim: Instantiate universal quantifier
    - contradiction: Solve goal when contradiction found
    - auto: Automatic proof search
    - reflexivity: Solve reflexive equality
    - and many more...

Example:
    >>> from proof_assistant.tactics import *
    >>> state = ProofState([([], parse_formula("P -> P"))])
    >>> state = tactic_intro(state, "H")
    >>> state = tactic_exact(state, "H")
    >>> state.is_complete()
    True
"""

import logging
from typing import List, Tuple, Optional, Union, Set
from functools import wraps
from copy import deepcopy

from .core.terms import (
    Term, Prop, Context, Goal,
    var, const, fun, pred,
    implies, and_, or_, not_, forall, exists, bottom, eq,
    prop_repr, term_repr, pretty_goal,
    free_vars, free_vars_term, fresh_var,
    substitute, substitute_var, subst_term_var,
    alpha_eq, term_eq
)
from .core.proof_state import ProofState
from .core.parser import parse_formula, parse_term

logger = logging.getLogger("ProofAssistant")


# === Error Handling ===

class TacticError(Exception):
    """Exception raised when a tactic fails."""
    pass


# === Tactic Decorator ===

def proof_tactic(func):
    """Decorator for proof tactics with error handling and recording.
    
    Wraps a tactic function to:
    1. Copy the state before execution
    2. Handle exceptions gracefully
    3. Record successful/failed steps
    
    Args:
        func: Tactic function to wrap
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(state: ProofState, *args, **kwargs) -> ProofState:
        state_before = ProofState(deepcopy(state.goals), state.proof_tree)
        try:
            working_state = ProofState(deepcopy(state.goals), state.proof_tree)
            result = func(working_state, *args, **kwargs)
            result.history = state.history.copy()
            result.future = state.future.copy()
            state.proof_tree.record_step(func.__name__, list(args), state_before, result, success=True)
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Tactic {func.__name__} failed: {error_msg}")
            state.proof_tree.record_step(func.__name__, list(args), state_before, state,
                                        success=False, error_message=error_msg)
            raise TacticError(error_msg)
    return wrapper


# === Name Generation ===

def generate_hypothesis_name(premise: Prop, ctx: Context) -> str:
    """Generate a meaningful hypothesis name.
    
    Args:
        premise: The proposition to name
        ctx: Current context (to avoid duplicates)
        
    Returns:
        A unique hypothesis name
    """
    existing_names = {name for name, _ in ctx}
    
    match premise:
        case ('pred', name, _):
            base = f"H{name}"
        case ('not', _):
            base = "Hn"
        case ('and', _, _):
            base = "Hand"
        case ('or', _, _):
            base = "Hor"
        case ('implies', _, _):
            base = "Himp"
        case ('forall', v, _):
            base = f"Hall{v}"
        case ('exists', v, _):
            base = f"Hex{v}"
        case _:
            base = "H"
    
    i = 1
    name = base
    while name in existing_names:
        name = f"{base}{i}"
        i += 1
    
    return name


def collect_vars_in_context(ctx: Context) -> Set[str]:
    """Collect all variable names in a context.
    
    Args:
        ctx: Context to analyze
        
    Returns:
        Set of variable names
    """
    vars_set = set()
    for name, prop in ctx:
        vars_set.add(name)
        vars_set.update(free_vars(prop))
    return vars_set


# === Basic Tactics ===

@proof_tactic
def tactic_intro(state: ProofState, name: Optional[str] = None) -> ProofState:
    """Introduce an implication or universal quantifier.
    
    For A → B, assumes A and proves B.
    For ∀x. P(x), introduces a fresh variable.
    
    Args:
        state: Current proof state
        name: Optional name for the introduced hypothesis
        
    Returns:
        New proof state with the introduction applied
        
    Raises:
        TacticError: If the goal is not an implication or forall
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    if goal[0] == "implies":
        premise, conclusion = goal[1], goal[2]
        if name is None:
            name = generate_hypothesis_name(premise, ctx)
        if any(n == name for n, _ in ctx):
            raise TacticError(f"Name '{name}' already exists in context")
        new_ctx = ctx + [(name, premise)]
        logger.info(f"Intro: assuming {prop_repr(premise)} as {name}")
        return state.add_subgoals([(new_ctx, conclusion)])
    
    elif goal[0] == "forall":
        varname, body = goal[1], goal[2]
        all_vars = collect_vars_in_context(ctx) | free_vars(body)
        fresh_var_name = fresh_var(existing=all_vars, base=varname)
        fresh_var_term = var(fresh_var_name)
        new_body = substitute(body, varname, fresh_var_term)
        logger.info(f"Intro: introducing fresh variable {fresh_var_name} for {varname}")
        return state.add_subgoals([(ctx, new_body)])
    
    else:
        raise TacticError(f"intro tactic failed: goal is not implication or forall, but {goal[0]}")


@proof_tactic
def tactic_exact(state: ProofState, term: Union[str, Prop]) -> ProofState:
    """Solve the goal with an exact match.
    
    Args:
        state: Current proof state
        term: Hypothesis name or proposition that exactly matches the goal
        
    Returns:
        New proof state with the goal solved
        
    Raises:
        TacticError: If no match is found
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    if isinstance(term, str):
        hyp = next((f for n, f in ctx if n == term), None)
        if hyp is None:
            existing_names = [n for n, _ in ctx]
            raise TacticError(f"No hypothesis named '{term}'. Available: {existing_names}")
        
        if alpha_eq(hyp, goal):
            logger.info(f"Exact: solved with hypothesis {term}")
            return ProofState(state.goals[:-1], state.proof_tree)
        else:
            raise TacticError(f"Hypothesis '{term}' doesn't match goal\n"
                            f"Hypothesis: {prop_repr(hyp)}\n"
                            f"Goal: {prop_repr(goal)}")
    else:
        if alpha_eq(term, goal):
            logger.info("Exact: solved with provided proposition")
            return ProofState(state.goals[:-1], state.proof_tree)
        else:
            raise TacticError(f"Formula doesn't match goal\n"
                            f"Formula: {prop_repr(term)}\n"
                            f"Goal: {prop_repr(goal)}")


@proof_tactic
def tactic_assumption(state: ProofState) -> ProofState:
    """Solve the goal if it matches any hypothesis.
    
    Args:
        state: Current proof state
        
    Returns:
        New proof state with the goal solved
        
    Raises:
        TacticError: If no matching hypothesis is found
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    for name, hyp in reversed(ctx):
        if alpha_eq(hyp, goal):
            logger.info(f"Assumption: solved with hypothesis {name}")
            return ProofState(state.goals[:-1], state.proof_tree)
    
    raise TacticError("No matching hypothesis found")


@proof_tactic
def tactic_split(state: ProofState) -> ProofState:
    """Split a conjunction goal into two subgoals.
    
    Args:
        state: Current proof state
        
    Returns:
        New proof state with two subgoals
        
    Raises:
        TacticError: If the goal is not a conjunction
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    if goal[0] == "and":
        left, right = goal[1], goal[2]
        logger.info(f"Split: creating subgoals for {prop_repr(left)} and {prop_repr(right)}")
        return state.add_subgoals([(ctx, left), (ctx, right)])
    else:
        raise TacticError(f"split tactic failed: goal is not conjunction, but {goal[0]}")


@proof_tactic
def tactic_destruct(state: ProofState, name: str) -> ProofState:
    """Perform case analysis on a hypothesis.
    
    For a conjunction, splits it into two hypotheses.
    For a disjunction, creates two subgoals.
    
    Args:
        state: Current proof state
        name: Name of the hypothesis to destruct
        
    Returns:
        New proof state with destruct applied
        
    Raises:
        TacticError: If the hypothesis is not found or not destructible
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    hyp_idx = -1
    hyp = None
    for i, (n, f) in enumerate(ctx):
        if n == name:
            hyp_idx = i
            hyp = f
            break
    
    if hyp is None:
        existing_names = [n for n, _ in ctx]
        raise TacticError(f"No hypothesis named '{name}'. Available: {existing_names}")
    
    ctx_before = ctx[:hyp_idx]
    ctx_after = ctx[hyp_idx+1:]
    
    if hyp[0] == "and":
        left, right = hyp[1], hyp[2]
        left_name = f"{name}_left"
        right_name = f"{name}_right"
        new_ctx = ctx_before + [(left_name, left), (right_name, right)] + ctx_after
        logger.info(f"Destruct: splitting conjunction {name}")
        return state.add_subgoals([(new_ctx, goal)])
    
    elif hyp[0] == "or":
        left, right = hyp[1], hyp[2]
        left_ctx = ctx_before + [(f"{name}_left", left)] + ctx_after
        right_ctx = ctx_before + [(f"{name}_right", right)] + ctx_after
        logger.info(f"Destruct: case analysis on disjunction {name}")
        return state.add_subgoals([(left_ctx, goal), (right_ctx, goal)])
    
    elif hyp[0] == "exists":
        varname, body = hyp[1], hyp[2]
        # Generate a fresh variable for the witness
        all_vars = collect_vars_in_context(ctx) | free_vars(body)
        witness_name = fresh_var(existing=all_vars, base=varname)
        witness_term = var(witness_name)
        new_body = substitute(body, varname, witness_term)
        new_ctx = ctx_before + [(f"{name}_witness", new_body)] + ctx_after
        logger.info(f"Destruct: introducing witness {witness_name} for existential {name}")
        return state.add_subgoals([(new_ctx, goal)])
    
    else:
        raise TacticError(f"Hypothesis '{name}' is not ∧, ∨, or ∃, but {hyp[0]}")


@proof_tactic
def tactic_left(state: ProofState) -> ProofState:
    """Solve a disjunction goal by proving the left component.
    
    Args:
        state: Current proof state
        
    Returns:
        New proof state with left disjunct as goal
        
    Raises:
        TacticError: If the goal is not a disjunction
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    if goal[0] == "or":
        left = goal[1]
        logger.info(f"Left: proving {prop_repr(left)}")
        return state.add_subgoals([(ctx, left)])
    else:
        raise TacticError(f"left tactic failed: goal is not disjunction, but {goal[0]}")


@proof_tactic
def tactic_right(state: ProofState) -> ProofState:
    """Solve a disjunction goal by proving the right component.
    
    Args:
        state: Current proof state
        
    Returns:
        New proof state with right disjunct as goal
        
    Raises:
        TacticError: If the goal is not a disjunction
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    if goal[0] == "or":
        right = goal[2]
        logger.info(f"Right: proving {prop_repr(right)}")
        return state.add_subgoals([(ctx, right)])
    else:
        raise TacticError(f"right tactic failed: goal is not disjunction, but {goal[0]}")


@proof_tactic
def tactic_forall_elim(state: ProofState, hyp_name: str, term_str: str) -> ProofState:
    """Instantiate a universal quantifier with a specific term.
    
    Args:
        state: Current proof state
        hyp_name: Name of the universally quantified hypothesis
        term_str: String representation of the term to instantiate with
        
    Returns:
        New proof state with the instantiated hypothesis
        
    Raises:
        TacticError: If the hypothesis is not found or not universal
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    hyp = next((f for n, f in ctx if n == hyp_name), None)
    if hyp is None:
        existing_names = [n for n, _ in ctx]
        raise TacticError(f"No hypothesis named '{hyp_name}'. Available: {existing_names}")
    
    if hyp[0] != "forall":
        raise TacticError(f"Hypothesis '{hyp_name}' is not ∀, but {hyp[0]}")
    
    try:
        term = parse_term(term_str)
    except Exception as e:
        raise TacticError(f"Invalid term '{term_str}': {e}")
    
    varname, body = hyp[1], hyp[2]
    new_prop = substitute(body, varname, term)
    
    # Generate unique name for the instantiated hypothesis
    new_hyp_name = f"{hyp_name}_inst"
    i = 1
    while any(n == new_hyp_name for n, _ in ctx):
        new_hyp_name = f"{hyp_name}_inst{i}"
        i += 1
    
    new_ctx = ctx + [(new_hyp_name, new_prop)]
    logger.info(f"Forall elimination: instantiated {hyp_name} with {term_repr(term)} as {new_hyp_name}")
    return state.add_subgoals([(new_ctx, goal)])


@proof_tactic
def tactic_exists_intro(state: ProofState, term_str: str) -> ProofState:
    """Provide a witness for an existential quantifier.
    
    Args:
        state: Current proof state
        term_str: String representation of the witness term
        
    Returns:
        New proof state with the witness substituted
        
    Raises:
        TacticError: If the goal is not existential or term is invalid
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    if goal[0] != "exists":
        raise TacticError(f"Goal is not ∃, but {goal[0]}")
    
    try:
        term = parse_term(term_str)
    except Exception as e:
        raise TacticError(f"Invalid term '{term_str}': {e}")
    
    varname, body = goal[1], goal[2]
    new_goal = substitute(body, varname, term)
    logger.info(f"Exists introduction: using witness {term_repr(term)}")
    return state.add_subgoals([(ctx, new_goal)])


@proof_tactic
def tactic_contradiction(state: ProofState) -> ProofState:
    """Solve the goal when a contradiction is found.
    
    Looks for:
    1. Bottom (⊥) in the context
    2. A proposition and its negation in the context
    
    Args:
        state: Current proof state
        
    Returns:
        New proof state with the goal solved
        
    Raises:
        TacticError: If no contradiction is found
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, _ = current
    
    # Check for bottom in context
    for name, hyp in ctx:
        if hyp[0] == "bottom":
            logger.info(f"Contradiction: found ⊥ as hypothesis {name}")
            return ProofState(state.goals[:-1], state.proof_tree)
    
    # Check for P and ¬P in context
    props = {name: hyp for name, hyp in ctx}
    for name1, p in props.items():
        for name2, q in props.items():
            if name1 != name2 and p[0] == "not" and alpha_eq(p[1], q):
                logger.info(f"Contradiction: found {name1} and {name2}")
                return ProofState(state.goals[:-1], state.proof_tree)
    
    raise TacticError("No contradiction found in context")


@proof_tactic
def tactic_reflexivity(state: ProofState) -> ProofState:
    """Solve an equality goal of the form t = t.
    
    Args:
        state: Current proof state
        
    Returns:
        New proof state with the goal solved
        
    Raises:
        TacticError: If the goal is not a reflexive equality
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    if goal[0] == "pred" and goal[1] == "=":
        left, right = goal[2]
        if term_eq(left, right):
            logger.info("Reflexivity: solved t = t")
            return ProofState(state.goals[:-1], state.proof_tree)
    
    raise TacticError("Goal is not a reflexive equality t = t")


@proof_tactic
def tactic_not_intro(state: ProofState, name: str = "H") -> ProofState:
    """Prove a negation ¬P by assuming P and proving ⊥.
    
    Args:
        state: Current proof state
        name: Name for the assumed hypothesis
        
    Returns:
        New proof state with P in context and ⊥ as goal
        
    Raises:
        TacticError: If the goal is not a negation
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    if goal[0] != "not":
        raise TacticError("Goal is not a negation ¬P")
    
    p = goal[1]
    new_ctx = ctx + [(name, p)]
    logger.info(f"Not intro: assuming {prop_repr(p)} to prove ⊥")
    return state.add_subgoals([(new_ctx, bottom())])


@proof_tactic
def tactic_not_elim(state: ProofState, hyp_name: str) -> ProofState:
    """Use double negation ¬¬P to prove P.
    
    Args:
        state: Current proof state
        hyp_name: Name of the double negation hypothesis
        
    Returns:
        New proof state with the goal solved
        
    Raises:
        TacticError: If the hypothesis is not a double negation
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    hyp = next((f for n, f in ctx if n == hyp_name), None)
    if hyp is None:
        raise TacticError(f"No hypothesis named '{hyp_name}'")
    
    if hyp[0] == 'not' and hyp[1][0] == 'not':
        P = hyp[1][1]
        if alpha_eq(P, goal):
            logger.info(f"Not elim: solved with double negation {hyp_name}")
            return ProofState(state.goals[:-1], state.proof_tree)
        else:
            raise TacticError("Goal doesn't match ¬¬P inner proposition")
    else:
        raise TacticError("Hypothesis is not double negation")


@proof_tactic
def tactic_apply(state: ProofState, hyp_name: str) -> ProofState:
    """Apply an implication to solve the goal.
    
    If we have H: A → B and goal is B, creates subgoal A.
    
    Args:
        state: Current proof state
        hyp_name: Name of the implication hypothesis
        
    Returns:
        New proof state with the antecedent as goal
        
    Raises:
        TacticError: If the hypothesis is not an implication
    """
    current = state.current()
    if current is None:
        raise TacticError("No current goal")
    ctx, goal = current
    
    hyp = next((f for n, f in ctx if n == hyp_name), None)
    if hyp is None:
        raise TacticError(f"No hypothesis named '{hyp_name}'")
    
    if hyp[0] != "implies":
        raise TacticError(f"Hypothesis '{hyp_name}' is not an implication")
    
    antecedent, consequent = hyp[1], hyp[2]
    
    if alpha_eq(consequent, goal):
        logger.info(f"Apply: need to prove {prop_repr(antecedent)}")
        return state.add_subgoals([(ctx, antecedent)])
    else:
        raise TacticError(f"Consequent doesn't match goal\n"
                         f"Consequent: {prop_repr(consequent)}\n"
                         f"Goal: {prop_repr(goal)}")


@proof_tactic
def tactic_auto(state: ProofState, depth: int = 3) -> ProofState:
    """Automatic proof search.
    
    Tries various tactics to solve the goal automatically.
    
    Args:
        state: Current proof state
        depth: Maximum search depth
        
    Returns:
        New proof state with progress made
        
    Raises:
        TacticError: If automatic proof search fails
    """
    if depth <= 0:
        raise TacticError("Auto depth exceeded")
    
    # Try assumption first
    try:
        return tactic_assumption(state)
    except TacticError:
        pass
    
    # Try contradiction
    try:
        return tactic_contradiction(state)
    except TacticError:
        pass
    
    current = state.current()
    if current:
        ctx, goal = current
        
        # Try split for conjunction
        if goal[0] == "and":
            try:
                split_state = tactic_split(state)
                # Recursively auto both subgoals
                left_state = tactic_auto(split_state, depth - 1)
                return tactic_auto(left_state, depth - 1)
            except TacticError:
                pass
        
        # Try intro for implication
        if goal[0] == "implies":
            try:
                intro_state = tactic_intro(state, f"H_auto{depth}")
                return tactic_auto(intro_state, depth - 1)
            except TacticError:
                pass
        
        # Try intro for forall
        if goal[0] == "forall":
            try:
                intro_state = tactic_intro(state)
                return tactic_auto(intro_state, depth - 1)
            except TacticError:
                pass
    
    # Try applying implications from context
    for name, hyp in ctx:
        if hyp[0] == "implies" and alpha_eq(hyp[2], goal):
            try:
                apply_state = tactic_apply(state, name)
                return tactic_auto(apply_state, depth - 1)
            except TacticError:
                continue
    
    raise TacticError("Auto tactic failed")


# === Tactic Hints ===

def tactic_hint(state: ProofState) -> List[str]:
    """Generate hints for the current goal.
    
    Args:
        state: Current proof state
        
    Returns:
        List of hint strings
    """
    hints = []
    current = state.current()
    
    if current is None:
        return ["No current goal"]
    
    ctx, goal = current
    hints.append(f"Goal: {prop_repr(goal)}")
    hints.append("Possible next steps:")
    
    match goal:
        case ('implies', p, q):
            hints.append("- Use 'intro' to assume the premise")
        case ('and', p, q):
            hints.append("- Use 'split' to break into two subgoals")
        case ('forall', v, body):
            hints.append("- Use 'intro' to introduce a new variable")
        case ('exists', v, body):
            hints.append("- Use 'exists_intro <term>' to provide a witness")
        case ('or', p, q):
            hints.append("- Use 'left' to prove the left disjunct")
            hints.append("- Use 'right' to prove the right disjunct")
        case ('not', p):
            hints.append("- Use 'not_intro' to assume the negation and prove ⊥")
        case ('pred', "=", [left, right]) if term_eq(left, right):
            hints.append("- Use 'reflexivity' to solve the equality")
        case _:
            hints.append("- Try 'assumption' if goal matches a hypothesis")
            hints.append("- Try 'auto' for automatic proof search")
    
    # Check for applicable hypotheses
    for name, hyp in ctx:
        match hyp:
            case ('implies', A, B) if alpha_eq(B, goal):
                hints.append(f"- Use 'apply {name}' to apply the implication")
            case ('and', A, B):
                hints.append(f"- Use 'destruct {name}' to break the conjunction")
            case ('or', A, B):
                hints.append(f"- Use 'destruct {name}' for case analysis")
            case ('not', ('not', P)) if alpha_eq(P, goal):
                hints.append(f"- Use 'not_elim {name}' for double negation elimination")
            case ('forall', v, body):
                hints.append(f"- Use 'forall_elim {name} <term>' to instantiate")
    
    return hints


# === Command Processing ===

def explain_tactic(tactic_name: str) -> str:
    """Get an explanation for a tactic.
    
    Args:
        tactic_name: Name of the tactic
        
    Returns:
        Explanation string
    """
    explanations = {
        "intro": "Introduces an implication or universal quantifier. For A → B, it assumes A and proves B. For ∀x. P(x), it introduces a fresh variable.",
        "exact": "Solves the goal when it exactly matches a hypothesis.",
        "split": "Splits a conjunction goal A ∧ B into two subgoals: prove A and prove B.",
        "destruct": "Performs case analysis on a disjunction or conjunction hypothesis.",
        "left": "Solves a disjunction goal A ∨ B by proving A.",
        "right": "Solves a disjunction goal A ∨ B by proving B.",
        "forall_elim": "Instantiates a universal quantifier with a specific term.",
        "exists_intro": "Provides a witness for an existential quantifier.",
        "contradiction": "Solves the goal when ⊥ is in the context.",
        "assume": "Adds a new hypothesis to the context.",
        "rename": "Renames a hypothesis.",
        "clear": "Removes a hypothesis from the context.",
        "not_intro": "Proves ¬P by assuming P and proving ⊥.",
        "not_elim": "Uses double negation ¬¬P to prove P.",
        "assumption": "Solves the goal if it matches a hypothesis.",
        "reflexivity": "Solves equality goals of the form t = t.",
        "auto": "Attempts to automatically prove the goal using simple tactics.",
        "apply": "Applies an implication to reduce the goal to proving the antecedent.",
    }
    return explanations.get(tactic_name, "No explanation available.")


def process_command(state: Optional[ProofState], command: str) -> Tuple[Optional[ProofState], str]:
    """Process a command string and return the new state.
    
    Args:
        state: Current proof state (may be None)
        command: Command string to process
        
    Returns:
        Tuple of (new_state, message)
    """
    cmd = command.strip()
    if not cmd:
        return state, ""
    
    parts = cmd.split(maxsplit=1)
    cmd_name = parts[0]
    arg = parts[1] if len(parts) > 1 else None
    
    try:
        # Goal command
        if cmd_name == "goal":
            if arg is None:
                return state, "Usage: goal <expr>"
            prop = parse_formula(arg)
            new_state = ProofState([([], prop)])
            return new_state, f"Goal set: {prop_repr(prop)}"
        
        # Help command
        if cmd_name == "help":
            help_text = [
                "Available commands:",
                "  goal <expr>         - Set the goal to prove",
                "  intro [name]        - Introduce implication or forall",
                "  exact <hyp>         - Solve with exact match",
                "  assumption          - Solve if matches hypothesis",
                "  split               - Split conjunction",
                "  destruct <name>     - Case analysis on hypothesis",
                "  left/right          - Prove left/right disjunct",
                "  forall_elim <h> <t> - Instantiate universal",
                "  exists_intro <term> - Provide witness",
                "  contradiction       - Solve with contradiction",
                "  reflexivity         - Solve reflexive equality",
                "  not_intro [name]    - Prove negation",
                "  not_elim <name>     - Use double negation",
                "  apply <name>        - Apply implication",
                "  auto [depth]        - Automatic proof search",
                "  hint                - Show hints for current goal",
                "  undo                - Undo last tactic",
                "  redo                - Redo last undone tactic",
                "  state               - Show current state",
                "  explain <tactic>    - Explain a tactic",
            ]
            return state, "\n".join(help_text)
        
        # Require an active proof for other commands
        if state is None:
            return state, "No active proof. Use 'goal <expr>' to set a goal."
        
        # Tactic commands
        if cmd_name == "intro":
            new_state = tactic_intro(state, arg)
            return new_state, str(new_state)
        
        elif cmd_name == "exact":
            if arg is None:
                return state, "Usage: exact <hyp_name>"
            new_state = tactic_exact(state, arg)
            return new_state, str(new_state)
        
        elif cmd_name == "assumption":
            new_state = tactic_assumption(state)
            return new_state, str(new_state)
        
        elif cmd_name == "split":
            new_state = tactic_split(state)
            return new_state, str(new_state)
        
        elif cmd_name == "destruct":
            if arg is None:
                return state, "Usage: destruct <hyp_name>"
            new_state = tactic_destruct(state, arg)
            return new_state, str(new_state)
        
        elif cmd_name == "left":
            new_state = tactic_left(state)
            return new_state, str(new_state)
        
        elif cmd_name == "right":
            new_state = tactic_right(state)
            return new_state, str(new_state)
        
        elif cmd_name == "forall_elim":
            if arg is None:
                return state, "Usage: forall_elim <hyp_name> <term>"
            parts2 = arg.split(maxsplit=1)
            if len(parts2) != 2:
                return state, "Usage: forall_elim <hyp_name> <term>"
            hyp_name, term_str = parts2
            new_state = tactic_forall_elim(state, hyp_name, term_str)
            return new_state, str(new_state)
        
        elif cmd_name == "exists_intro":
            if arg is None:
                return state, "Usage: exists_intro <term>"
            new_state = tactic_exists_intro(state, arg)
            return new_state, str(new_state)
        
        elif cmd_name == "contradiction":
            new_state = tactic_contradiction(state)
            return new_state, str(new_state)
        
        elif cmd_name == "reflexivity":
            new_state = tactic_reflexivity(state)
            return new_state, str(new_state)
        
        elif cmd_name == "not_intro":
            name = arg if arg else "H"
            new_state = tactic_not_intro(state, name)
            return new_state, str(new_state)
        
        elif cmd_name == "not_elim":
            if arg is None:
                return state, "Usage: not_elim <hyp_name>"
            new_state = tactic_not_elim(state, arg)
            return new_state, str(new_state)
        
        elif cmd_name == "apply":
            if arg is None:
                return state, "Usage: apply <hyp_name>"
            new_state = tactic_apply(state, arg)
            return new_state, str(new_state)
        
        elif cmd_name == "auto":
            depth = int(arg) if arg and arg.isdigit() else 3
            new_state = tactic_auto(state, depth)
            return new_state, str(new_state)
        
        elif cmd_name == "hint":
            hints = tactic_hint(state)
            return state, "\n".join(hints)
        
        elif cmd_name == "undo":
            new_state = state.undo()
            if new_state:
                return new_state, str(new_state)
            return state, "No actions to undo"
        
        elif cmd_name == "redo":
            new_state = state.redo()
            if new_state:
                return new_state, str(new_state)
            return state, "No actions to redo"
        
        elif cmd_name == "state":
            return state, str(state)
        
        elif cmd_name == "explain":
            if arg is None:
                return state, "Usage: explain <tactic_name>"
            return state, explain_tactic(arg)
        
        else:
            return state, f"Unknown command: {cmd_name}"
    
    except TacticError as e:
        return state, f"Error: {str(e)}"
    except Exception as e:
        return state, f"Unexpected error: {str(e)}"
