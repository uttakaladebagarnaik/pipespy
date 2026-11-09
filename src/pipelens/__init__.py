"""
PipeLens - A lightweight pipeline debugger and automated story insight engine for Pandas.
"""

from pipelens.tracker import Lens, watch
from pipelens.diff import StepDiff, DataSnapshot

__version__ = "0.1.0"
__all__ = ["Lens", "watch", "StepDiff", "DataSnapshot"]
