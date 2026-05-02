import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os

os.makedirs("output", exist_ok=True)

# ── Global style ───────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "font.family":        "DejaVu Sans",
    "axes.titlesize":     13,
    "axes.titleweight":   "bold",
    "axes.labelsize":     11,
    "xtick.labelsize":    9,
    "ytick.labelsize":    9,
    "figure.dpi":         150,
    "savefig.bbox":       "tight",
    "savefig.dpi":        150,
})

BLUE   = "#2563EB"
GREEN  = "#16A34A"
ORANGE = "#EA580C"
PURPLE = "#7C3AED"
TEAL   = "#0D9488"
RED    = "#DC2626"
COLORS = [BLUE, GREEN, ORANGE, PURPLE, TEAL, RED,
          "#0891B2", "#B45309", "#BE185D", "#065F46"]

# ── Load summaries ─────────────────────────────────────────────────────────────
df       = pd.read_csv("data\\cleaned_superstore.csv")
region   = pd.read_csv("data\\region_summary.csv")
category = pd.read_csv("data\\category_summary.csv")
monthly  = pd.read_csv("data\\monthly_trend.csv")
segment  = pd.read_csv("data\\segment_summary.csv")
state    = pd.read_csv("data\\state_summary.csv")
products = pd.read_csv("data\\top_products.csv")
yoy      = pd.read_csv("data\\yoy_growth.csv")
shipmode = pd.read_csv("data\\shipmode_summary.csv")

MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]

def fmt_k(x, _):
    return f"${x/1000:.0f}K" if x >= 1000 else f"${x:.0f}"

print("Generating charts …")

# ══════════════════════════════════════════════════════════════════
# CHART 1 — KPI Summary Card (text-based, looks great in README)
# ══════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 4, figsize=(14, 3))
fig.patch.set_facecolor("#F8FAFC")

kpis = [
    ("Total Revenue",    f"${df['sales'].sum():,.0f}",          BLUE),
    ("Total Orders",     f"{df['order_id'].nunique():,}",        GREEN),
    ("Unique Customers", f"{df['customer_id'].nunique():,}",     ORANGE),
    ("Avg Order Value",  f"${df['sales'].sum()/df['order_id'].nunique():,.0f}", PURPLE),
]
for ax, (label, value, color) in zip(axes, kpis):
    ax.set_facecolor("white")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0,0),1,1, color=color, alpha=0.08, transform=ax.transAxes))
    ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=22,
            fontweight="bold", color=color, transform=ax.transAxes)
    ax.text(0.5, 0.28, label, ha="center", va="center", fontsize=10,
            color="#64748B", transform=ax.transAxes)
    for spine in ax.spines.values():
        spine.set_edgecolor(color); spine.set_linewidth(1.5); spine.set_visible(True)

plt.suptitle("Sales Performance — Key Metrics", fontsize=14, fontweight="bold",
             color="#1E293B", y=1.02)
plt.tight_layout()
plt.savefig("output\\chart1_kpi_cards.png")
plt.close()
print("  ✓ chart1_kpi_cards.png")

# ══════════════════════════════════════════════════════════════════
# CHART 2 — Monthly Revenue Trend (multi-year line chart)
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(13, 5))

monthly["month"] = pd.Categorical(monthly["month"], categories=MONTH_ORDER, ordered=True)
years = sorted(monthly["year"].unique())
line_colors = [BLUE, GREEN, ORANGE, PURPLE]

for i, yr in enumerate(years):
    yd = monthly[monthly["year"] == yr].sort_values("month")
    ax.plot(yd["month"].astype(str), yd["Revenue"],
            marker="o", markersize=5, linewidth=2,
            color=line_colors[i % len(line_colors)], label=str(yr))
    # label last point
    last = yd.iloc[-1]
    ax.annotate(f"${last['Revenue']/1000:.0f}K",
                xy=(str(last["month"]), last["Revenue"]),
                xytext=(4, 4), textcoords="offset points",
                fontsize=7, color=line_colors[i % len(line_colors)])

ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_title("Monthly Revenue Trend by Year")
ax.set_xlabel("Month"); ax.set_ylabel("Revenue (USD)")
ax.legend(title="Year", framealpha=0.5)
ax.grid(axis="y", alpha=0.4)
plt.tight_layout()
plt.savefig("output\\chart2_monthly_trend.png")
plt.close()
print("  ✓ chart2_monthly_trend.png")

# ══════════════════════════════════════════════════════════════════
# CHART 3 — Revenue by Region (horizontal bar)
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 4))

