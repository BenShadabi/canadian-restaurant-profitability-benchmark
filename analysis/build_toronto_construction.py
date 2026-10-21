"""Exploratory check: were Toronto restaurant and bar licences near large construction sites more likely to end in 2023 to 2025?
Reads the raw City of Toronto files in data/toronto_raw/ (run toronto_download.py and build_toronto.py first) and writes data/toronto_construction.csv.
Large construction site = a building permit (cleared or active) with an estimated cost of at least $5M, located by its City address point. A site is active
in the window if it was issued by 2025-12-31 and not completed before 2023-01-01. This is a rough proxy: Metrolinx transit works are not in City permits.
Comparison is within each neighbourhood (licences near a site against licences in the same neighbourhood that are not), pooled with Mantel-Haenszel weights,
with a confidence interval from resampling neighbourhoods. It shows association, not cause.
Run from the repo root:  python analysis/build_toronto_construction.py     Requires: pandas, numpy, scipy
"""
import json
import numpy as np, pandas as pd
from scipy.spatial import cKDTree

RAW = "data/toronto_raw/"
W0, W1 = pd.Timestamp("2023-01-01"), pd.Timestamp("2025-12-31")
rng = np.random.default_rng(2026)

lic = pd.read_csv(RAW + "placed_licences.csv", dtype={"area_code": str})
lic = lic[lic["live_2023"] & (lic["how"] == "address match")].reset_index(drop=True)   # only licences placed from a street address, so distances mean something
lic["exit"] = lic["exit"].astype(int)

# ---------- construction sites ----------
ap = pd.read_csv(RAW + "address_points.csv", usecols=["ADDRESS_POINT_ID", "geometry"], low_memory=False)
xy = ap["geometry"].map(lambda g: json.loads(g)["coordinates"][0])
ap["lon"], ap["lat"] = xy.map(lambda c: c[0]), xy.map(lambda c: c[1])
ap = ap.drop_duplicates("ADDRESS_POINT_ID").set_index("ADDRESS_POINT_ID")
cols = ["PERMIT_NUM", "PERMIT_TYPE", "GEO_ID", "ISSUED_DATE", "COMPLETED_DATE", "STATUS", "EST_CONST_COST"]
bp = pd.concat([pd.read_csv(RAW + f, usecols=cols, low_memory=False) for f in ("building_permits_cleared.csv", "building_permits_active.csv")])
bp = bp[~bp["STATUS"].isin(["Cancelled", "Superseded"])]
bp["cost"] = pd.to_numeric(bp["EST_CONST_COST"], errors="coerce")
bp["issued"] = pd.to_datetime(bp["ISSUED_DATE"], errors="coerce"); bp["done"] = pd.to_datetime(bp["COMPLETED_DATE"], errors="coerce")
bp["GEO_ID"] = pd.to_numeric(bp["GEO_ID"], errors="coerce")
bp = bp.dropna(subset=["GEO_ID"]).astype({"GEO_ID": "int64"})
bp = bp.join(ap[["lat", "lon"]], on="GEO_ID").dropna(subset=["lat", "lon", "issued"])


def to_m(lat, lon):  # local metres around Toronto
    return np.c_[(lon + 79.38) * 111320 * np.cos(np.radians(43.7)), (lat - 43.65) * 110574]


def sites(min_cost, kind):
    s = bp[bp["cost"] >= min_cost]
    if kind == "active":      # under way at some point in 2023 to 2025
        s = s[(s["issued"] <= W1) & (s["done"].isna() | (s["done"] >= W0))]
    else:                     # finished 2017 to 2021 and not under way in the window (placebo)
        s = s[(s["done"] >= "2017-01-01") & (s["done"] < W0) & (s["issued"] < W0)]
    return s.drop_duplicates("GEO_ID")


P = to_m(lic["lat"].values, lic["lon"].values)


def near_count(s, radius):
    tree = cKDTree(to_m(s["lat"].values, s["lon"].values))
    return np.array([len(x) for x in tree.query_ball_point(P, r=radius)])


def mh(df, exposed):
    """Mantel-Haenszel pooled risk difference (exposed minus unexposed) across neighbourhoods, with a cluster bootstrap CI."""
    df = df.assign(e=exposed)
    g = df.groupby(["area_code", "e"])["exit"].agg(["sum", "count"]).unstack("e").fillna(0)
    g = g[(g[("count", True)] > 0) & (g[("count", False)] > 0)]
    def pooled(t):
        n1, n0 = t[("count", True)].values, t[("count", False)].values
        d = t[("sum", True)].values / n1 - t[("sum", False)].values / n0
        w = n1 * n0 / (n1 + n0)
        return (w * d).sum() / w.sum()
    est = pooled(g)
    boots = [pooled(g.iloc[rng.integers(0, len(g), len(g))]) for _ in range(2000)]
    return est, np.percentile(boots, 2.5), np.percentile(boots, 97.5), len(g)


rows = []
def run(label, s, radius, dose=None):
    c = near_count(s, radius)
    exposed = (c >= 1) if dose is None else ((c >= dose[0]) & (c <= dose[1]))
    base = df_all if dose is None else df_all[(c == 0) | exposed]
    ex = exposed if dose is None else exposed[(c == 0) | exposed]
    est, lo, hi, k = mh(base, ex)
    rows.append({"analysis": label, "radius_m": radius, "sites": len(s), "licences_exposed": int(ex.sum()), "exits_exposed": int(base["exit"][ex].sum()),
                 "rate_exposed": round(base["exit"][ex].mean(), 4), "licences_unexposed": int((~ex).sum()), "exits_unexposed": int(base["exit"][~ex].sum()),
                 "rate_unexposed": round(base["exit"][~ex].mean(), 4), "adjusted_difference": round(est, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4), "neighbourhoods_compared": k})


df_all = lic
main = sites(5e6, "active")
run("Large site ($5M+) active 2023-2025, within 150 m", main, 150)
run("Same, within 75 m", main, 75)
run("Same, within 300 m", main, 300)
run("Larger sites only ($20M+), within 150 m", sites(2e7, "active"), 150)
run("Placebo: sites finished 2017-2021, within 150 m", sites(5e6, "past"), 150)
c = near_count(main, 150)
run("Dose: 1 to 2 active large sites within 150 m", main, 150, dose=(1, 2))
run("Dose: 3 or more active large sites within 150 m", main, 150, dose=(3, 10**6))
out = pd.DataFrame(rows); out.to_csv("data/toronto_construction.csv", index=False)
print(out.to_string(index=False))
print("licences analysed:", len(lic), "overall exit rate", round(lic["exit"].mean(), 4), "major active sites:", len(main))
