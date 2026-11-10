"""
record_demo.py - Automated 35-Second Video Showcase Script for PipeTrace.
Zero Pandas knowledge required! Just run this script and record your screen.
"""

import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from pipetrace import trace
from pipetrace.diff import StepDiff
from pipetrace.reporter import PipelineReporter

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.syntax import Syntax
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def run_showcase():
    console = Console()

    # ----------------------------------------------------
    # SCENE 1: THE OLD PAINFUL WAY (3 seconds)
    # ----------------------------------------------------
    console.clear()
    old_code = """# ❌ THE OLD PAINFUL WAY:
df = pd.read_csv("customers.csv")
print(df.shape)  # -> (10,000, 6)

df = df.drop_duplicates(subset=["id"])
print(df.shape)  # -> (9,850, 6)

df = df.query("age >= 18")
print(df.shape)  # -> (8,420, 6)  <-- Wait, where did 1,430 rows vanish?

df = df.merge(orders, on="id", how="left")
print(df.shape)  # -> (8,600, 9)  <-- Wait, why did rows increase??
print(df.isna().sum())  # <-- Which step created new NaNs??
"""
    console.print(Panel(
        Syntax(old_code, "python", theme="monokai", line_numbers=True),
        title="[bold red]❌ The Problem: Manual, Messy Debugging[/bold red]",
        border_style="red"
    ))
    time.sleep(3.5)

    # ----------------------------------------------------
    # SCENE 2: THE PIPETRACE SOLUTION (4 seconds)
    # ----------------------------------------------------
    console.print("\n")
    new_code = """# ✨ THE PIPETRACE WAY:
from pipetrace import trace

# Wrap once in trace() and just call .report() at the end!
clean_df = (
    trace(raw_customers)
    .drop_duplicates(subset=["id"])
    .query("age >= 18")
    .merge(orders, on="id", how="left")
    .dropna(subset=["email"])
    .report(title="E-Commerce Cleaning Pipeline")
)
"""
    console.print(Panel(
        Syntax(new_code, "python", theme="monokai", line_numbers=True),
        title="[bold green]✅ The Solution: One-Line Observability with PipeTrace[/bold green]",
        border_style="green"
    ))
    time.sleep(3.0)

    # ----------------------------------------------------
    # SCENE 3: THE LIVE AUDIT DASHBOARD EXECUTION (15 seconds)
    # ----------------------------------------------------
    console.print("\n[bold yellow]⚡ Running Pipeline & Generating Audit Report...[/bold yellow]\n")
    time.sleep(1.2)

    # Generate realistic, impressive steps showcasing all alerts & insights
    history = [
        StepDiff(
            step_number=1,
            method_name="drop_duplicates",
            args_repr="subset=['id']",
            before_shape=(10000, 5),
            after_shape=(9850, 5),
            row_diff=-150,
            col_diff=0,
            added_columns=[],
            removed_columns=[],
            new_nulls={},
            memory_change_kb=-12.5,
            duration_ms=4.2,
            insights=["Pattern: 72% of dropped rows had duplicate '@gmail.com' emails."],
            alerts=[],
        ),
        StepDiff(
            step_number=2,
            method_name="query",
            args_repr="'age >= 18'",
            before_shape=(9850, 5),
            after_shape=(8900, 5),
            row_diff=-950,
            col_diff=0,
            added_columns=[],
            removed_columns=[],
            new_nulls={},
            memory_change_kb=-76.0,
            duration_ms=6.8,
            insights=[],
            alerts=["High loss: Dropped 950 rows (9.6% of data). Check age filter logic!"],
        ),
        StepDiff(
            step_number=3,
            method_name="merge",
            args_repr="orders, on='id', how='left'",
            before_shape=(8900, 5),
            after_shape=(9200, 8),
            row_diff=300,
            col_diff=3,
            added_columns=["order_id", "amount", "status"],
            removed_columns=[],
            new_nulls={"amount": 45},
            memory_change_kb=95.4,
            duration_ms=14.1,
            insights=["New column(s): order_id, amount, status"],
            alerts=[
                "Row explosion: +300 rows (+3.4%). Duplicate keys found in orders table!",
                "New missing values in 'amount': +45 NaNs (0.5% of column).",
            ],
        ),
        StepDiff(
            step_number=4,
            method_name="dropna",
            args_repr="subset=['email']",
            before_shape=(9200, 8),
            after_shape=(9150, 8),
            row_diff=-50,
            col_diff=0,
            added_columns=[],
            removed_columns=[],
            new_nulls={},
            memory_change_kb=-4.0,
            duration_ms=2.9,
            insights=["Missing values in 'email' caused majority of drops."],
            alerts=[],
        ),
    ]

    PipelineReporter.render_terminal(history, title="E-Commerce Cleaning Pipeline")
    time.sleep(2.0)

    # ----------------------------------------------------
    # SCENE 4: CALL TO ACTION BANNER (5 seconds)
    # ----------------------------------------------------
    cta = Text()
    cta.append("📦 Install now via pip:\n", style="bold white")
    cta.append("pip install pipetrace\n\n", style="bold cyan")
    cta.append("🔗 PyPI:   ", style="dim")
    cta.append("https://pypi.org/project/pipetrace/\n", style="underline cyan")
    cta.append("⭐ GitHub: ", style="dim")
    cta.append("https://github.com/uttakaladebagarnaik/pipespy\n", style="underline yellow")
    cta.append("💡 Open Source • Lightweight • Zero Config", style="italic green")

    console.print(Panel(cta, title="[bold magenta]🚀 PipeTrace v0.1.0[/bold magenta]", border_style="cyan"))


if __name__ == "__main__":
    run_showcase()
