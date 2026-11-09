"""
demo.py - Quick demonstration of PipeLens in action.
"""

import sys
from pathlib import Path

# Add src to sys.path so demo runs directly without pre-installing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import numpy as np
from pipelens import watch


def main():
    print("🚀 Running PipeLens Real-World Pipeline Demo...\n")

    # 1. Create simulated messy customer data
    np.random.seed(42)
    raw_customers = pd.DataFrame({
        "id": [1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10],  # Has duplicate IDs (2, 10)
        "name": ["Aarav", "Priya", "Priya", "Rahul", "Sneha", "Vikram", "Ananya", "Rohan", "Kavya", "Aditya", "Neha", "Neha"],
        "age": [25, 16, 16, 32, 28, 17, 45, np.nan, 29, 31, 24, 24],  # Has minors (16, 17) & NaN
        "status": ["active", "active", "active", "inactive", "active", "active", "inactive", "active", "active", "active", "active", "active"],
        "email": ["aarav@gmail.com", "priya@gmail.com", "priya@gmail.com", None, "sneha@yahoo.com", "vikram@gmail.com", "ananya@gmail.com", "rohan@hotmail.com", "kavya@gmail.com", "aditya@gmail.com", "neha@gmail.com", "neha@gmail.com"],
    })

    # Supplementary order data
    orders = pd.DataFrame({
        "id": [1, 1, 3, 4, 7, 9, 10],  # id=1 has 2 orders (will expand rows on merge!)
        "order_amount": [1200, 450, 890, 2300, 150, 4200, 310],
        "category": ["Electronics", "Books", "Fashion", "Electronics", "Groceries", "Electronics", "Beauty"],
    })

    print(f"📦 Loaded Raw Data: {raw_customers.shape[0]} rows, {raw_customers.shape[1]} columns.\n")

    # 2. Pipeline transformation with PipeLens
    clean_df = (
        watch(raw_customers)
        # Step 1: Remove duplicates
        .drop_duplicates(subset=["id"])
        # Step 2: Remove minors & missing age
        .query("age >= 18")
        # Step 3: Remove records without email
        .dropna(subset=["email"])
        # Step 4: Left join with order history
        .merge(orders, on="id", how="left")
        # Step 5: Fill missing order values
        .fillna({"order_amount": 0, "category": "None"})
        # Generate the beautiful audit report and return the cleaned DataFrame!
        .report(title="Customer Cleaning & Enrichment Pipeline")
    )

    print("✨ Cleaned DataFrame successfully returned to developer:")
    print(clean_df.head())


if __name__ == "__main__":
    main()
