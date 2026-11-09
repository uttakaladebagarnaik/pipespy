"""
test_pipespy.py - Comprehensive Unit test suite for PipeSpy.
"""

import pytest
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pipespy import Lens, watch, Spy, StepDiff, DataSnapshot
from pipespy.diff import take_snapshot, compute_diff, is_dataframe
from pipespy.insights import InsightEngine
from pipespy.reporter import PipelineReporter


class MockSeries:
    """Mock Series for testing value counts and sum."""
    def __init__(self, data: dict):
        self._data = data

    def sum(self):
        return sum(self._data.values())

    def items(self):
        return self._data.items()


class MockDataFrame:
    """A duck-typed DataFrame emulator for running robust unit tests."""
    def __init__(self, data: dict):
        self._data = {k: list(v) for k, v in data.items()}
        self._cols = list(data.keys())
        first_col = self._cols[0] if self._cols else ""
        self._row_count = len(self._data[first_col]) if first_col else 0

    @property
    def shape(self):
        return (self._row_count, len(self._cols))

    @property
    def columns(self):
        return list(self._cols)

    @property
    def dtypes(self):
        return {c: "int64" if all(isinstance(x, int) for x in self._data[c] if x is not None) else "object" for c in self._cols}

    def __len__(self):
        return self._row_count

    def isna(self):
        null_counts = {c: sum(1 for x in self._data[c] if x is None) for c in self._cols}
        class NullResult:
            def sum(self_nr):
                return MockSeries(null_counts)
        return NullResult()

    def isnull(self):
        return self.isna()

    def memory_usage(self, deep=False):
        return MockSeries({c: self._row_count * 8 for c in self._cols})

    def drop_duplicates(self, subset=None):
        cols_to_check = subset if subset else self._cols
        seen = set()
        filtered_indices = []
        for i in range(self._row_count):
            key = tuple(self._data[col][i] for col in cols_to_check)
            if key not in seen:
                seen.add(key)
                filtered_indices.append(i)
        new_data = {c: [self._data[c][i] for i in filtered_indices] for c in self._cols}
        return MockDataFrame(new_data)

    def query(self, expr: str):
        filtered_indices = []
        for i in range(self._row_count):
            row_dict = {col: self._data[col][i] for col in self._cols}
            try:
                if eval(expr, {}, row_dict):
                    filtered_indices.append(i)
            except Exception:
                pass
        new_data = {c: [self._data[c][i] for i in filtered_indices] for c in self._cols}
        return MockDataFrame(new_data)

    def dropna(self, subset=None):
        cols_to_check = subset if subset else self._cols
        filtered_indices = []
        for i in range(self._row_count):
            has_na = any(self._data[col][i] is None for col in cols_to_check)
            if not has_na:
                filtered_indices.append(i)
        new_data = {c: [self._data[c][i] for i in filtered_indices] for c in self._cols}
        return MockDataFrame(new_data)

    def assign(self, **kwargs):
        new_data = dict(self._data)
        for k, v in kwargs.items():
            if callable(v):
                new_data[k] = [v(self)] * self._row_count
            else:
                new_data[k] = [v] * self._row_count
        return MockDataFrame(new_data)

    def scalar_stat(self):
        return 42

    def __getitem__(self, item):
        new_data = {c: self._data[c][: max(1, self._row_count - 1)] for c in self._cols}
        return MockDataFrame(new_data)


def test_is_dataframe():
    df = MockDataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})
    assert is_dataframe(df) is True
    assert is_dataframe([1, 2, 3]) is False
    assert is_dataframe("not a df") is False


def test_invalid_type_raises():
    with pytest.raises(TypeError, match="PipeSpy expects a DataFrame-like object"):
        Lens("invalid string")


def test_take_snapshot():
    df = MockDataFrame({"id": [1, 2, 3], "score": [10, None, 30]})
    snap = take_snapshot(df)
    assert snap.shape == (3, 2)
    assert snap.columns == ["id", "score"]
    assert snap.null_counts["score"] == 1
    assert snap.null_counts["id"] == 0


def test_lens_proxy_wrapping_and_chaining():
    df = MockDataFrame({"id": [1, 2, 3, 4, 5, 6, 7, 8], "name": ["A", "B", "C", "D", "E", "F", "G", "H"]})
    lens = watch(df)

    assert len(lens) == 8
    assert len(lens.history) == 0

    # Chaining operations
    result = (
        lens
        .drop_duplicates(subset=["id"])
        .query("id > 2")
    )

    assert isinstance(result, Lens)
    assert len(result.history) == 2
    assert result.history[0].method_name == "drop_duplicates"
    assert result.history[1].method_name == "query"
    assert result.df is not None
    assert result.to_df() is not None


