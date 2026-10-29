"""Creates a deliberately messy sales CSV to demo the pipeline."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 200

df = pd.DataFrame({
    "Order ID": np.arange(1001, 1001 + n),
    "Order Date": pd.date_range("2026-01-01", periods=n, freq="D").strftime("%Y-%m-%d"),
    "Region": rng.choice(["north", "SOUTH ", "East", "west", "North"], n),
    "Product": rng.choice(["Laptop", "Phone", "Tablet", "Monitor"], n),
    "Quantity": rng.integers(1, 10, n).astype(float),
    "Unit Price": rng.integers(200, 1500, n).astype(float),
    "Notes": [None] * n,
})
df["Total"] = df["Quantity"] * df["Unit Price"]
df["Unit Price"] = df["Unit Price"].map(lambda v: f"${v:,.0f}")  # price stored as text

# inject mess
for col in ["Quantity", "Region", "Total"]:
    df.loc[rng.choice(n, 12, replace=False), col] = None
df = pd.concat([df, df.sample(8, random_state=1)], ignore_index=True)  # duplicates

df.to_csv("data/sample_sales.csv", index=False)
print("Wrote data/sample_sales.csv with", len(df), "rows")
