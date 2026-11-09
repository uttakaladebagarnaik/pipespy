# 🔍 PipeTrace

[![PyPI version](https://img.shields.io/pypi/v/pipetrace.svg?color=blue)](https://pypi.org/project/pipetrace/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#)

> **A lightweight, non-intrusive pipeline debugger and automated story insight engine for Pandas.**

Stop writing `print(df.shape)` after every single line of your Pandas pipelines. **PipeTrace** seamlessly traces row losses, column mutations, unexpected `NaN` introductions, and join explosions — giving you a clean visual X-ray and automated story insights at the end of your pipeline.

---

## ⚡ The Problem

When developers chain Pandas operations:

```python
# Where did my rows go? Which step created duplicate keys? Why are there new NaNs?
clean_df = (
    df
    .drop_duplicates(subset=["id"])
    .query("age >= 18")
    .merge(orders, on="id", how="left")
    .dropna(subset=["email"])
)
```

Debugging this usually requires breaking the chain and adding dozens of temporary `print()` statements.

## 💡 The PipeTrace Solution

Wrap your DataFrame in `trace()` (or `watch()`). PipeTrace intercepts every step, records structural diffs, generates smart alerts, and prints a gorgeous audit report:

```python
import pandas as pd
from pipetrace import trace

clean_df = (
    trace(raw_customers)
    .drop_duplicates(subset=["id"])
    .query("age >= 18")
    .merge(orders, on="id", how="left")
    .dropna(subset=["email"])
    .report(title="Customer Cleaning Pipeline") # 🔍 Audit report printed & clean DataFrame returned!
)
```

### 🖥️ Terminal Report Preview

```text
┌─────────────────── ⚡ Customer Cleaning Pipeline ───────────────────────────┐
│ 🔍 PipeTrace Data Audit & Insights                                          │
│ Initial: 10,000 rows × 5 cols  ➔  Final: 8,420 rows × 8 cols                │
│ Net Row Change: -1,580 rows | Total Time: 42.1ms                            │
└─────────────────────────────────────────────────────────────────────────────┘
                        Pipeline Step-by-Step Execution                        
┌─────┬───────────────────────────┬───────────────────┬───────────┬──────────┬────────────────────────────────────────┐
│  #  │ Operation                 │              Rows │   Cols    │     Time │ Insights & Alerts                      │
├─────┼───────────────────────────┼───────────────────┼───────────┼──────────┼────────────────────────────────────────┤
│  1  │ .drop_duplicates(subset=… │        9,850 (-150)│     5     │    4.2ms │ 💡 Pattern: 70% drops had same email   │
│  2  │ .query('age >= 18')       │        9,100 (-750)│     5     │    8.1ms │ ⚠️ High loss: Dropped 750 records      │
│  3  │ .merge(orders, how='left')│      9,400 (+300)  │  8 (+3)   │   12.4ms │ ⚠️ Row explosion (+300 rows in join!)  │
│  4  │ .dropna(subset=['email']) │        8,420 (-980)│     8     │    3.1ms │ 💡 Missing values in 'email' caused drops│
└─────┴───────────────────────────┴───────────────────┴───────────┴──────────┴────────────────────────────────────────┘
```

---

## 🚀 Key Features

- **Zero-Friction Chaining:** `trace(df)` wraps your DataFrame transparently. Any standard Pandas operation (`query`, `drop_duplicates`, `merge`, `fillna`, `assign`, etc.) works as normal.
- **Automated Insights & Alerts:**
  - 🚨 **Empty DataFrame Alert:** Immediately warns if any filter wiped out all data (0 rows).
  - 💥 **Join / Cartesian Explosion:** Alerts if a `merge` multiplied rows due to duplicate join keys.
  - 📉 **High Data Loss Alert:** Highlights steps that dropped > 50% of records.
  - 🧩 **Pattern Detection:** Analyzes dropped records to find dominant categorical values causing drops.
  - ⚠️ **New NaN Detector:** Tracks columns that gained missing values during transformation.
- **Jupyter Notebook Ready:** Native rich HTML rendering in Jupyter notebooks (`_repr_html_`).
- **Export to DataFrame:** Call `.summary()` to get a pandas DataFrame containing step numbers, shapes, durations, and alerts for CI/CD logging.

---

## 📦 Installation

```bash
pip install pipetrace
```

*Requirements:* Python 3.8+, `pandas`, `rich`.

---

## 🛠️ Usage Examples

### 1. Basic Chaining with `.report()`

```python
import pandas as pd
from pipetrace import trace

df = pd.read_csv("sales_data.csv")

clean_df = (
    trace(df)
    .drop_duplicates(subset=["transaction_id"])
    .query("amount > 0")
    .assign(tax=lambda d: d["amount"] * 0.18)
    .report()
)
```

### 2. Live Logging Mode

Want real-time console feedback as each step executes? Enable `live=True`:

```python
clean_df = (
    trace(df, live=True)
    .drop_duplicates()
    .query("status == 'active'")
    .to_df()
)
```

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

---

## 📄 License

MIT License. (c) 2026 Uttakaladeba Garnaik & Contributors.
