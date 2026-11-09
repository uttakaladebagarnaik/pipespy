"""
PipeSpy - A lightweight pipeline debugger and automated story insight engine for Pandas.
"""

from pipespy.tracker import Lens, watch, Lens as Spy
from pipespy.diff import StepDiff, DataSnapshot

__version__ = "0.1.0"
__all__ = ["Spy", "Lens", "watch", "StepDiff", "DataSnapshot"]
