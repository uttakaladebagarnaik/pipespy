"""
diff.py - Snapshot and difference calculation for DataFrame transformations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

try:
    import pandas as pd
    HAS_PANDAS = True
except Exception:
    HAS_PANDAS = False


@dataclass
class DataSnapshot:
    shape: Tuple[int, int]
    columns: List[str]
    dtypes: Dict[str, str]
    null_counts: Dict[str, int]
    memory_bytes: int


def is_dataframe(obj: Any) -> bool:
    """Check if an object behaves like a DataFrame (duck-typing or pandas instance)."""
    if HAS_PANDAS and isinstance(obj, pd.DataFrame):
        return True
    return hasattr(obj, "shape") and hasattr(obj, "columns") and isinstance(getattr(obj, "shape", None), tuple)


def take_snapshot(df: Any) -> DataSnapshot:
    """Take a lightweight snapshot of the DataFrame state."""
    if not is_dataframe(df):
        raise TypeError(f"Expected DataFrame-like object with shape and columns, got {type(df).__name__}")

    shape = getattr(df, "shape", (0, 0))
    columns = [str(c) for c in getattr(df, "columns", [])]

    # Handle dtypes
    dtypes: Dict[str, str] = {}
    if hasattr(df, "dtypes"):
        try:
            dtypes = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
        except Exception:
            dtypes = {c: "unknown" for c in columns}
    else:
        dtypes = {c: "unknown" for c in columns}

    # Handle null counts
    null_counts: Dict[str, int] = {}
    try:
        if hasattr(df, "isna") or hasattr(df, "isnull"):
            na_checker = getattr(df, "isna", getattr(df, "isnull", None))
            res = na_checker()
            if hasattr(res, "sum"):
                null_sum = res.sum()
                if hasattr(null_sum, "items"):
                    null_counts = {str(col): int(val) for col, val in null_sum.items()}
                elif isinstance(null_sum, dict):
                    null_counts = {str(col): int(val) for col, val in null_sum.items()}
            elif hasattr(res, "items"):
                null_counts = {str(col): int(val) for col, val in res.items()}
    except Exception:
        pass

    # Ensure all columns exist in null_counts
    for c in columns:
        if c not in null_counts:
            null_counts[c] = 0

    # Handle memory usage
    try:
        if hasattr(df, "memory_usage"):
            mem = int(df.memory_usage(deep=False).sum())
        else:
            mem = 0
    except Exception:
        mem = 0

    return DataSnapshot(
        shape=shape,
        columns=columns,
        dtypes=dtypes,
        null_counts=null_counts,
        memory_bytes=mem,
    )


@dataclass
class StepDiff:
    step_number: int
    method_name: str
    args_repr: str
    before_shape: Tuple[int, int]
    after_shape: Tuple[int, int]
    row_diff: int
    col_diff: int
    added_columns: List[str]
    removed_columns: List[str]
    new_nulls: Dict[str, int]
    memory_change_kb: float
    duration_ms: float
    insights: List[str] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)

    @property
    def row_change_pct(self) -> float:
        if self.before_shape[0] == 0:
            return 0.0
        return (self.row_diff / self.before_shape[0]) * 100.0


def compute_diff(
    before_df: Any,
    after_df: Any,
    before_snap: DataSnapshot,
    after_snap: DataSnapshot,
    method_name: str,
    args: tuple,
    kwargs: dict,
    duration_ms: float,
    step_number: int,
) -> StepDiff:
    """Compute structural and statistical diff between two dataframe states."""
    row_diff = after_snap.shape[0] - before_snap.shape[0]
    col_diff = after_snap.shape[1] - before_snap.shape[1]

    added_columns = [c for c in after_snap.columns if c not in before_snap.columns]
    removed_columns = [c for c in before_snap.columns if c not in after_snap.columns]

    new_nulls: Dict[str, int] = {}
    for col in after_snap.columns:
        if col in before_snap.columns:
            delta_null = after_snap.null_counts.get(col, 0) - before_snap.null_counts.get(col, 0)
            if delta_null > 0:
                new_nulls[col] = delta_null

    memory_change_kb = (after_snap.memory_bytes - before_snap.memory_bytes) / 1024.0

    # Format arguments representation cleanly
    arg_strings = [repr(a) for a in args]
    kwarg_strings = [f"{k}={repr(v)}" for k, v in kwargs.items()]
    all_args = ", ".join(arg_strings + kwarg_strings)
    if len(all_args) > 60:
        all_args = all_args[:57] + "..."

    return StepDiff(
        step_number=step_number,
        method_name=method_name,
        args_repr=all_args,
        before_shape=before_snap.shape,
        after_shape=after_snap.shape,
        row_diff=row_diff,
        col_diff=col_diff,
        added_columns=added_columns,
        removed_columns=removed_columns,
        new_nulls=new_nulls,
        memory_change_kb=memory_change_kb,
        duration_ms=duration_ms,
    )
