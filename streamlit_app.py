"""
Interactive Proof Assistant - Streamlit Application
====================================================

A comprehensive web interface for formal theorem proving with:
- Interactive proof construction
- Real-time proof state visualization
- Export to Coq, Isabelle, and Lean
- Command history and undo/redo
- Syntax highlighting and help

Run with: streamlit run streamlit_app.py
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
from copy import deepcopy
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from proof_assistant.core.terms import prop_repr, term_repr, pretty_goal
from proof_assistant.core.proof_state import ProofState, ProofTree
from proof_assistant.core.parser import parse_formula, parse_term
from proof_assistant.tactics import (
    process_command, tactic_hint, explain_tactic,
    TacticError
)


# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Interactive Proof Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': """
        # Interactive Proof Assistant
        
        A web-based theorem proving assistant supporting natural deduction
        with export capabilities to Coq, Isabelle, and Lean.
        
        Version 2.0.0
        """
    }
)


# ============================================================================
# Session State Initialization
# ============================================================================

def init_session_state():
    """Initialize all session state variables."""
    if 'proof_state' not in st.session_state:
        st.session_state.proof_state = None
    if 'theorem_name' not in st.session_state:
        st.session_state.theorem_name = "theorem"
    if 'command_history' not in st.session_state:
        st.session_state.command_history = []
    if 'saved_proofs' not in st.session_state:
        st.session_state.saved_proofs = {}
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False


init_session_state()


# ============================================================================
# Helper Functions
# ============================================================================

def get_proof_state_display() -> str:
    """Generate a formatted display of the current proof state."""
    if st.session_state.proof_state is None:
        return "No active proof. Set a goal to begin."
    
    if st.session_state.proof_state.is_complete():
        return "✅ **Proof complete!** Use the Export tab to export your proof."
    
    return str(st.session_state.proof_state)


def get_goal_type() -> str:
    """Get the type of the current goal."""
    if st.session_state.proof_state is None:
        return "none"
    
    current = st.session_state.proof_state.current()
    if current is None:
        return "complete"
    
    _, goal = current
    return goal[0] if isinstance(goal, tuple) else "unknown"


def get_context_hypotheses() -> list:
    """Get the list of hypotheses in the current context."""
    if st.session_state.proof_state is None:
        return []
    
    current = st.session_state.proof_state.current()
    if current is None:
        return []
    
    ctx, _ = current
    return ctx


def run_command(command: str) -> tuple:
    """Execute a command and return (success, message)."""
    try:
        new_state, msg = process_command(st.session_state.proof_state, command)
        st.session_state.proof_state = new_state
        
        # Record command in history
        st.session_state.command_history.append({
            'command': command,
            'timestamp': datetime.now().isoformat(),
            'success': True
        })
        
        return True, msg
    except Exception as e:
        st.session_state.command_history.append({
            'command': command,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'error': str(e)
        })
        return False, f"Error: {str(e)}"


def get_tactic_suggestions() -> list:
    """Get tactic suggestions for the current goal."""
    if st.session_state.proof_state is None:
        return []
    
    try:
        hints = tactic_hint(st.session_state.proof_state)
        return hints
    except:
        return []


# ============================================================================
# Custom CSS
# ============================================================================

def load_custom_css():
    """Load custom CSS for the application."""
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
    }
    
    /* Proof state styling */
    .proof-state {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        font-family: 'Fira Code', monospace;
    }
    
    /* Goal highlighting */
    .goal-highlight {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    
    /* Hypothesis styling */
    .hypothesis {
        background-color: #e7f3ff;
        border-radius: 0.25rem;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem 0;
        font-family: monospace;
    }
    
    /* Success message */
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        color: #155724;
    }
    
    /* Tactic buttons */
    .tactic-button {
        min-width: 100px;
    }
    
    /* Code blocks */
    .stCodeBlock {
        border-radius: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)


load_custom_css()


# ============================================================================
# Sidebar
# ============================================================================

def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        st.title("🔍 Proof Assistant")
        st.markdown("---")
        
        # Navigation
        tab = st.radio(
            "Navigation",
            ["🏠 Proof Workspace", "🛠️ Tactics", "📤 Export", "📜 History", "❓ Help"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Quick stats
        if st.session_state.proof_state is not None:
            st.subheader("📊 Statistics")
            
            col1, col2 = st.columns(2)
            with col1:
                goals = len(st.session_state.proof_state.goals)
                st.metric("Goals", goals)
            with col2:
                steps = len(st.session_state.proof_state.proof_tree.steps)
                st.metric("Steps", steps)
            
            if st.session_state.proof_state.is_complete():
                st.success("✅ Proof Complete!")
        
        st.markdown("---")
        
        # Settings
        with st.expander("⚙️ Settings"):
            st.session_state.theorem_name = st.text_input(
                "Theorem Name",
                value=st.session_state.theorem_name
            )
            
            st.session_state.dark_mode = st.checkbox(
                "Dark Mode",
                value=st.session_state.dark_mode
            )
        
        st.markdown("---")
        st.caption("Version 2.0.0")
        
        return tab


# ============================================================================
# Main Content
# ============================================================================

def render_workspace_tab():
    """Render the proof workspace tab."""
    st.header("🏠 Proof Workspace")
    
    # Goal setting section
    st.subheader("Set Initial Goal")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        goal_input = st.text_input(
            "Logical Formula",
            placeholder="forall x. P(x) -> Q(x)",
            help="Enter a logical formula using P, Q, and, or, ->, not, forall, exists"
        )
    with col2:
        st.text_input("Theorem Name", value=st.session_state.theorem_name, key="theorem_name_input")
    
    if st.button("SetBranch Goal", type="primary", use_container_width=True):
        if goal_input.strip():
            success, msg = run_command(f"goal {goal_input}")
            if success:
                st.success(msg)
            else:
                st.error(msg)
        else:
            st.warning("Please enter a formula")
    
    st.markdown("---")
    
    # Proof state display
    st.subheader("Current Proof State")
    state_display = get_proof_state_display()
    
    if "✅ Proof complete!" in state_display:
        st.success(state_display)
    elif "No active proof" in state_display:
        st.info(state_display)
    else:
        st.code(state_display, language="text")
    
    # Hypotheses display
    if st.session_state.proof_state and not st.session_state.proof_state.is_complete():
        hypotheses = get_context_hypotheses()
        if hypotheses:
            st.subheader("📋 Hypotheses")
            for name, formula in hypotheses:
                st.markdown(f"**{name}** : `{prop_repr(formula)}`")
    
    st.markdown("---")
    
    # Quick command input
    st.subheader("Command Input")
    
    command_input = st.text_input(
        "Enter Command",
        placeholder="intro H",
        key="command_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Execute", type="primary"):
            if command_input.strip():
                success, msg = run_command(command_input)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
    
    with col2:
        if st.button("Undo"):
            success, msg = run_command("undo")
            if "No actions" in msg:
                st.warning(msg)
            else:
                st.success("Undone!")
    
    # Hints
    if st.session_state.proof_state and not st.session_state.proof_state.is_complete():
        st.markdown("---")
        st.subheader("💡 Hints")
        
        with st.expander("Show hints for current goal", expanded=True):
            hints = get_tactic_suggestions()
            for hint in hints:
                st.markdown(f"- {hint}")


def render_tactics_tab():
    """Render the tactics tab with interactive buttons."""
    st.header("🛠️ Tactics")
    
    if st.session_state.proof_state is None:
        st.warning("No active proof. Set a goal first in the Proof Workspace tab.")
        return
    
    if st.session_state.proof_state.is_complete():
        st.success("✅ Proof is already complete! Visit the Export tab to export your proof.")
        return
    
    goal_type = get_goal_type()
    
    # Basic tactics
    st.subheader("Basic Tactics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("intro", help="Introduce implication or forall", use_container_width=True):
            success, msg = run_command("intro")
            st.rerun()
    
    with col2:
        if st.button("assumption", help="Solve if goal matches hypothesis", use_container_width=True):
            success, msg = run_command("assumption")
            st.rerun()
    
    with col3:
        if st.button("auto", help="Automatic proof search", use_container_width=True):
            success, msg = run_command("auto")
            st.rerun()
    
    with col4:
        if st.button("contradiction", help="Solve with contradiction", use_container_width=True):
            success, msg = run_command("contradiction")
            st.rerun()
    
    st.markdown("---")
    
    # Context-dependent tactics
    st.subheader("Goal-Specific Tactics")
    
    goal_tactics = {
        "implies": [
            ("intro", "Assume premise, prove conclusion"),
        ],
        "and": [
            ("split", "Split into two subgoals"),
        ],
        "or": [
            ("left", "Prove left disjunct"),
            ("right", "Prove right disjunct"),
        ],
        "forall": [
            ("intro", "Introduce variable"),
        ],
        "exists": [
            ("exists_intro", "Provide witness"),
        ],
        "not": [
            ("not_intro", "Assume P, prove ⊥"),
        ],
    }
    
    if goal_type in goal_tactics:
        tactics = goal_tactics[goal_type]
        cols = st.columns(len(tactics))
        
        for i, (tactic, help_text) in enumerate(tactics):
            with cols[i]:
                if tactic == "exists_intro":
                    witness = st.text_input("Witness", key="witness_input")
                    if st.button(tactic, help=help_text, use_container_width=True):
                        if witness:
                            success, msg = run_command(f"exists_intro {witness}")
                            st.rerun()
                else:
                    if st.button(tactic, help=help_text, use_container_width=True):
                        success, msg = run_command(tactic)
                        st.rerun()
    else:
        st.info(f"No specific tactics for goal type: {goal_type}")
    
    st.markdown("---")
    
    # Hypothesis-based tactics
    hypotheses = get_context_hypotheses()
    if hypotheses:
        st.subheader("Hypothesis Tactics")
        
        for name, formula in hypotheses:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
                
                with col1:
                    st.code(name, language=None)
                
                with col2:
                    st.code(prop_repr(formula), language=None)
                
                formula_type = formula[0] if isinstance(formula, tuple) else "unknown"
                
                with col3:
                    if st.button("exact", key=f"exact_{name}", help=f"Use {name} to solve goal"):
                        success, msg = run_command(f"exact {name}")
                        st.rerun()
                
                with col4:
                    if formula_type in ["and", "or", "exists"]:
                        if st.button("destruct", key=f"destruct_{name}", help=f"Case analysis on {name}"):
                            success, msg = run_command(f"destruct {name}")
                            st.rerun()
                
                with col5:
                    if formula_type == "implies":
                        if st.button("apply", key=f"apply_{name}", help=f"Apply {name}"):
                            success, msg = run_command(f"apply {name}")
                            st.rerun()
    
    st.markdown("---")
    
    # Navigation
    st.subheader("Navigation")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("↩️ Undo Last Step", use_container_width=True):
            success, msg = run_command("undo")
            st.rerun()
    
    with col2:
        if st.button("↪️ Redo", use_container_width=True):
            success, msg = run_command("redo")
            st.rerun()


def render_export_tab():
    """Render the export tab."""
    st.header("📤 Export Proof")
    
    if st.session_state.proof_state is None:
        st.warning("No active proof to export.")
        return
    
    proof_tree = st.session_state.proof_state.proof_tree
    
    if not proof_tree.initial_goal:
        st.warning("No initial goal set. Set a goal first.")
        return
    
    # Export options
    st.subheader("Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_system = st.selectbox(
            "Target System",
            ["All", "Coq", "Isabelle", "Lean"],
            help="Choose which theorem prover to export to"
        )
    
    with col2:
        export_dir = st.text_input(
            "Export Directory",
            value="exports",
            help="Directory to save exported files"
        )
    
    # Set theorem name
    proof_tree.theorem_name = st.session_state.theorem_name
    
    if st.button("Export Proof", type="primary", use_container_width=True):
        try:
            if export_system == "All":
                exports = proof_tree.export_all(export_dir)
                st.success("Exported to all theorem provers!")
                
                for system, code in exports.items():
                    if code:
                        with st.expander(f"{system.upper()} Code", expanded=False):
                            lang = "coq" if system == "coq" else "isabelle" if system == "isabelle" else "lean"
                            st.code(code, language=lang)
            else:
                if export_system == "Coq":
                    code = proof_tree.export_coq()
                    lang = "coq"
                    ext = "v"
                elif export_system == "Isabelle":
                    code = proof_tree.export_isabelle()
                    lang = "isabelle"
                    ext = "thy"
                elif export_system == "Lean":
                    code = proof_tree.export_lean()
                    lang = "lean"
                    ext = "lean"
                
                if code:
                    st.success(f"Generated {export_system} code!")
                    st.code(code, language=lang)
                    
                    # Download button
                    filename = f"{st.session_state.theorem_name.lower()}.{ext}"
                    st.download_button(
                        label=f"Download {export_system} file",
                        data=code,
                        file_name=filename,
                        mime="text/plain"
                    )
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
    
    st.markdown("---")
    
    # Proof summary
    st.subheader("Proof Summary")
    
    if proof_tree.steps:
        for i, step in enumerate(proof_tree.steps):
            status = "✅" if step.success else "❌"
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown(f"**Step {i+1}** {status}")
                with col2:
                    st.code(f"{step.tactic_name} {' '.join(str(a) for a in step.arguments)}", language=None)
    else:
        st.info("No proof steps recorded yet.")


def render_history_tab():
    """Render the command history tab."""
    st.header("📜 History")
    
    if not st.session_state.command_history:
        st.info("No commands executed yet.")
        return
    
    # Command history
    st.subheader("Recent Commands")
    
    for i, entry in enumerate(reversed(st.session_state.command_history[-20:])):
        status = "✅" if entry.get('success', True) else "❌"
        timestamp = entry.get('timestamp', '')[:19]
        command = entry.get('command', '')
        
        with st.container():
            col1, col2, col3 = st.columns([1, 4, 2])
            with col1:
                st.markdown(status)
            with col2:
                st.code(command, language=None)
            with col3:
                st.caption(timestamp)
    
    st.markdown("---")
    
    # Full proof script
    st.subheader("Full Proof Script")
    
    script_lines = []
    script_lines.append(f"# Theorem: {st.session_state.theorem_name}")
    script_lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    script_lines.append("")
    
    for entry in st.session_state.command_history:
        cmd = entry.get('command', '')
        if not cmd.startswith(('state', 'context', 'hint', 'explain', 'help')):
            script_lines.append(cmd)
    
    script_content = "\n".join(script_lines)
    st.code(script_content, language="bash")
    
    # Download button
    st.download_button(
        label="Download Proof Script",
        data=script_content,
        file_name=f"{st.session_state.theorem_name.lower()}_proof.txt",
        mime="text/plain"
    )
    
    # Clear history button
    if st.button("Clear History"):
        st.session_state.command_history = []
        st.rerun()


def render_help_tab():
    """Render the help tab."""
    st.header("❓ Help")
    
    # Syntax reference
    st.subheader("Syntax Reference")
    
    with st.expander("Logical Connectives", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            | Connective | Symbol | ASCII |
            |------------|--------|-------|
            | And | ∧ | `and`, `&&` |
            | Or | ∨ | `or`, \|\| |
            | Implies | → | `->`, `=>` |
            | Not | ¬ | `not`, `~` |
            | Iff | ↔ | `<=>` |
            """)
        with col2:
            st.markdown("""
            | Quantifier | Symbol | ASCII |
            |------------|--------|-------|
            | Forall | ∀ | `forall` |
            | Exists | ∃ | `exists` |
            | Bottom | ⊥ | `False`, `false` |
            | Equality | = | `=` |
            """)
    
    with st.expander("Examples", expanded=True):
        st.markdown("""
        - `P -> Q` : Implication
        - `P and Q` : Conjunction
        - `P or Q` : Disjunction
        - `not P` : Negation
        - `forall x. P(x)` : Universal quantification
        - `exists x. P(x)` : Existential quantification
        - `P(x) -> Q(x)` : Predicate implication
        - `forall x. exists y. R(x, y)` : Nested quantifiers
        - `P and Q -> P` : Simple theorem
        """)
    
    st.markdown("---")
    
    # Tactics reference
    st.subheader("Tactics Reference")
    
    tactics_help = [
        ("intro", "Introduce an implication or universal quantifier"),
        ("exact H", "Solve goal with hypothesis H"),
        ("assumption", "Solve goal if it matches any hypothesis"),
        ("split", "Split conjunction goal into two subgoals"),
        ("destruct H", "Case analysis on hypothesis H"),
        ("left", "Solve disjunction by proving left side"),
        ("right", "Solve disjunction by proving right side"),
        ("exists_intro t", "Provide witness t for existential"),
        ("contradiction", "Solve goal when contradiction found"),
        ("reflexivity", "Solve reflexive equality t = t"),
        ("apply H", "Apply implication hypothesis H"),
        ("auto", "Automatic proof search"),
        ("undo", "Undo last tactic"),
        ("redo", "Redo last undone tactic"),
    ]
    
    for tactic, description in tactics_help:
        st.markdown(f"**`{tactic}`** : {description}")
    
    st.markdown("---")
    
    # Tutorial
    st.subheader("Quick Tutorial")
    
    with st.expander("Proving P → P (Identity)"):
        st.markdown("""
        1. Set goal: `goal P -> P`
        2. Introduce hypothesis: `intro H`
        3. Use hypothesis: `exact H`
        4. Proof complete!
        """)
    
    with st.expander("Proving P ∧ Q → P (And Elimination)"):
        st.markdown("""
        1. Set goal: `goal P and Q -> P`
        2. Introduce hypothesis: `intro H`
        3. Destruct conjunction: `destruct H`
        4. Use left part: `exact H_left`
        5. Proof complete!
        """)
    
    with st.expander("Proving P → P ∨ Q (Or Introduction)"):
        st.markdown("""
        1. Set goal: `goal P -> P or Q`
        2. Introduce hypothesis: `intro H`
        3. Choose left side: `left`
        4. Use hypothesis: `exact H`
        5. Proof complete!
        """)


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point."""
    tab = render_sidebar()
    
    if tab == "🏠 Proof Workspace":
        render_workspace_tab()
    elif tab == "🛠️ Tactics":
        render_tactics_tab()
    elif tab == "📤 Export":
        render_export_tab()
    elif tab == "📜 History":
        render_history_tab()
    elif tab == "❓ Help":
        render_help_tab()


if __name__ == "__main__":
    main()
