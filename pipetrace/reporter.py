"""
reporter.py - Visual formatting and rendering of pipeline audit reports.
"""

from typing import Any, List
from pipetrace.diff import StepDiff

try:
    import pandas as pd
    HAS_PANDAS = True
except Exception:
    HAS_PANDAS = False

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class PipelineReporter:
    """Renders the execution history and step insights into rich terminal or text formats."""

    @staticmethod
    def render_terminal(history: List[StepDiff], title: str = "PipeTrace Pipeline Audit"):
        """Render beautiful terminal report using Rich if available, else plain text."""
        if not history:
            print("No transformation steps recorded.")
            return

        if HAS_RICH:
            PipelineReporter._render_rich(history, title)
        else:
            PipelineReporter._render_plain(history, title)

    @staticmethod
    def _render_rich(history: List[StepDiff], title: str):
        console = Console()
        initial_shape = history[0].before_shape
        final_shape = history[-1].after_shape
        total_time_ms = sum(s.duration_ms for s in history)
        total_row_diff = final_shape[0] - initial_shape[0]

        # Header Banner
        banner_text = Text()
        banner_text.append("🔍 PipeTrace Data Audit & Insights\n", style="bold cyan")
        banner_text.append(f"Initial: {initial_shape[0]:,} rows × {initial_shape[1]} cols  ➔  ", style="dim")
        banner_text.append(f"Final: {final_shape[0]:,} rows × {final_shape[1]} cols\n", style="bold green")

        row_color = "red" if total_row_diff < 0 else ("yellow" if total_row_diff > 0 else "green")
        sign = "+" if total_row_diff > 0 else ""
        banner_text.append(f"Net Row Change: {sign}{total_row_diff:,} rows | Total Time: {total_time_ms:.1f}ms", style=row_color)

        console.print(Panel(banner_text, title=f"⚡ {title}", border_style="cyan"))

        # Step-by-Step Table
        table = Table(title="Pipeline Step-by-Step Execution", border_style="dim", header_style="bold magenta")
        table.add_column("#", style="dim", justify="center")
        table.add_column("Operation", style="bold white")
        table.add_column("Rows", justify="right")
        table.add_column("Cols", justify="center")
        table.add_column("Time", justify="right")
        table.add_column("Insights & Alerts", style="white")

        for s in history:
            op_str = f".{s.method_name}({s.args_repr})"
            if len(op_str) > 28:
                op_str = op_str[:25] + "..."

            if s.row_diff < 0:
                row_str = f"{s.after_shape[0]:,} [red]({s.row_diff:,})[/red]"
            elif s.row_diff > 0:
                row_str = f"{s.after_shape[0]:,} [green](+{s.row_diff:,})[/green]"
            else:
                row_str = f"{s.after_shape[0]:,} [dim](=)[/dim]"

            col_str = f"{s.after_shape[1]}"
            if s.col_diff != 0:
                col_sign = "+" if s.col_diff > 0 else ""
                col_str += f" ({col_sign}{s.col_diff})"

            notes = []
            for a in s.alerts:
                notes.append(f"[bold red]⚠️  {a}[/bold red]")
            for i in s.insights:
                notes.append(f"[cyan]💡 {i}[/cyan]")

            notes_str = "\n".join(notes) if notes else "[dim]Clean execution[/dim]"

            table.add_row(
                str(s.step_number),
                op_str,
                row_str,
                col_str,
                f"{s.duration_ms:.1f}ms",
                notes_str,
            )

        console.print(table)
        console.print()

    @staticmethod
    def _render_plain(history: List[StepDiff], title: str):
        print(f"=== {title} ===")
        for s in history:
            sign = "+" if s.row_diff > 0 else ""
            print(f"[{s.step_number}] .{s.method_name}({s.args_repr})")
            print(f"    Rows: {s.before_shape[0]} -> {s.after_shape[0]} ({sign}{s.row_diff}) | Time: {s.duration_ms:.1f}ms")
            for a in s.alerts:
                print(f"    [ALERT] {a}")
            for i in s.insights:
                print(f"    [INSIGHT] {i}")
        print("=" * 40)

    @staticmethod
    def to_dataframe(history: List[StepDiff]) -> Any:
        """Convert step history into a pandas DataFrame or list of dicts."""
        rows = []
        for s in history:
            rows.append({
                "step": s.step_number,
                "operation": s.method_name,
                "args": s.args_repr,
                "rows_before": s.before_shape[0],
                "rows_after": s.after_shape[0],
                "row_diff": s.row_diff,
                "cols_before": s.before_shape[1],
                "cols_after": s.after_shape[1],
                "duration_ms": round(s.duration_ms, 2),
                "alerts": "; ".join(s.alerts),
                "insights": "; ".join(s.insights),
            })
        if HAS_PANDAS:
            return pd.DataFrame(rows)
        return rows
