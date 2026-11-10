"""
walkthrough.py - Aapke screen recording ke liye clean aur realistic code!
Isko VS Code me khol kar screen par dikhana hai.
"""

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from pipetrace import trace
from tests.test_pipetrace import MockDataFrame

# 1. Hamara Raw Dataset (Isme kuch data errors hain)
raw_data = MockDataFrame({
    "customer_id": [101, 101, 102, 103, 104, 105],
    "name": ["Aarav", "Aarav", "Priya", "Rahul", "Sneha", "Vikram"],
    "age": [25, 25, 16, 32, 17, 29],         # 16 aur 17 minors hain!
    "email": ["aarav@mail.com", "aarav@mail.com", "priya@mail.com", None, "sneha@mail.com", "vikram@mail.com"],
})

# 2. Chained Data Pipeline with PipeTrace
clean_df = (
    trace(raw_data)
    .drop_duplicates(subset=["customer_id"])   # Step 1: Duplicate customer ID hatayega
    .query("age >= 18")                       # Step 2: 18 se chote logo ko filter karega
    .dropna(subset=["email"])                 # Step 3: Missing email walo ko hatayega
    .report(title="Customer Data Pipeline")   # 🔍 Poora visual audit hisab yahan aayega!
)