def test_scalar_operation_passthrough():
    df = MockDataFrame({"id": [1, 2, 3]})
    lens = watch(df)
    val = lens.scalar_stat()
    assert val == 42


def test_nonexistent_attribute_raises():
    df = MockDataFrame({"id": [1, 2, 3]})
    lens = watch(df)
    with pytest.raises(AttributeError):
        _ = lens.non_existent_method()


def test_pipe_custom_function():
    df = MockDataFrame({"id": [1, 2, 3], "val": [10, 20, 30]})
    lens = watch(df)

    def custom_filter(data):
        return data.query("id > 1")

    result = lens.pipe(custom_filter)
    assert len(result.history) == 1
    assert result.history[0].method_name == "custom_filter"


def test_indexing_interception():
    df = MockDataFrame({"id": [1, 2, 3, 4], "val": [10, 20, 30, 40]})
    lens = watch(df)
    sliced = lens[lens.df]
    assert len(sliced.history) == 1
    assert sliced.history[0].method_name == "__getitem__"


def test_live_logging(capsys):
    df = MockDataFrame({"id": [1, 2, 3, 4, 5]})
    lens = watch(df, live=True)
    _ = lens.drop_duplicates()
    captured = capsys.readouterr()
    assert "[PipeSpy Live]" in captured.out


def test_insight_engine_high_loss_alert():
    before_snap = DataSnapshot(shape=(100, 2), columns=["a", "b"], dtypes={}, null_counts={}, memory_bytes=100)
    after_snap = DataSnapshot(shape=(30, 2), columns=["a", "b"], dtypes={}, null_counts={}, memory_bytes=30)
    diff = StepDiff(
        step_number=1,
        method_name="query",
        args_repr="val > 50",
        before_shape=(100, 2),
        after_shape=(30, 2),
        row_diff=-70,
        col_diff=0,
        added_columns=[],
        removed_columns=[],
        new_nulls={},
        memory_change_kb=-0.07,
        duration_ms=5.0,
    )

    insights, alerts = InsightEngine.generate(None, None, before_snap, after_snap, diff)
    assert any("High loss" in a for a in alerts)


def test_insight_engine_empty_dataframe_alert():
    before_snap = DataSnapshot(shape=(50, 2), columns=["a", "b"], dtypes={}, null_counts={}, memory_bytes=100)
    after_snap = DataSnapshot(shape=(0, 2), columns=["a", "b"], dtypes={}, null_counts={}, memory_bytes=0)
    diff = StepDiff(
        step_number=1,
        method_name="query",
        args_repr="age > 100",
        before_shape=(50, 2),
        after_shape=(0, 2),
        row_diff=-50,
        col_diff=0,
        added_columns=[],
        removed_columns=[],
        new_nulls={},
        memory_change_kb=-0.1,
        duration_ms=2.0,
    )

    insights, alerts = InsightEngine.generate(None, None, before_snap, after_snap, diff)
    assert any("CRITICAL" in a and "empty" in a for a in alerts)


def test_insight_engine_new_nulls_alert():
    before_snap = DataSnapshot(shape=(10, 2), columns=["a", "b"], dtypes={}, null_counts={"a": 0, "b": 0}, memory_bytes=100)
    after_snap = DataSnapshot(shape=(10, 2), columns=["a", "b"], dtypes={}, null_counts={"a": 0, "b": 5}, memory_bytes=100)
    diff = StepDiff(
        step_number=1,
        method_name="merge",
        args_repr="",
        before_shape=(10, 2),
        after_shape=(10, 2),
        row_diff=0,
        col_diff=0,
        added_columns=[],
        removed_columns=[],
        new_nulls={"b": 5},
        memory_change_kb=0.0,
        duration_ms=4.0,
    )

    insights, alerts = InsightEngine.generate(None, None, before_snap, after_snap, diff)
    assert any("New missing values in 'b'" in a for a in alerts)


def test_report_and_summary():
    df = MockDataFrame({"id": [1, 2, 3, 4], "val": [10, 20, 30, 40]})
    lens = watch(df)
    filtered = lens.drop_duplicates()

    # summary check
    summary = filtered.summary()
    assert len(summary) == 1

    # report returns clean df
    returned_df = filtered.report(return_df=True)
    assert is_dataframe(returned_df)

    # test plain rendering directly
    PipelineReporter._render_plain(filtered.history, "Test Plain")
