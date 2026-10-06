"""Build the conservative case, the per-1% lever table and the waste-share range from data/.
Writes data/scenario_cases.csv, data/lever_per_point.csv, data/waste_share_range.csv and assets/lever_per_point.png.
Run from the repo root:  python analysis/build_scenarios.py        Requires: pandas, matplotlib
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import scenario

NAVY, GOLD, GREY, INK = "#12355B", "#B7791F", "#4B5563", "#0F1B2D"
s = scenario.load()

# ---- the two cases side by side ----
cases = pd.DataFrame([
    {"case": "Before", "labour_gain": 0, "overhead_gain": 0, "waste_gain": 0, "profit": s["profit"], "margin": s["margin_before"],
     "note": "ISED average restaurant, 2024"},
    {"case": "Conservative", "labour_gain": s["gain_lab"], "overhead_gain": s["gain_util"], "waste_gain": s["gain_waste"],
     "profit": s["conservative"], "margin": s["margin_conservative"], "note": "Overhead = published utilities and telecom line only"},
    {"case": "Headline", "labour_gain": s["gain_lab"], "overhead_gain": s["gain_oh"], "waste_gain": s["gain_waste"],
     "profit": s["headline"], "margin": s["margin_headline"], "note": "Overhead = utilities + calculated other expenses"},
])
cases.round(4).to_csv("data/scenario_cases.csv", index=False)

# ---- profit gain from a 1% cut in each cost line ----
pp = pd.DataFrame({"line": list(s["per_point"]), "profit_gain_per_1pct_cut": [round(v) for v in s["per_point"].values()]})
pp = pp.sort_values("profit_gain_per_1pct_cut", ascending=False)
pp.to_csv("data/lever_per_point.csv", index=False)

# ---- how much the assumed waste share matters ----
pd.DataFrame(s["waste_range"]).round(2).to_csv("data/waste_share_range.csv", index=False)

# ---- chart: one series, sorted, labelled directly, no legend ----
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.spines.left": False, "axes.spines.bottom": False})
fig, ax = plt.subplots(figsize=(7, 3.4), dpi=150)
labels = list(pp["line"])[::-1]
vals = list(pp["profit_gain_per_1pct_cut"])[::-1]
ax.barh(labels, vals, color=NAVY, height=0.5)
for y, v in enumerate(vals):
    ax.text(v + 60, y, f"${v:,.0f}", va="center", fontsize=10, color=INK)
ax.set_xlim(0, max(vals) * 1.18)
ax.xaxis.set_visible(False)
ax.tick_params(axis="y", length=0, labelsize=10, labelcolor=INK)
fig.text(0.012, 0.94, "A 1% cut to cost of sales is worth almost twice a 1% cut to labour", fontsize=12, fontweight="bold", color=NAVY, va="top")
fig.text(0.012, 0.865, "Annual profit gain from a 1% cut in each cost line, average restaurant, 2024", fontsize=9, color=GREY, va="top")
fig.text(0.012, 0.02, "Overhead includes the calculated 'other expenses' line, which is not a published figure. Source: ISED, Canadian Industry Statistics.",
         fontsize=7.5, color=GREY)
fig.tight_layout(rect=(0, 0.05, 1, 0.82))
fig.savefig("assets/lever_per_point.png")
plt.close(fig)

print(f"conservative {s['conservative']:,.0f} ({s['margin_conservative']*100:.1f}%)  headline {s['headline']:,.0f} ({s['margin_headline']*100:.1f}%)")
print(pp.to_string(index=False))
