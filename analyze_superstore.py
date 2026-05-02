import pandas as pd
import numpy as np
import os

# ── Load ───────────────────────────────────────────────────────────────────────
df = pd.read_csv("data\\cleaned_superstore.csv")
print(f"Dataset loaded: {len(df):,} rows")
print(f"Columns: {list(df.columns)}\n")

SEP = "=" * 65

# ══════════════════════════════════════════════════════════════════
# QUERY 1 — Overall Business KPIs
# ══════════════════════════════════════════════════════════════════
print(SEP)
print("QUERY 1 | Overall Business KPIs")
print(SEP)

total_sales   = df["sales"].sum()
num_orders    = df["order_id"].nunique()
num_customers = df["customer_id"].nunique()
num_products  = df["product_id"].nunique()
avg_order_val = total_sales / num_orders
num_cities    = df["city"].nunique()
num_states    = df["state"].nunique()

print(f"  Total Revenue    : ${total_sales:>12,.2f}")
print(f"  Total Orders     : {num_orders:>12,}")
print(f"  Unique Customers : {num_customers:>12,}")
print(f"  Unique Products  : {num_products:>12,}")
print(f"  Avg Order Value  : ${avg_order_val:>12,.2f}")
print(f"  Cities Covered   : {num_cities:>12,}")
print(f"  States Covered   : {num_states:>12,}")

# ══════════════════════════════════════════════════════════════════
# QUERY 2 — Revenue by Region
# ══════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("QUERY 2 | Revenue by Region")
print(SEP)

region_q = (
    df.groupby("region")
    .agg(
        Revenue   =("sales",       "sum"),
        Orders    =("order_id",    "nunique"),
        Customers =("customer_id", "nunique"),
        Cities    =("city",        "nunique"),
    )
    .round(2)
    .assign(Revenue_share=lambda x: (x["Revenue"] / x["Revenue"].sum() * 100).round(1))
    .assign(Avg_order=lambda x: (x["Revenue"] / x["Orders"]).round(2))
    .sort_values("Revenue", ascending=False)
)
print(region_q.to_string())
region_q.to_csv("data\\region_summary.csv")

# ══════════════════════════════════════════════════════════════════
# QUERY 3 — Revenue by Category & Sub-Category
# ══════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("QUERY 3 | Revenue by Category & Sub-Category")
print(SEP)

cat_q = (
    df.groupby(["category", "sub_category"])
    .agg(
        Revenue  =("sales",      "sum"),
        Orders   =("order_id",   "nunique"),
        Products =("product_id", "nunique"),
    )
    .round(2)
    .assign(Revenue_share=lambda x: (x["Revenue"] / x["Revenue"].sum() * 100).round(1))
    .sort_values("Revenue", ascending=False)
)
print(cat_q.to_string())
cat_q.to_csv("data\\category_summary.csv")

# ══════════════════════════════════════════════════════════════════
# QUERY 4 — Monthly Revenue Trend by Year
# ══════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("QUERY 4 | Monthly Revenue Trend by Year")
print(SEP)

month_order = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]

monthly_q = (
    df.groupby(["year", "month"])
    .agg(Revenue=("sales", "sum"), Orders=("order_id", "nunique"))
    .round(2)
    .reset_index()
)
monthly_q["month"] = pd.Categorical(
    monthly_q["month"], categories=month_order, ordered=True
)
monthly_q = monthly_q.sort_values(["year", "month"]).reset_index(drop=True)
print(monthly_q.to_string(index=False))
monthly_q.to_csv("data\\monthly_trend.csv", index=False)

# ══════════════════════════════════════════════════════════════════
# QUERY 5 — Customer Segment Revenue
# ══════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("QUERY 5 | Customer Segment Revenue")
print(SEP)

seg_q = (
    df.groupby("segment")
    .agg(
        Revenue   =("sales",       "sum"),
        Orders    =("order_id",    "nunique"),
        Customers =("customer_id", "nunique"),
    )
    .round(2)
    .assign(Revenue_share=lambda x: (x["Revenue"] / x["Revenue"].sum() * 100).round(1))
    .assign(Avg_order=lambda x: (x["Revenue"] / x["Orders"]).round(2))
    .sort_values("Revenue", ascending=False)
)
print(seg_q.to_string())
seg_q.to_csv("data\\segment_summary.csv")

# ══════════════════════════════════════════════════════════════════
# QUERY 6 — Top 10 States by Revenue
# ══════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("QUERY 6 | Top 10 & Bottom 10 States by Revenue")
print(SEP)

state_q = (
    df.groupby(["state", "region"])
    .agg(Revenue=("sales", "sum"), Orders=("order_id", "nunique"))
    .round(2)
    .assign(Avg_order=lambda x: (x["Revenue"] / x["Orders"]).round(2))
    .sort_values("Revenue", ascending=False)
)

print("  -- Top 10 States by Revenue --")
print(state_q.head(10).to_string())

print("\n  -- Bottom 10 States by Revenue --")
print(state_q.tail(10).to_string())
state_q.to_csv("data\\state_summary.csv")

# ══════════════════════════════════════════════════════════════════
# QUERY 7 — Top 10 Best-Selling Products
# ══════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("QUERY 7 | Top 10 Best-Selling Products")
print(SEP)

product_q = (
    df.groupby(["product_name", "category", "sub_category"])
    .agg(Revenue=("sales", "sum"), Orders=("order_id", "nunique"))
    .round(2)
    .sort_values("Revenue", ascending=False)
    .head(10)
)
print(product_q.to_string())
product_q.to_csv("data\\top_products.csv")

# ══════════════════════════════════════════════════════════════════
# QUERY 8 — Year-over-Year Revenue Growth
# ══════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("QUERY 8 | Year-over-Year Revenue Growth")
print(SEP)

yoy_q = (
    df.groupby("year")
    .agg(Revenue=("sales", "sum"), Orders=("order_id", "nunique"))
    .round(2)
)
yoy_q["YoY_Growth_%"] = yoy_q["Revenue"].pct_change().mul(100).round(1)
yoy_q["Avg_order"]    = (yoy_q["Revenue"] / yoy_q["Orders"]).round(2)
print(yoy_q.to_string())
yoy_q.to_csv("data\\yoy_growth.csv")

# ══════════════════════════════════════════════════════════════════
# QUERY 9 — Ship Mode Distribution
# ══════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("QUERY 9 | Revenue by Ship Mode")
print(SEP)

ship_q = (
    df.groupby("ship_mode")
    .agg(Revenue=("sales", "sum"), Orders=("order_id", "nunique"))
    .round(2)
    .assign(Revenue_share=lambda x: (x["Revenue"] / x["Revenue"].sum() * 100).round(1))
    .sort_values("Revenue", ascending=False)
)
print(ship_q.to_string())
ship_q.to_csv("data\\shipmode_summary.csv")

print(f"\n{SEP}")
print("All 9 queries done. Summary CSVs saved to data\\")
print(SEP)
