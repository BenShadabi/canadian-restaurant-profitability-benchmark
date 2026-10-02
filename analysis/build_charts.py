"""Rebuild every chart in assets/ from the CSV files in data/.
Run from the repo root:  python analysis/build_charts.py
Requires: pandas, matplotlib
"""
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NAVY, GOLD, SLATE, GREY, GREEN, RED = "#12355B", "#B7791F", "#5B7189", "#4B5563", "#1B7F5C", "#B42318"
BLUE, ORANGE = NAVY, GOLD  # full-service = navy, limited-service = gold (dashed); same colours as docs/index.html
plt.rcParams.update({"axes.axisbelow": True, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#9CA3AF", "axes.labelcolor": GREY, "xtick.color": GREY, "ytick.color": GREY,
                     "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlecolor": NAVY, "axes.titlelocation": "left"})

ind = pd.read_csv("data/industry_trend.csv")
avg = pd.read_csv("data/average_restaurant_2024.csv").set_index("line")["dollars"]
wag = pd.read_csv("data/wages_food_services.csv")

# ---- scenario maths (same as the Scenario tab in the workbook) ----
rev, cos, lab, util = avg["revenue"], avg["cost_of_sales"], avg["labour_and_commissions"], avg["utilities_and_telecom"]
other = rev - cos - lab - avg["rent"] - util - avg["amortization_and_depletion"] - avg["net_profit"]
LAB_CUT, OH_CUT, WASTE_SHARE, WASTE_CUT = 0.10, 0.15, 0.05, 0.20
gain_lab = lab * LAB_CUT
gain_oh = (util + other) * OH_CUT
gain_waste = cos * WASTE_SHARE * WASTE_CUT
profit0 = avg["net_profit"]; profit1 = profit0 + gain_lab + gain_oh + gain_waste

def line_segments(ax):
    ax.plot(ind.year, ind.full_service_revenue_bn, color=BLUE, lw=2.4, marker="o", ms=5, label="Full-service restaurants")
    ax.plot(ind.year, ind.limited_service_revenue_bn, color=ORANGE, lw=2.4, marker="s", ms=5, ls="--", label="Limited-service eating places")
    ax.set_title("Limited-service revenue led in 2020, 2021, 2024 ($B)"); ax.set_ylim(0, 50); ax.grid(axis="y", color="#D5DAE1")
    ax.text(2024.08, ind.full_service_revenue_bn.iloc[-1] - 3.2, "Full-service", color=BLUE, fontsize=9, ha="right")
    ax.text(2024.08, ind.limited_service_revenue_bn.iloc[-1] + 1.5, "Limited-service", color=ORANGE, fontsize=9, ha="right")
def margin_seg(ax):
    d = ind.dropna(subset=["full_service_margin"])
    ax.plot(d.year, d.full_service_margin * 100, color=BLUE, lw=2.4, marker="o", ms=5, label="Full-service")
    ax.plot(d.year, d.limited_service_margin * 100, color=ORANGE, lw=2.4, marker="s", ms=5, ls="--", label="Limited-service")
    ax.set_title("2020: full-service margin fell to 0.3% (%), 2019-2022"); ax.set_ylim(0, 8); ax.set_xticks(d.year); ax.grid(axis="y", color="#D5DAE1")
    ax.annotate("2020: full-service 0.3%\nvs limited-service 5.3%", xy=(2020, 0.3), xytext=(2020.35, 2.2), fontsize=9, color=NAVY,
                arrowprops=dict(arrowstyle="-", color="#9CA3AF"))
    ax.legend(frameon=False, fontsize=9, loc="upper right")
def margin_all(ax):
    ax.plot(ind.year, ind.operating_margin * 100, color=NAVY, lw=2.4, marker="o", ms=5)
    ax.set_title("Industry operating margin (%), Statistics Canada"); ax.set_ylim(0, 6); ax.grid(axis="y", color="#D5DAE1")
    for x, y in zip(ind.year, ind.operating_margin * 100): ax.text(x, y + 0.25, f"{y:.1f}", ha="center", fontsize=9, color=NAVY)
