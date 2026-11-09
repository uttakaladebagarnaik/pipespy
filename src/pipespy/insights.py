"""
insights.py - Heuristic story and anomaly generator for pipeline transitions.
"""

from typing import Any, List, Tuple
from pipespy.diff import StepDiff, DataSnapshot

try:
    import pandas as pd
    HAS_PANDAS = True
except Exception:
    HAS_PANDAS = False


class InsightEngine:
    """Analyzes differences between pipeline steps and generates human-friendly insights."""

    @staticmethod
    def generate(
        before_df: Any,
        after_df: Any,
        before_snap: DataSnapshot,
        after_snap: DataSnapshot,
        diff: StepDiff,
    ) -> Tuple[List[str], List[str]]:
        """Returns a tuple of (insights, alerts)."""
        insights: List[str] = []
        alerts: List[str] = []

        before_rows, _ = before_snap.shape
        after_rows, _ = after_snap.shape

        # 1. Critical: Empty Dataframe Alert
        if after_rows == 0 and before_rows > 0:
            alerts.append("CRITICAL: DataFrame became completely empty (0 rows) after this step!")
            return insights, alerts

        # 2. Row Reduction / Filtering Insights
        if diff.row_diff < 0:
            abs_drop = abs(diff.row_diff)
            pct_drop = abs(diff.row_change_pct)

            if pct_drop >= 50.0:
                alerts.append(f"High loss: Dropped {abs_drop:,} rows ({pct_drop:.1f}% of data).")

            # Try to identify why rows were dropped if index difference is valid
            try:
                if before_df is not None and after_df is not None and hasattr(before_df, "index") and hasattr(after_df, "index"):
                    dropped_indices = before_df.index.difference(after_df.index)
                    if len(dropped_indices) > 0 and hasattr(before_df, "loc"):
                        dropped_slice = before_df.loc[dropped_indices]

                        # Check for dominant categorical values among dropped records
                        pattern_found = False
                        for col in dropped_slice.columns:
                            col_series = dropped_slice[col]
                            if hasattr(col_series, "dtype") and (col_series.dtype == "object" or col_series.dtype.name == "category"):
                                val_counts = col_series.value_counts(dropna=False)
                                if not val_counts.empty:
                                    top_val = val_counts.index[0]
                                    top_freq = val_counts.iloc[0]
                                    top_pct = (top_freq / len(dropped_slice)) * 100
                                    if top_pct >= 40.0:
                                        insights.append(
                                            f"Pattern: {top_pct:.0f}% of dropped rows had '{col}' == '{top_val}'."
                                        )
                                        pattern_found = True
                                        break
                        if not pattern_found and diff.method_name in ("dropna", "drop_na"):
                            nan_counts = dropped_slice.isna().sum().sort_values(ascending=False)
                            if not nan_counts.empty and nan_counts.iloc[0] > 0:
                                top_col = nan_counts.index[0]
                                insights.append(
                                    f"Missing values in '{top_col}' caused majority of drops."
                                )
            except Exception:
                pass

        # 3. Row Expansion (Merge / Cartesian explosions)
        elif diff.row_diff > 0:
            pct_gain = diff.row_change_pct
            if diff.method_name in ("merge", "join"):
                alerts.append(
                    f"Row explosion: +{diff.row_diff:,} rows (+{pct_gain:.1f}%). Check for duplicate keys in join!"
                )
            else:
                insights.append(f"Added +{diff.row_diff:,} new rows (+{pct_gain:.1f}%).")

        # 4. Null / Missing Values introduced
        if diff.new_nulls:
            for col, count in diff.new_nulls.items():
                if after_rows > 0:
                    pct = (count / after_rows) * 100.0
                    alerts.append(
                        f"New missing values in '{col}': +{count:,} NaNs ({pct:.1f}% of column)."
                    )

        # 5. Type Mutations (e.g., int -> float due to nulls)
        for col in after_snap.columns:
            if col in before_snap.columns:
                old_dtype = before_snap.dtypes.get(col, "")
                new_dtype = after_snap.dtypes.get(col, "")
                if old_dtype != new_dtype and old_dtype and new_dtype:
                    if "int" in old_dtype and "float" in new_dtype:
                        insights.append(
                            f"Type shift: '{col}' converted from {old_dtype} to {new_dtype} (likely due to NaNs)."
                        )
                    else:
                        insights.append(f"Type changed: '{col}' from {old_dtype} to {new_dtype}.")

        # 6. Column additions / drops
        if diff.added_columns:
            insights.append(f"New column(s): {', '.join(diff.added_columns)}")
        if diff.removed_columns:
            insights.append(f"Removed column(s): {', '.join(diff.removed_columns)}")

        # 7. No structural change
        if diff.row_diff == 0 and diff.col_diff == 0 and not diff.new_nulls and not insights and not alerts:
            insights.append("Operation applied cleanly without altering row/column count.")

        return insights, alerts
