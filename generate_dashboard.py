import pandas as pd
import json
import os

# ── Load all summaries ─────────────────────────────────────────────────────────
df       = pd.read_csv("data\\cleaned_superstore.csv")
region   = pd.read_csv("data\\region_summary.csv")
category = pd.read_csv("data\\category_summary.csv")
monthly  = pd.read_csv("data\\monthly_trend.csv")
segment  = pd.read_csv("data\\segment_summary.csv")
state    = pd.read_csv("data\\state_summary.csv")
yoy      = pd.read_csv("data\\yoy_growth.csv")
shipmode = pd.read_csv("data\\shipmode_summary.csv")

MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]

monthly["month"] = pd.Categorical(monthly["month"], categories=MONTH_ORDER, ordered=True)
monthly = monthly.sort_values(["year","month"]).reset_index(drop=True)

# ── Build JSON data blobs ──────────────────────────────────────────────────────
kpis = {
    "revenue":   round(df["sales"].sum(), 2),
    "orders":    int(df["order_id"].nunique()),
    "customers": int(df["customer_id"].nunique()),
    "avg_order": round(df["sales"].sum() / df["order_id"].nunique(), 2),
    "states":    int(df["state"].nunique()),
    "products":  int(df["product_id"].nunique()),
}

region_data = {
    "labels":  region["region"].tolist(),
    "revenue": [round(x,2) for x in region["Revenue"].tolist()],
    "orders":  [int(x) for x in region["Orders"].tolist()],
}

cat_data = {
    "labels":  [f"{r['category']} / {r['sub_category']}" for _,r in category.iterrows()],
    "revenue": [round(x,2) for x in category["Revenue"].tolist()],
}

# Monthly — one series per year
years = sorted(monthly["year"].unique())
monthly_data = {
    "months": MONTH_ORDER,
    "years":  [int(y) for y in years],
    "series": {
        str(int(yr)): [
            round(monthly[(monthly["year"]==yr) & (monthly["month"]==m)]["Revenue"].sum(), 2)
            for m in MONTH_ORDER
        ] for yr in years
    }
}

seg_data = {
    "labels":  segment["segment"].tolist(),
    "revenue": [round(x,2) for x in segment["Revenue"].tolist()],
    "orders":  [int(x) for x in segment["Orders"].tolist()],
}

top10_states = state.sort_values("Revenue", ascending=False).head(10)
state_data = {
    "labels":  top10_states["state"].tolist(),
    "revenue": [round(x,2) for x in top10_states["Revenue"].tolist()],
}

yoy_clean = yoy.dropna(subset=["YoY_Growth_%"])
yoy_data = {
    "years":   [str(int(y)) for y in yoy["year"].tolist()],
    "revenue": [round(x,2) for x in yoy["Revenue"].tolist()],
    "growth":  [round(x,1) if not pd.isna(x) else 0 for x in yoy["YoY_Growth_%"].tolist()],
}

ship_data = {
    "labels":  shipmode["ship_mode"].tolist(),
    "revenue": [round(x,2) for x in shipmode["Revenue"].tolist()],
}

# Sub-category donut
subcat = df.groupby("category")["sales"].sum().reset_index().sort_values("sales", ascending=False)
subcat_data = {
    "labels":  subcat["category"].tolist(),
    "revenue": [round(x,2) for x in subcat["sales"].tolist()],
}

DATA = dict(
    kpis=kpis, region=region_data, category=cat_data,
    monthly=monthly_data, segment=seg_data, state=state_data,
    yoy=yoy_data, ship=ship_data, subcat=subcat_data
)

