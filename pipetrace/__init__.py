"""
PipeTrace - A lightweight pipeline debugger and automated story insight engine for Pandas.
"""

from pipetrace.tracker import Lens, watch, Lens as trace, Lens as Trace
from pipetrace.diff import StepDiff, DataSnapshot

__version__ = "0.1.0"
__all__ = ["trace", "Trace", "watch", "Lens", "StepDiff", "DataSnapshot"]
