"""
tracker.py - Core Lens proxy for intercepting and tracking DataFrame operations.
"""

import time
from typing import Any, Callable, List, Optional

from pipespy.diff import take_snapshot, compute_diff, is_dataframe, StepDiff
from pipespy.insights import InsightEngine
from pipespy.reporter import PipelineReporter


class Lens:
    """Transparent proxy wrapping a pandas/tabular DataFrame to track pipeline transformations."""

    def __init__(
        self,
        df: Any,
        history: Optional[List[StepDiff]] = None,
        live: bool = False,
    ):
        if not is_dataframe(df):
            raise TypeError(f"PipeSpy expects a DataFrame-like object with shape and columns, got {type(df).__name__}")

        # Use object.__setattr__ to avoid triggering custom __setattr__
        object.__setattr__(self, "_df", df)
        object.__setattr__(self, "_history", history or [])
        object.__setattr__(self, "_live", live)

    @property
    def df(self) -> Any:
        """Access the underlying DataFrame."""
        return self._df

    def to_df(self) -> Any:
        """Return the underlying DataFrame."""
        return self._df

    @property
    def history(self) -> List[StepDiff]:
        """Return the list of recorded step differences."""
        return list(self._history)

    def summary(self) -> Any:
        """Return a summary of all pipeline steps."""
        return PipelineReporter.to_dataframe(self._history)

    def report(self, title: str = "PipeSpy Pipeline Audit", return_df: bool = True) -> Any:
        """
        Render the visual audit report.
        If return_df=True (default), returns the clean DataFrame for smooth chaining.
        """
        PipelineReporter.render_terminal(self._history, title=title)
        return self._df if return_df else self

    def pipe(self, func: Callable, *args, **kwargs) -> Any:
        """Intercept df.pipe() to monitor custom transformation functions."""
        func_name = getattr(func, "__name__", "custom_function")
        return self._execute_and_track(func_name, func, self._df, *args, **kwargs)

    def _execute_and_track(self, method_name: str, func: Callable, *args, **kwargs) -> Any:
        """Executes the dataframe operation and logs the before/after state diff."""
        start_time = time.perf_counter()
        before_snap = take_snapshot(self._df)

        result = func(*args, **kwargs)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        if is_dataframe(result):
            after_snap = take_snapshot(result)
            step_num = len(self._history) + 1

            diff = compute_diff(
                before_df=self._df,
                after_df=result,
                before_snap=before_snap,
                after_snap=after_snap,
                method_name=method_name,
                args=args,
                kwargs=kwargs,
                duration_ms=duration_ms,
                step_number=step_num,
            )

            insights, alerts = InsightEngine.generate(
                before_df=self._df,
                after_df=result,
                before_snap=before_snap,
                after_snap=after_snap,
                diff=diff,
            )
            diff.insights = insights
            diff.alerts = alerts

            if self._live:
                sign = "+" if diff.row_diff > 0 else ""
                print(f"[PipeSpy Live] Step {step_num}: .{method_name}() -> Rows: {after_snap.shape[0]} ({sign}{diff.row_diff})")

            new_history = list(self._history) + [diff]
            return Lens(result, history=new_history, live=self._live)

        # If operation returns a Series, scalar, or None, return as is
        return result

    def __getitem__(self, item: Any) -> Any:
        """Intercept indexing and boolean slicing like df[df['col'] > 0]"""
        def slice_operation(df, key):
            return df[key]

        return self._execute_and_track("__getitem__", slice_operation, self._df, item)

    def __getattr__(self, name: str) -> Any:
        """Intercept any DataFrame method call."""
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        if not hasattr(self._df, name):
            raise AttributeError(f"Neither Lens nor DataFrame has attribute '{name}'")

        attr = getattr(self._df, name)

        if callable(attr):
            def wrapper(*args, **kwargs):
                return self._execute_and_track(name, attr, *args, **kwargs)
            return wrapper

        return attr

    def __len__(self) -> int:
        if hasattr(self._df, "__len__"):
            try:
                return len(self._df)
            except TypeError:
                pass
        if hasattr(self._df, "shape") and isinstance(self._df.shape, tuple):
            return self._df.shape[0]
        return 0

    def __repr__(self) -> str:
        return f"<PipeSpy [Steps: {len(self._history)}] wrapping DataFrame:\n{repr(self._df)}>"

    def _repr_html_(self) -> str:
        """Rich HTML display for Jupyter Notebooks."""
        summary_obj = self.summary()
        summary_html = summary_obj.to_html(classes="pipespy-table", index=False) if hasattr(summary_obj, "to_html") else str(summary_obj)
        preview_html = self._df.head(5)._repr_html_() if hasattr(self._df, "head") and hasattr(self._df.head(5), "_repr_html_") else f"<pre>{str(self._df)[:400]}</pre>"
        return f"""
        <div style="border: 2px solid #00acc1; border-radius: 8px; padding: 12px; margin: 8px 0; font-family: sans-serif;">
            <h4 style="margin: 0 0 8px 0; color: #00838f;">🕵️ PipeSpy Audit History ({len(self._history)} steps)</h4>
            {summary_html}
            <details style="margin-top: 10px;">
                <summary style="cursor: pointer; color: #555;">View Current DataFrame Preview</summary>
                <div style="margin-top: 8px;">{preview_html}</div>
            </details>
        </div>
        """


Spy = Lens


def watch(df: Any, live: bool = False) -> Lens:
    """Convenience factory function: pipespy.watch(df) or pipespy.Spy(df)"""
    return Lens(df, live=live)
