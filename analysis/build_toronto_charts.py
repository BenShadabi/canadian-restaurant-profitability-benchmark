"""Toronto charts: assets/toronto_map.png and assets/toronto_rankings.png, from data/toronto_neighbourhoods.csv and the boundary file.
Run from the repo root after build_toronto.py:  python analysis/build_toronto_charts.py
Requires: pandas, matplotlib, shapely
"""
import json
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon
from shapely.geometry import shape

NAVY, GOLD, GREY = "#12355B", "#B7791F", "#4B5563"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#9CA3AF",
                     "axes.labelcolor": GREY, "xtick.color": GREY, "ytick.color": GREY, "axes.titleweight": "bold", "axes.titlesize": 12,
                     "axes.titlecolor": NAVY, "axes.titlelocation": "left"})
nb = pd.read_csv("data/toronto_neighbourhoods.csv", dtype={"area_code": str})
feats = json.load(open("data/toronto_raw/neighbourhoods.geojson"))["features"]
geo = {f["properties"]["AREA_SHORT_CODE"]: shape(f["geometry"]) for f in feats}
rank = nb[~nb["low_sample"]].copy()


def draw(ax, values, cmap, title, note, grey_missing=True):
    patches, cols = [], []
    for code, g in geo.items():
        row = nb[nb.area_code == code].iloc[0]; v = values.get(code)
        for poly in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
            patches.append(MplPolygon(np.array(poly.exterior.coords), closed=True)); cols.append(v)
    pc = PatchCollection(patches, edgecolor="white", linewidth=0.4)
    arr = np.array([np.nan if c is None else c for c in cols], dtype=float)
    cm = plt.get_cmap(cmap).copy(); cm.set_bad("#E5E7EB")
    pc.set_array(np.ma.masked_invalid(arr)); pc.set_cmap(cm)
    ax.add_collection(pc); ax.autoscale_view(); ax.set_aspect(1 / np.cos(np.radians(43.7))); ax.axis("off")
    ax.set_title(title); ax.text(0.0, -0.03, note, transform=ax.transAxes, fontsize=8.5, color=GREY, va="top")
    return pc


fig, axes = plt.subplots(1, 2, figsize=(15, 5.6), dpi=140)
dens = {r.area_code: r.per_1000_residents for r in nb.itertuples()}
pc = draw(axes[0], dens, "Blues", "Licensed restaurants and bars per 1,000 residents", "Residents are 2021 census counts. Downtown cores look high because many customers do not live there.")
cb = fig.colorbar(pc, ax=axes[0], shrink=0.6, pad=0.01); cb.outline.set_visible(False)
exits = {r.area_code: r.exit_rate_3yr for r in nb.itertuples() if not r.low_sample}
pc2 = draw(axes[1], exits, "YlOrBr", "Share of licences that ended, 2023 to 2025", "Grey = fewer than 50 licences, too few to compare. Licence data, not profit.")
cb2 = fig.colorbar(pc2, ax=axes[1], shrink=0.6, pad=0.01, format=lambda v, p: f"{v:.0%}"); cb2.outline.set_visible(False)
fig.suptitle("Toronto restaurants by neighbourhood (licences active on 2026-10-21)", x=0.012, ha="left", fontsize=15, fontweight="bold", color=NAVY)
fig.tight_layout(rect=(0, 0.02, 1, 0.93)); fig.savefig("assets/toronto_map.png"); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(15, 6.4), dpi=140)
top = nb.sort_values("per_1000_residents", ascending=False).head(10).iloc[::-1]
axes[0].barh(top.neighbourhood, top.per_1000_residents, color=NAVY, height=0.62)
for y, (v, n) in enumerate(zip(top.per_1000_residents, top.active_licences)): axes[0].text(v + 0.2, y, f"{v:.1f}  ({n} licences)", va="center", fontsize=9, color=NAVY)
axes[0].set_title("Most licensed restaurants and bars per 1,000 residents"); axes[0].set_xlim(0, top.per_1000_residents.max() * 1.45); axes[0].xaxis.set_visible(False); axes[0].spines["bottom"].set_visible(False)
hi, lo = rank.sort_values("exit_rate_3yr", ascending=False).head(6), rank.sort_values("exit_rate_3yr").head(6)
both = pd.concat([lo, hi]).iloc[::-1]
axes[1].barh(both.neighbourhood, both.exit_rate_3yr * 100, color=[GOLD if r >= hi.exit_rate_3yr.min() else NAVY for r in both.exit_rate_3yr], height=0.62)
for y, (v, n) in enumerate(zip(both.exit_rate_3yr, both.live_at_2023_01_01)): axes[1].text(v * 100 + 0.3, y, f"{v:.1%}  (of {n})", va="center", fontsize=9, color=NAVY)
axes[1].set_title("Licences that ended, 2023 to 2025: lowest and highest six\n(neighbourhoods with 50+ licences only)"); axes[1].set_xlim(0, both.exit_rate_3yr.max() * 100 * 1.4); axes[1].xaxis.set_visible(False); axes[1].spines["bottom"].set_visible(False)
fig.suptitle("Toronto neighbourhood rankings: counts of licences, not profit", x=0.012, ha="left", fontsize=15, fontweight="bold", color=NAVY)
fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig("assets/toronto_rankings.png"); plt.close(fig)
print("rankable neighbourhoods:", len(rank))
