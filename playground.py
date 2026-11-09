"""
playground.py - Aapka personal test script (No Pandas knowledge needed!)
Isko run karke aap PipeSpy ko khud test kar sakte hain.
"""

import sys
from pathlib import Path

# Windows console encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# PipeSpy aur test helper ko load karte hain
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from pipespy import watch, Spy
from tests.test_pipespy import MockDataFrame


def test_my_first_pipeline():
    print("=" * 60)
    print("🕵️ PIPESPY SELF-TEST PLAYGROUND")
    print("=" * 60)

    # 1. Socho ye aapka ek Excel Sheet hai:
    # Isme 6 logo ka data hai, par kuch galtiyaan hain:
    # - ID 101 do baar hai (Duplicate)
    # - Age data
    # - Ek bande ka email gayab hai (Missing/None)
    data = MockDataFrame({
        "id": [101, 101, 102, 103, 104, 105],
        "name": ["Aarav", "Aarav", "Priya", "Rahul", "Sneha", "Vikram"],
        "age": [4, 4, 5, 0, 2, 8],
        "email": ["aarav@gmail.com", "aarav@gmail.com", "priya@gmail.com", None, "sneha@gmail.com", "vikram@gmail.com"]
    })

    print(f"\n1️⃣ Shuruwaati Data: {data.shape[0]} Rows (Records)")

    # 2. Ab PipeSpy ka jaadu dekho:
    clean_data = (
        Spy(data)
        .drop_duplicates(subset=["id"])   # Rule 1: Duplicate ID hatao
        .query("age >= 18")               # Rule 2: 18 saal se chote logo ko hatao
        .dropna(subset=["email"])         # Rule 3: Jinka email nahi hai unhe hatao
        .report(title="My First Data Cleaning Test") # Yahan PipeSpy poora hisab dikhayega!
    )

    print("\n2️⃣ Final Cleaned Data: Saari galtiyaan hat gayi!")
    print(f"Bache hue records: {clean_data.shape[0]} Rows")
    print("=" * 60)


if __name__ == "__main__":
    test_my_first_pipeline()