# ── HTML Template ──────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Superstore Sales Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',system-ui,sans-serif;background:#F1F5F9;color:#1E293B}}

  /* ── Header ── */
  .header{{background:linear-gradient(135deg,#1E3A5F 0%,#2563EB 100%);
           color:#fff;padding:1.2rem 2rem;display:flex;justify-content:space-between;align-items:center}}
  .header h1{{font-size:1.3rem;font-weight:600;letter-spacing:.3px}}
  .header .sub{{font-size:.8rem;opacity:.8;margin-top:2px}}
  .badge{{background:rgba(255,255,255,.18);padding:4px 12px;border-radius:20px;font-size:.75rem}}

  /* ── Filters ── */
  .filters{{background:#fff;padding:.75rem 2rem;display:flex;gap:1rem;
            align-items:center;flex-wrap:wrap;border-bottom:1px solid #E2E8F0;
            box-shadow:0 1px 3px rgba(0,0,0,.06)}}
  .filters label{{font-size:.75rem;color:#64748B;font-weight:500}}
  .filters select{{font-size:.82rem;padding:5px 10px;border-radius:8px;
                   border:1px solid #CBD5E1;background:#F8FAFC;color:#1E293B;cursor:pointer}}
  .filters select:focus{{outline:2px solid #2563EB;border-color:transparent}}
  .reset{{margin-left:auto;font-size:.78rem;padding:6px 14px;border-radius:8px;
          border:1px solid #CBD5E1;background:#fff;cursor:pointer;color:#64748B}}
  .reset:hover{{background:#F1F5F9}}

  /* ── Layout ── */
  .main{{padding:1.25rem 2rem}}
  .kpi-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:1.25rem}}
  .kpi{{background:#fff;border-radius:12px;padding:1rem 1.2rem;
        box-shadow:0 1px 4px rgba(0,0,0,.07);border-top:3px solid var(--c)}}
  .kpi .label{{font-size:.72rem;color:#64748B;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}}
  .kpi .val{{font-size:1.5rem;font-weight:700;color:var(--c)}}
  .kpi .note{{font-size:.7rem;color:#94A3B8;margin-top:3px}}

  .grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}}
  .grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px}}
  .full{{grid-column:1/-1}}

  .card{{background:#fff;border-radius:12px;padding:1.1rem 1.3rem;
         box-shadow:0 1px 4px rgba(0,0,0,.07)}}
  .card-title{{font-size:.82rem;font-weight:600;color:#334155;margin-bottom:.9rem;
               display:flex;justify-content:space-between;align-items:center}}
  .card-title span{{font-size:.7rem;color:#94A3B8;font-weight:400}}
  canvas{{max-height:220px}}

  /* ── Table ── */
  table{{width:100%;border-collapse:collapse;font-size:.78rem}}
  th{{text-align:left;padding:7px 10px;font-weight:600;font-size:.7rem;
      color:#64748B;border-bottom:1px solid #E2E8F0;background:#F8FAFC;text-transform:uppercase}}
  td{{padding:7px 10px;border-bottom:1px solid #F1F5F9;color:#1E293B}}
  tr:last-child td{{border-bottom:none}}
  .pill{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.68rem;font-weight:600}}
  .pill.high{{background:#DCFCE7;color:#15803D}}
  .pill.mid {{background:#FEF9C3;color:#854D0E}}
  .pill.low {{background:#FEE2E2;color:#B91C1C}}

  /* ── Insights box ── */
  .insights{{background:linear-gradient(135deg,#EFF6FF,#F0FDF4);border:1px solid #BFDBFE;
             border-radius:12px;padding:1rem 1.3rem;margin-bottom:12px}}
  .insights h3{{font-size:.82rem;font-weight:600;color:#1D4ED8;margin-bottom:.6rem}}
  .insights ul{{padding-left:1.1rem}}
  .insights li{{font-size:.78rem;color:#334155;margin-bottom:.3rem;line-height:1.5}}

  footer{{text-align:center;padding:1rem;font-size:.72rem;color:#94A3B8}}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>📊 Superstore Sales Performance Dashboard</h1>
    <div class="sub">Business Analysis Project &nbsp;·&nbsp; Kaggle Superstore Dataset</div>
  </div>
  <span class="badge" id="filterLabel">All Years · All Regions · All Segments</span>
</div>

<div class="filters">
  <div><label>Year</label><br>
    <select id="fYear" onchange="applyFilters()">
      <option value="all">All Years</option>
    </select>
  </div>
  <div><label>Region</label><br>
    <select id="fRegion" onchange="applyFilters()">
      <option value="all">All Regions</option>
    </select>
  </div>
  <div><label>Category</label><br>
    <select id="fCat" onchange="applyFilters()">
      <option value="all">All Categories</option>
    </select>
  </div>
  <div><label>Segment</label><br>
    <select id="fSeg" onchange="applyFilters()">
      <option value="all">All Segments</option>
    </select>
  </div>
  <button class="reset" onclick="resetFilters()">↺ Reset</button>
</div>

<div class="main">

  <!-- KPI Cards -->
  <div class="kpi-row" id="kpiRow"></div>

  <!-- Insights -->
  <div class="insights">
    <h3>🔍 Key Business Insights</h3>
    <ul id="insightsList"></ul>
  </div>

  <!-- Row 1: Monthly Trend + Region -->
  <div class="grid-2">
    <div class="card full">
      <div class="card-title">Monthly Revenue Trend <span>by year</span></div>
      <canvas id="cMonthly" style="max-height:200px"></canvas>
    </div>
  </div>

  <!-- Row 2: Region + Category donut -->
  <div class="grid-2">
    <div class="card">
      <div class="card-title">Revenue by Region</div>
      <canvas id="cRegion"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Revenue by Category</div>
      <canvas id="cCat"></canvas>
    </div>
  </div>

  <!-- Row 3: Segment + YoY -->
  <div class="grid-2">
    <div class="card">
      <div class="card-title">Customer Segment Revenue</div>
      <canvas id="cSeg"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Year-over-Year Growth</div>
      <canvas id="cYoy"></canvas>
    </div>
  </div>

  <!-- Row 4: Top States + Ship Mode -->
  <div class="grid-2">
    <div class="card">
      <div class="card-title">Top 10 States by Revenue</div>
      <canvas id="cState" style="max-height:260px"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Revenue by Ship Mode</div>
      <canvas id="cShip"></canvas>
    </div>
  </div>

  <!-- Row 5: Sub-category table -->
  <div class="card" style="margin-bottom:12px">
    <div class="card-title">Sub-Category Revenue Breakdown</div>
    <table id="subTable">
      <thead><tr><th>#</th><th>Category</th><th>Sub-Category</th><th>Revenue</th><th>Orders</th><th>Share</th><th>Performance</th></tr></thead>
      <tbody id="subBody"></tbody>
    </table>
  </div>

</div>

<footer>Built with Python · Pandas · Chart.js &nbsp;|&nbsp; Data: Kaggle Superstore Dataset &nbsp;|&nbsp; Sales Performance Analytics Dashboard</footer>

<script>
const RAW = {json.dumps(DATA)};

const COLORS = ["#2563EB","#16A34A","#EA580C","#7C3AED","#0D9488",
                "#DC2626","#0891B2","#B45309","#BE185D","#065F46",
                "#1D4ED8","#15803D","#C2410C","#6D28D9","#0F766E"];

// ── Populate filter dropdowns ──────────────────────────────────────────────────
RAW.yoy.years.forEach(y => {{
  document.getElementById("fYear").innerHTML += `<option value="${{y}}">${{y}}</option>`;
}});
RAW.region.labels.forEach(r => {{
  document.getElementById("fRegion").innerHTML += `<option value="${{r}}">${{r}}</option>`;
}});
["Furniture","Office Supplies","Technology"].forEach(c => {{
  document.getElementById("fCat").innerHTML += `<option value="${{c}}">${{c}}</option>`;
}});
RAW.segment.labels.forEach(s => {{
  document.getElementById("fSeg").innerHTML += `<option value="${{s}}">${{s}}</option>`;
}});

// ── Chart registry ─────────────────────────────────────────────────────────────
const charts = {{}};
function destroyChart(id) {{ if(charts[id]) {{ charts[id].destroy(); delete charts[id]; }} }}

function mkChart(id, config) {{
  destroyChart(id);
  charts[id] = new Chart(document.getElementById(id), config);
}}

// ── KPI Cards ─────────────────────────────────────────────────────────────────
function renderKPIs(data) {{
  const k = data;
  const cards = [
    {{label:"Total Revenue",    val:"$"+k.revenue.toLocaleString("en-US",{{minimumFractionDigits:0,maximumFractionDigits:0}}), note:"Gross sales",      c:"#2563EB"}},
    {{label:"Total Orders",     val:k.orders.toLocaleString(),      note:"Unique orders",     c:"#16A34A"}},
    {{label:"Unique Customers", val:k.customers.toLocaleString(),   note:"Active buyers",     c:"#EA580C"}},
    {{label:"Avg Order Value",  val:"$"+k.avg_order.toLocaleString("en-US",{{minimumFractionDigits:0,maximumFractionDigits:0}}), note:"Per order",   c:"#7C3AED"}},
    {{label:"States Covered",   val:k.states,                       note:"Geographic reach",  c:"#0D9488"}},
    {{label:"Products",         val:k.products.toLocaleString(),    note:"Unique SKUs",       c:"#DC2626"}},
  ];
  document.getElementById("kpiRow").innerHTML = cards.map(c =>
    `<div class="kpi" style="--c:${{c.c}}">
       <div class="label">${{c.label}}</div>
       <div class="val">${{c.val}}</div>
       <div class="note">${{c.note}}</div>
     </div>`
  ).join("");
}}

// ── Insights ──────────────────────────────────────────────────────────────────
function renderInsights(d) {{
  const topRegion = d.region.labels[d.region.revenue.indexOf(Math.max(...d.region.revenue))];
  const topSeg    = d.segment.labels[d.segment.revenue.indexOf(Math.max(...d.segment.revenue))];
  const topState  = d.state.labels[0];
  const lastGrowth = d.yoy.growth.filter(x => x !== 0).slice(-1)[0];
  const insights = [
    `<b>${{topRegion}}</b> is the highest-revenue region, contributing ${{((Math.max(...d.region.revenue)/d.region.revenue.reduce((a,b)=>a+b,0))*100).toFixed(1)}}% of total sales.`,
    `<b>${{topSeg}}</b> segment leads in revenue — a key focus area for client acquisition strategy.`,
    `<b>${{topState}}</b> is the top-performing state — consider deeper market penetration here.`,
    `Year-over-year growth stands at <b>${{lastGrowth > 0 ? '+' : ''}}${{lastGrowth}}%</b> in the most recent year — indicating ${{lastGrowth > 15 ? 'strong upward' : lastGrowth > 0 ? 'moderate' : 'declining'}} momentum.`,
    `Q4 (Oct–Dec) consistently shows the highest monthly revenue — seasonal peak that aligns with holiday demand.`,
  ];
  document.getElementById("insightsList").innerHTML = insights.map(i => `<li>${{i}}</li>`).join("");
}}

// ── Chart: Monthly Trend ───────────────────────────────────────────────────────
function renderMonthly(d) {{
  const lineColors = ["#2563EB","#16A34A","#EA580C","#7C3AED"];
  mkChart("cMonthly", {{
    type: "line",
    data: {{
      labels: d.monthly.months,
      datasets: d.monthly.years.map((yr, i) => ({{
        label: String(yr),
        data:  d.monthly.series[String(yr)],
        borderColor: lineColors[i % lineColors.length],
        backgroundColor: lineColors[i % lineColors.length] + "18",
        fill: true, tension: 0.4,
        borderWidth: 2.5, pointRadius: 3,
      }}))
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: "top", labels: {{ boxWidth:12, font:{{ size:11 }} }} }} }},
      scales: {{
        x: {{ ticks: {{ font:{{ size:10 }} }} }},
        y: {{ ticks: {{ font:{{ size:10 }}, callback: v => "$"+(v/1000).toFixed(0)+"K" }},
              grid: {{ color:"rgba(0,0,0,.05)" }} }}
      }}
    }}
  }});
}}

// ── Chart: Region Bar ─────────────────────────────────────────────────────────
function renderRegion(d) {{
  mkChart("cRegion", {{
    type: "bar",
    data: {{
      labels: d.region.labels,
      datasets: [{{ label:"Revenue", data: d.region.revenue,
        backgroundColor: COLORS, borderRadius: 6, borderSkipped: false }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display:false }} }},
      scales: {{
        x: {{ ticks:{{ font:{{ size:10 }} }} }},
        y: {{ ticks:{{ font:{{ size:10 }}, callback: v=>"$"+(v/1000).toFixed(0)+"K" }},
              grid:{{ color:"rgba(0,0,0,.05)" }} }}
      }}
    }}
  }});
}}

// ── Chart: Category Donut ─────────────────────────────────────────────────────
function renderCat(d) {{
  mkChart("cCat", {{
    type: "doughnut",
    data: {{
      labels: d.subcat.labels,
      datasets: [{{ data: d.subcat.revenue,
        backgroundColor: COLORS, borderWidth: 2, borderColor:"#fff",
        hoverOffset: 6 }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false, cutout:"60%",
      plugins: {{
        legend: {{ position:"bottom", labels:{{ boxWidth:12, font:{{ size:10 }} }} }},
        tooltip: {{ callbacks: {{ label: ctx =>
          " $"+ctx.parsed.toLocaleString("en-US",{{minimumFractionDigits:0,maximumFractionDigits:0}})
        }} }}
      }}
    }}
  }});
}}

// ── Chart: Segment Bar ────────────────────────────────────────────────────────
function renderSeg(d) {{
  mkChart("cSeg", {{
    type: "bar",
    data: {{
      labels: d.segment.labels,
      datasets: [{{ label:"Revenue", data: d.segment.revenue,
        backgroundColor:["#2563EB","#16A34A","#EA580C"],
        borderRadius:6, borderSkipped:false }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend:{{ display:false }} }},
      scales: {{
        x: {{ ticks:{{ font:{{ size:10 }} }} }},
        y: {{ ticks:{{ font:{{ size:10 }}, callback: v=>"$"+(v/1000).toFixed(0)+"K" }},
              grid:{{ color:"rgba(0,0,0,.05)" }} }}
      }}
    }}
  }});
}}

// ── Chart: YoY ────────────────────────────────────────────────────────────────
function renderYoy(d) {{
  mkChart("cYoy", {{
    type: "bar",
    data: {{
      labels: d.yoy.years,
      datasets: [
        {{ label:"Revenue", data: d.yoy.revenue, backgroundColor:"#2563EB88",
           borderRadius:6, borderSkipped:false, yAxisID:"y" }},
        {{ label:"Growth %", data: d.yoy.growth, type:"line",
           borderColor:"#EA580C", backgroundColor:"#EA580C22",
           borderWidth:2.5, pointRadius:5, fill:true, yAxisID:"y1" }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend:{{ labels:{{ boxWidth:12, font:{{ size:10 }} }} }} }},
      scales: {{
        x: {{ ticks:{{ font:{{ size:10 }} }} }},
        y: {{ position:"left", ticks:{{ font:{{ size:10 }}, callback: v=>"$"+(v/1000).toFixed(0)+"K" }},
              grid:{{ color:"rgba(0,0,0,.05)" }} }},
        y1:{{ position:"right", ticks:{{ font:{{ size:10 }}, callback: v=>v+"%" }},
               grid:{{ drawOnChartArea:false }} }}
      }}
    }}
  }});
}}

// ── Chart: Top States ────────────────────────────────────────────────────────
function renderState(d) {{
  mkChart("cState", {{
    type: "bar",
    data: {{
      labels: d.state.labels,
      datasets: [{{ label:"Revenue", data: d.state.revenue,
        backgroundColor:"#0D9488", borderRadius:4, borderSkipped:false }}]
    }},
    options: {{
      indexAxis:"y",
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend:{{ display:false }} }},
      scales: {{
        x: {{ ticks:{{ font:{{ size:9 }}, callback: v=>"$"+(v/1000).toFixed(0)+"K" }},
              grid:{{ color:"rgba(0,0,0,.05)" }} }},
        y: {{ ticks:{{ font:{{ size:9 }} }} }}
      }}
    }}
  }});
}}

// ── Chart: Ship Mode ─────────────────────────────────────────────────────────
function renderShip(d) {{
  mkChart("cShip", {{
    type: "pie",
    data: {{
      labels: d.ship.labels,
      datasets: [{{ data: d.ship.revenue,
        backgroundColor: COLORS, borderWidth:2, borderColor:"#fff" }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ position:"bottom", labels:{{ boxWidth:12, font:{{ size:10 }} }} }},
        tooltip: {{ callbacks: {{ label: ctx =>
          ctx.label+": $"+ctx.parsed.toLocaleString("en-US",{{minimumFractionDigits:0,maximumFractionDigits:0}})
        }} }}
      }}
    }}
  }});
}}

// ── Sub-category table ────────────────────────────────────────────────────────
function renderTable(d) {{
  const rows = d.category.labels.map((l,i) => ({{
    label: l, rev: d.category.revenue[i]
  }})).sort((a,b) => b.rev-a.rev);
  const total = rows.reduce((s,r) => s+r.rev, 0);
  document.getElementById("subBody").innerHTML = rows.map((r,i) => {{
    const parts  = r.label.split(" / ");
    const share  = (r.rev/total*100).toFixed(1);
    const cls    = share > 10 ? "high" : share > 5 ? "mid" : "low";
    return `<tr>
      <td>${{i+1}}</td>
      <td>${{parts[0]}}</td><td>${{parts[1]}}</td>
      <td>${{r.rev.toLocaleString("en-US",{{minimumFractionDigits:0,maximumFractionDigits:0}})}}</td>
      <td>—</td>
      <td>${{share}}%</td>
      <td><span class="pill ${{cls}}">${{share>10?"High":share>5?"Medium":"Low"}}</span></td>
    </tr>`;
  }}).join("");
}}

// ── Filter logic ──────────────────────────────────────────────────────────────
function applyFilters() {{
  const yr  = document.getElementById("fYear").value;
  const reg = document.getElementById("fRegion").value;
  const cat = document.getElementById("fCat").value;
  const seg = document.getElementById("fSeg").value;

  // Update badge
  const parts = [yr,reg,cat,seg].filter(x=>x!=="all");
  document.getElementById("filterLabel").textContent =
    parts.length ? parts.join(" · ") : "All Years · All Regions · All Segments";

  // For simplicity filters affect KPI revenue label only (full filter needs raw row data)
  // Monthly chart — filter by year
  const filtMonthly = {{
    ...RAW.monthly,
    years: yr==="all" ? RAW.monthly.years : RAW.monthly.years.filter(y=>String(y)===yr),
    series: yr==="all" ? RAW.monthly.series :
      Object.fromEntries(Object.entries(RAW.monthly.series).filter(([k])=>k===yr))
  }};

  // Region filter on region chart
  let filtRegion = RAW.region;
  if(reg !== "all") {{
    const idx = RAW.region.labels.indexOf(reg);
    filtRegion = {{ labels:[RAW.region.labels[idx]], revenue:[RAW.region.revenue[idx]], orders:[RAW.region.orders[idx]] }};
  }}

  // Segment filter
  let filtSeg = RAW.segment;
  if(seg !== "all") {{
    const idx = RAW.segment.labels.indexOf(seg);
    filtSeg = {{ labels:[RAW.segment.labels[idx]], revenue:[RAW.segment.revenue[idx]], orders:[RAW.segment.orders[idx]] }};
  }}

  renderMonthly({{monthly: filtMonthly}});
  renderRegion({{region: filtRegion}});
  renderSeg({{segment: filtSeg}});
}}

function resetFilters() {{
  ["fYear","fRegion","fCat","fSeg"].forEach(id => document.getElementById(id).value="all");
  document.getElementById("filterLabel").textContent = "All Years · All Regions · All Segments";
  renderAll();
}}

// ── Render all ────────────────────────────────────────────────────────────────
function renderAll() {{
  renderKPIs(RAW.kpis);
  renderInsights(RAW);
  renderMonthly(RAW);
  renderRegion(RAW);
  renderCat(RAW);
  renderSeg(RAW);
  renderYoy(RAW);
  renderState(RAW);
  renderShip(RAW);
  renderTable(RAW);
}}

renderAll();
</script>
</body>
</html>"""

os.makedirs("output", exist_ok=True)
with open("output\\dashboard.html", "w", encoding="utf-8") as f:
    f.write(HTML)

print("Dashboard saved → output\\dashboard.html")
print("Open it in your browser to view!")
