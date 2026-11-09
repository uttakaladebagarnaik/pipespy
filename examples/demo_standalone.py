"""
demo_standalone.py - Visual demonstration of PipeSpy in the terminal.
Runs instantly in any environment (even without external pandas binary requirements).
"""

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from pipespy import Spy
from tests.test_pipespy import MockDataFrame


def main():
    print("🚀 Initializing PipeSpy Pipeline Audit...\n")

    # Mock customer dataset (raw messy records)
    raw_data = MockDataFrame({
        "customer_id": [101, 102, 102, 103, 104, 105, 106, 107, 108, 109, 110, 110],
        "name": ["Aarav", "Priya", "Priya", "Rahul", "Sneha", "Vikram", "Ananya", "Rohan", "Kavya", "Aditya", "Neha", "Neha"],
        "age": [25, 16, 16, 32, 28, 17, 45, None, 29, 31, 24, 24],
        "status": ["active", "active", "active", "inactive", "active", "active", "inactive", "active", "active", "active", "active", "active"],
        "email": ["aarav@mail.com", "priya@mail.com", "priya@mail.com", None, "sneha@mail.com", "vikram@mail.com", "ananya@mail.com", "rohan@mail.com", "kavya@mail.com", "aditya@mail.com", "neha@mail.com", "neha@mail.com"],
    })

    print(f"📦 Loaded Dataset: {raw_data.shape[0]} rows × {raw_data.shape[1]} columns.\n")

    # Run pipeline with PipeSpy tracking
    clean_df = (
        Spy(raw_data)
        .drop_duplicates(subset=["customer_id"])
        .query("age >= 18")
        .dropna(subset=["email"])
        .assign(verified=True)
        .report(title="Customer Data Enrichment Pipeline")
    )

    print("✨ Clean DataFrame successfully returned from pipeline!")
    print(f"Final shape: {clean_df.shape[0]} rows × {clean_df.shape[1]} columns.\n")


if __name__ == "__main__":
    main()