region_s = region.sort_values("Revenue")
bars = ax.barh(region_s["region"], region_s["Revenue"],
               color=COLORS[:len(region_s)], edgecolor="white", height=0.5)
for bar, val in zip(bars, region_s["Revenue"]):
    ax.text(bar.get_width() + 1000, bar.get_y() + bar.get_height()/2,
            f"${val:,.0f}", va="center", fontsize=9, fontweight="bold")

ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_title("Revenue by Region")
ax.set_xlabel("Revenue (USD)")
ax.set_xlim(0, region_s["Revenue"].max() * 1.18)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig("output\\chart3_region_revenue.png")
plt.close()
print("  ✓ chart3_region_revenue.png")

# ══════════════════════════════════════════════════════════════════
# CHART 4 — Revenue by Category (donut chart)
# ══════════════════════════════════════════════════════════════════
cat_top = (
    df.groupby("category")["sales"].sum()
    .sort_values(ascending=False)
    .reset_index()
)
fig, ax = plt.subplots(figsize=(7, 7))
wedges, texts, autotexts = ax.pie(
    cat_top["sales"],
    labels=cat_top["category"],
    autopct="%1.1f%%",
    startangle=140,
    colors=COLORS[:len(cat_top)],
    pctdistance=0.75,
    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2),
)
for t in autotexts:
    t.set_fontsize(10); t.set_fontweight("bold")
ax.set_title("Revenue Share by Category", pad=20)
plt.tight_layout()
plt.savefig("output\\chart4_category_donut.png")
plt.close()
print("  ✓ chart4_category_donut.png")

# ══════════════════════════════════════════════════════════════════
# CHART 5 — Sub-Category Revenue Bar (sorted)
# ══════════════════════════════════════════════════════════════════
subcat_rev = (
    df.groupby(["sub_category", "category"])["sales"]
    .sum().reset_index().sort_values("sales", ascending=True)
)
cat_color_map = {c: COLORS[i] for i, c in enumerate(subcat_rev["category"].unique())}

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(subcat_rev["sub_category"], subcat_rev["sales"],
               color=[cat_color_map[c] for c in subcat_rev["category"]],
               edgecolor="white", height=0.6)
for bar, val in zip(bars, subcat_rev["sales"]):
    ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2,
            f"${val/1000:.0f}K", va="center", fontsize=8)

ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_title("Revenue by Sub-Category")
ax.set_xlabel("Revenue (USD)")
ax.set_xlim(0, subcat_rev["sales"].max() * 1.2)
# Legend for categories
from matplotlib.patches import Patch
legend_els = [Patch(color=cat_color_map[c], label=c) for c in cat_color_map]
ax.legend(handles=legend_els, title="Category", loc="lower right")
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig("output\\chart5_subcat_revenue.png")
plt.close()
print("  ✓ chart5_subcat_revenue.png")

# ══════════════════════════════════════════════════════════════════
# CHART 6 — Customer Segment Revenue (grouped bar)
# ══════════════════════════════════════════════════════════════════
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))

seg_colors = [BLUE, GREEN, ORANGE]
bars = ax1.bar(segment["segment"], segment["Revenue"],
               color=seg_colors, edgecolor="white", width=0.5)
for bar, val in zip(bars, segment["Revenue"]):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1000,
             f"${val:,.0f}", ha="center", fontsize=8, fontweight="bold")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax1.set_title("Revenue by Customer Segment")
ax1.set_ylabel("Revenue (USD)")
ax1.grid(axis="y", alpha=0.3)

bars2 = ax2.bar(segment["segment"], segment["Orders"],
                color=seg_colors, edgecolor="white", width=0.5)
for bar, val in zip(bars2, segment["Orders"]):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
             f"{int(val):,}", ha="center", fontsize=8, fontweight="bold")
ax2.set_title("Orders by Customer Segment")
ax2.set_ylabel("Number of Orders")
ax2.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig("output\\chart6_segment.png")
plt.close()
print("  ✓ chart6_segment.png")

# ══════════════════════════════════════════════════════════════════
# CHART 7 — Top 10 States by Revenue (horizontal bar)
# ══════════════════════════════════════════════════════════════════
top10_states = state.sort_values("Revenue", ascending=False).head(10)
bot10_states = state.sort_values("Revenue", ascending=True).head(10)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Top 10
bars = ax1.barh(top10_states["state"], top10_states["Revenue"],
                color=GREEN, edgecolor="white", height=0.6)