def structure(ax):
    items = [("Cost of sales", cos), ("Labour", lab), ("Other expenses (calculated)", other), ("Rent", avg["rent"]),
             ("Amortization", avg["amortization_and_depletion"]), ("Utilities", util), ("Net profit", avg["net_profit"])]
    labs = [i[0] for i in items][::-1]; vals = [i[1] / rev * 100 for i in items][::-1]
    cols = [GREEN if l == "Net profit" else SLATE for l in labs]
    ax.barh(labs, vals, color=cols, height=0.62)
    for y, v in enumerate(vals): ax.text(v + 0.6, y, f"{v:.1f}%", va="center", fontsize=9, color=NAVY)
    ax.set_title("Cost of sales and labour take 68 cents\nof each dollar (2024, % of revenue)"); ax.set_xlim(0, 55); ax.xaxis.set_visible(False)
    ax.spines["bottom"].set_visible(False)
def waterfall(ax):
    steps = [("Profit\nbefore", profit0, None), ("Labour\n-10%", gain_lab, GREEN), ("Overhead\n-15%", gain_oh, GREEN),
             ("Waste\n-20%", gain_waste, GREEN), ("Profit\nafter", profit1, None)]
    run = 0
    for i, (l, v, c) in enumerate(steps):
        if c is None:
            ax.bar(i, v, color=NAVY, width=0.6); run = v; ax.text(i, v + 1500, f"${v:,.0f}", ha="center", fontsize=9, color=NAVY)
        else:
            ax.bar(i, v, bottom=run, color=c, width=0.6); ax.text(i, run + v + 1500, f"+${v:,.0f}", ha="center", fontsize=9, color=NAVY); run += v
    ax.set_xticks(range(len(steps))); ax.set_xticklabels([s[0] for s in steps], fontsize=9)
    ax.set_title("What-if: three levers lift profit \\$21,500 to \\$68,169\n(assumes waste = 5% of cost of sales)"); ax.set_ylim(0, profit1 * 1.15); ax.yaxis.set_major_formatter(lambda x, p: f"${x/1000:.0f}k")
    ax.grid(axis="y", color="#D5DAE1")
def wages(ax):
    ax.bar(wag.year, wag.avg_hourly_wage_cad, color=SLATE, width=0.6)
    ax.set_title("Hourly pay up 16.1% since 2020 (axis starts at $0)"); ax.set_ylim(0, 24); ax.grid(axis="y", color="#D5DAE1")
    for x, y in zip(wag.year, wag.avg_hourly_wage_cad): ax.text(x, y + 0.4, f"${y:.2f}", ha="center", fontsize=9, color=NAVY)
    ax.set_xticks(wag.year)

panels = [("revenue_by_segment", line_segments), ("margin_by_segment", margin_seg), ("industry_margin", margin_all),
          ("cost_structure", structure), ("scenario_waterfall", waterfall), ("wages", wages)]
for name, fn in panels:
    f, ax = plt.subplots(figsize=(7, 4.2), dpi=150); fn(ax); f.tight_layout(); f.savefig(f"assets/{name}.png"); plt.close(f)

fig, axes = plt.subplots(2, 3, figsize=(18, 9.6), dpi=140)
for ax, (_, fn) in zip(axes.flat, panels): fn(ax)
fig.suptitle("Canadian Restaurant Profitability Benchmark: key charts", x=0.012, ha="left", fontsize=20, fontweight="bold", color=NAVY)
fig.text(0.012, 0.935, "Sources: Statistics Canada, ISED. Net margin (ISED) and operating margin (Statistics Canada) are different bases. Scenario is a what-if, not a forecast.", fontsize=10, color=GREY)
fig.tight_layout(rect=(0, 0, 1, 0.92)); fig.savefig("assets/dashboard.png"); plt.close(fig)
print(f"profit before {profit0:,.0f} after {profit1:,.0f}  (+{profit1/profit0-1:.0%});  gains lab {gain_lab:,.0f} oh {gain_oh:,.0f} waste {gain_waste:,.0f}; other expenses {other:,.0f}")
