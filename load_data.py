import pandas as pd
import os
import glob

# ── Auto-detect the Superstore CSV (handles all common filenames) ──────────────
search_patterns = [
    "data/*.csv",
    "data/*.CSV",
]

csv_files = []
for pattern in search_patterns:
    csv_files.extend(glob.glob(pattern))

if not csv_files:
    print("ERROR: No CSV found in data\\ folder.")
    print("Make sure superstore_sales.csv is inside the data\\ folder.")
    exit()

# Pick the right file (prefer one with 'superstore' or 'train' or 'Sample' in name)
target = csv_files[0]
for f in csv_files:
    name = os.path.basename(f).lower()
    if any(k in name for k in ["superstore", "train", "sample", "sales"]):
        target = f
        break

print(f"Found: {target}")

# ── Load ───────────────────────────────────────────────────────────────────────
df = pd.read_csv(target, encoding="latin-1")
print(f"Shape : {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"\nColumns:\n{list(df.columns)}\n")
print(df.head(3).to_string())

# ── Standardise column names (strip spaces, fix encoding) ─────────────────────
df.columns = (
    df.columns
    .str.strip()
    .str.replace(" ", "_")
    .str.replace("-", "_")
    .str.lower()
)

# ── Parse dates ────────────────────────────────────────────────────────────────
date_col = next((c for c in df.columns if "order" in c and "date" in c), None)
if date_col:
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=False, errors="coerce")
    df["month"]   = df[date_col].dt.strftime("%b")   # Jan, Feb …
    df["year"]    = df[date_col].dt.year
    df["quarter"] = df[date_col].dt.to_period("Q").astype(str)
    print(f"\nDate range: {df[date_col].min().date()}  →  {df[date_col].max().date()}")

# ── Save cleaned version ───────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
df.to_csv("data\\cleaned_superstore.csv", index=False)
print(f"\nCleaned file saved → data\\cleaned_superstore.csv")
print(f"Ready for analysis!")