for bar, val in zip(bars, top10_states["Revenue"]):
    ax1.text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2,
             f"${val/1000:.0f}K", va="center", fontsize=8, fontweight="bold")
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax1.set_title("Top 10 States by Revenue")
ax1.set_xlabel("Revenue (USD)")
ax1.set_xlim(0, top10_states["Revenue"].max() * 1.22)
ax1.grid(axis="x", alpha=0.3)

# Bottom 10
bars2 = ax2.barh(bot10_states["state"], bot10_states["Revenue"],
                 color=RED, edgecolor="white", height=0.6)
for bar, val in zip(bars2, bot10_states["Revenue"]):
    ax2.text(bar.get_width() + 100, bar.get_y() + bar.get_height()/2,
             f"${val/1000:.1f}K", va="center", fontsize=8, fontweight="bold")
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax2.set_title("Bottom 10 States by Revenue")
ax2.set_xlabel("Revenue (USD)")
ax2.set_xlim(0, bot10_states["Revenue"].max() * 1.35)
ax2.grid(axis="x", alpha=0.3)

plt.tight_layout()
plt.savefig("output\\chart7_state_revenue.png")
plt.close()
print("  ✓ chart7_state_revenue.png")

# ══════════════════════════════════════════════════════════════════
# CHART 8 — Year-over-Year Revenue Growth
# ══════════════════════════════════════════════════════════════════
fig, ax1 = plt.subplots(figsize=(8, 4))
ax2 = ax1.twinx()

bars = ax1.bar(yoy["year"].astype(str), yoy["Revenue"],
               color=BLUE, alpha=0.7, edgecolor="white", width=0.5, label="Revenue")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax1.set_ylabel("Revenue (USD)", color=BLUE)
ax1.tick_params(axis="y", labelcolor=BLUE)

yoy_valid = yoy.dropna(subset=["YoY_Growth_%"])
ax2.plot(yoy_valid["year"].astype(str), yoy_valid["YoY_Growth_%"],
         color=ORANGE, marker="o", linewidth=2.5, markersize=7, label="YoY Growth %")
for _, row in yoy_valid.iterrows():
    ax2.annotate(f"{row['YoY_Growth_%']:.1f}%",
                 xy=(str(int(row["year"])), row["YoY_Growth_%"]),
                 xytext=(0, 10), textcoords="offset points",
                 ha="center", fontsize=9, color=ORANGE, fontweight="bold")
ax2.set_ylabel("YoY Growth %", color=ORANGE)
ax2.tick_params(axis="y", labelcolor=ORANGE)

ax1.set_title("Year-over-Year Revenue & Growth")
ax1.set_xlabel("Year")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
ax1.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("output\\chart8_yoy_growth.png")
plt.close()
print("  ✓ chart8_yoy_growth.png")

# ══════════════════════════════════════════════════════════════════
# CHART 9 — Top 10 Products Heatmap style horizontal bar
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(11, 6))

prod_df = products.reset_index() if "product_name" not in products.columns else products
prod_df = prod_df.sort_values("Revenue", ascending=True).tail(10)

norm = plt.Normalize(prod_df["Revenue"].min(), prod_df["Revenue"].max())
cmap = plt.cm.Blues
bar_colors = [cmap(norm(v)) for v in prod_df["Revenue"]]

bars = ax.barh(prod_df["product_name"].str[:45], prod_df["Revenue"],
               color=bar_colors, edgecolor="white", height=0.6)
for bar, val in zip(bars, prod_df["Revenue"]):
    ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height()/2,
            f"${val:,.0f}", va="center", fontsize=8, fontweight="bold")

ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_title("Top 10 Best-Selling Products by Revenue")
ax.set_xlabel("Revenue (USD)")
ax.set_xlim(0, prod_df["Revenue"].max() * 1.25)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig("output\\chart9_top_products.png")
plt.close()
print("  ✓ chart9_top_products.png")

# ══════════════════════════════════════════════════════════════════
# CHART 10 — Ship Mode Revenue Pie
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 5))
wedges, texts, autotexts = ax.pie(
    shipmode["Revenue"],
    labels=shipmode["ship_mode"],
    autopct="%1.1f%%",
    startangle=90,
    colors=COLORS[:len(shipmode)],
    pctdistance=0.78,
    wedgeprops=dict(edgecolor="white", linewidth=2),
)
for t in autotexts:
    t.set_fontsize(10); t.set_fontweight("bold")
ax.set_title("Revenue by Ship Mode")
plt.tight_layout()
plt.savefig("output\\chart10_shipmode.png")
plt.close()
print("  ✓ chart10_shipmode.png")

print("\nAll 10 charts saved to output\\")
print("Phase 3 complete!")
