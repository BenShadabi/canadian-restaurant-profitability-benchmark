"""Toronto neighbourhood section: restaurant density and closure rate by neighbourhood and business improvement area (BIA).
Reads the City of Toronto open data in data/toronto_raw/ (run analysis/toronto_download.py first) and writes the small CSVs in data/toronto_*.csv.
Nothing here is profit data: it counts licences. The national profit analysis does not use these files.
Run from the repo root:  python analysis/build_toronto.py
Requires: pandas, openpyxl, shapely
"""
import json, re
import pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

SNAPSHOT = pd.Timestamp("2026-10-21")          # date the data was downloaded
WINDOW_START, WINDOW_END = pd.Timestamp("2023-01-01"), pd.Timestamp("2025-12-31")
CATEGORY = "EATING OR DRINKING ESTABLISHMENT"  # take-out and retail food licences are a separate category and are not counted
MIN_LIVE = 50                                  # below this many licences a neighbourhood or BIA closure rate is too noisy to rank
RAW = "data/toronto_raw/"

WORDS = {"AVENUE": "AVE", "STREET": "ST", "ROAD": "RD", "DRIVE": "DR", "BOULEVARD": "BLVD", "CRESCENT": "CRES", "COURT": "CT", "CRT": "CT",
         "PLACE": "PL", "TERRACE": "TERR", "LANE": "LN", "HIGHWAY": "HWY", "SQUARE": "SQ", "PARKWAY": "PKWY", "TRAIL": "TRL", "CIRCLE": "CIR",
         "WEST": "W", "EAST": "E", "NORTH": "N", "SOUTH": "S", "GARDENS": "GDNS"}
POSTAL = re.compile(r"\b([A-Z]\d[A-Z])\s?(\d[A-Z]\d)\b")


def norm_street(s, keep_unit=False):
    """'1111 Finch Ave W, #5' -> '1111 FINCH AVE W' (or with '#5' kept for telling units apart)."""
    s = str(s).upper()
    unit = ""
    m = re.search(r"#\s*([A-Z0-9-]+)", s)
    if m: unit = m.group(1)
    s = re.split(r",", s)[0]
    s = re.sub(r"#.*", "", s)
    s = re.sub(r"[^A-Z0-9 ]", "", s)
    s = " ".join(WORDS.get(w, w) for w in s.split())
    return f"{s}|{unit}" if keep_unit else s


# ---------- licences ----------
lic = pd.read_csv(RAW + "business_licences.csv", low_memory=False)
lic = lic[lic["Category"] == CATEGORY].copy()
lic["issued"] = pd.to_datetime(lic["Issued"], errors="coerce")
lic["cancel"] = pd.to_datetime(lic["Cancel Date"], errors="coerce")
lic = lic.drop_duplicates("Licence No.", keep="last")
lic["street"] = lic["Licence Address Line 1"].map(norm_street)
lic["street_unit"] = lic["Licence Address Line 1"].map(lambda v: norm_street(v, True))
lic["postal"] = lic["Licence Address Line 3"].astype(str).str.upper().str.extract(POSTAL).fillna("").sum(axis=1)

active = (lic["issued"] <= SNAPSHOT) & (lic["cancel"].isna() | (lic["cancel"] > SNAPSHOT))
live_2023 = (lic["issued"] < WINDOW_START) & (lic["cancel"].isna() | (lic["cancel"] >= WINDOW_START))
ended = live_2023 & lic["cancel"].between(WINDOW_START, WINDOW_END)

# a cancelled licence only counts as a closure when no other licence starts at the same address and unit within 90 days of its cancel date (before or after),
# which filters out owner changes and re-issued licences
by_addr = lic.groupby("street_unit")
issues = {k: list(zip(g["Licence No."], g["issued"])) for k, g in by_addr}
def replaced(row):
    for no, d in issues[row["street_unit"]]:
        if no != row["Licence No."] and pd.notna(d) and abs(d - row["cancel"]) <= pd.Timedelta(days=90): return True
    return False
lic["exit"] = False
lic.loc[ended, "exit"] = [not replaced(r) for _, r in lic[ended].iterrows()]

# ---------- place each licence on the map ----------
ds = pd.read_csv(RAW + "dinesafe.csv", usecols=["estId", "address", "latitude", "longitude"], low_memory=False).drop_duplicates("estId")
ds["postal"] = ds["address"].str.upper().str.extract(POSTAL).fillna("").sum(axis=1)
ds["street"] = ds["address"].str.upper().str.replace(POSTAL, "", regex=True).str.replace(" NONE", "", regex=False).map(norm_street)
addr_xy = ds.groupby("street")[["latitude", "longitude"]].mean()
postal_xy = ds[ds["postal"] != ""].groupby("postal")[["latitude", "longitude"]].mean()

need = lic[active | live_2023].copy()
need["lat"] = need["street"].map(addr_xy["latitude"]); need["lon"] = need["street"].map(addr_xy["longitude"])
need["how"] = need["lat"].notna().map({True: "address match", False: ""})
miss = need["lat"].isna()
need.loc[miss, "lat"] = need.loc[miss, "postal"].map(postal_xy["latitude"]); need.loc[miss, "lon"] = need.loc[miss, "postal"].map(postal_xy["longitude"])
need.loc[miss & need["lat"].notna(), "how"] = "postal code centre"
need.loc[need["lat"].isna(), "how"] = "not placed"
placed = need[need["lat"].notna()].copy()


def assign(points, features, key):
    polys = [shape(f["geometry"]) for f in features]
    tree = STRtree(polys); out = []
    for lon, lat in zip(points["lon"], points["lat"]):
        hit = tree.query(Point(lon, lat), predicate="within")
        out.append(key(features[hit[0]]) if len(hit) else None)
    return out


nb = json.load(open(RAW + "neighbourhoods.geojson"))["features"]
bia = json.load(open(RAW + "bia.geojson"))["features"]
placed["area_code"] = assign(placed, nb, lambda f: f["properties"]["AREA_SHORT_CODE"])
placed["bia"] = assign(placed, bia, lambda f: f["properties"]["AREA_NAME"])
placed["active"], placed["live_2023"], placed["exit"], placed["cancel"] = active[placed.index], live_2023[placed.index], lic.loc[placed.index, "exit"], lic.loc[placed.index, "cancel"]

# ---------- population (2021 census, 158 neighbourhoods) ----------
prof = pd.read_excel(RAW + "neighbourhood_profiles_2021.xlsx", sheet_name=0, header=None)
pop = pd.DataFrame({"area_code": prof.iloc[1, 1:].astype(str).str.zfill(3).values, "neighbourhood": prof.iloc[0, 1:].values,
                    "population_2021": pd.to_numeric(prof.iloc[3, 1:], errors="coerce").values})
assert prof.iloc[3, 0].startswith("Total - Age groups")


def summarise(df, key):
    g = df.groupby(key).agg(active_licences=("active", "sum"), live_at_2023_01_01=("live_2023", "sum"), exits_2023_2025=("exit", "sum")).reset_index()
    g["exit_rate_3yr"] = (g["exits_2023_2025"] / g["live_at_2023_01_01"].where(g["live_at_2023_01_01"] > 0)).round(4)
    return g


per_nb = summarise(placed, "area_code")
per_nb = pop.merge(per_nb, on="area_code", how="left").fillna({"active_licences": 0, "live_at_2023_01_01": 0, "exits_2023_2025": 0})
per_nb["per_1000_residents"] = (per_nb["active_licences"] / per_nb["population_2021"] * 1000).round(2)
per_nb["low_sample"] = per_nb["live_at_2023_01_01"] < MIN_LIVE
per_nb = per_nb[["area_code", "neighbourhood", "population_2021", "active_licences", "per_1000_residents", "live_at_2023_01_01", "exits_2023_2025", "exit_rate_3yr", "low_sample"]]
per_nb.to_csv("data/toronto_neighbourhoods.csv", index=False)

per_bia = summarise(placed.dropna(subset=["bia"]), "bia").rename(columns={"bia": "bia_name"})
per_bia["low_sample"] = per_bia["live_at_2023_01_01"] < MIN_LIVE
per_bia.sort_values("active_licences", ascending=False).to_csv("data/toronto_bia.csv", index=False)

# ---------- how well the licences were placed ----------
n_all = int((active | live_2023).sum())
summary = [("licences_in_scope", n_all, "eating or drinking licences active on the download date or live on 2023-01-01"),
           ("address_match", int((need["how"] == "address match").sum()), "placed by matching the street address to a DineSafe premises"),
           ("postal_code_centre", int((need["how"] == "postal code centre").sum()), "placed at the average position of DineSafe premises with the same postal code (approximate)"),
           ("not_placed", int((need["how"] == "not placed").sum()), "no address or postal code match, left out of every neighbourhood figure"),
           ("outside_neighbourhoods", int(placed["area_code"].isna().sum()), "placed, but outside all 158 neighbourhood boundaries"),
           ("raw_cancellations_2023_2025", int((placed["live_2023"] & placed["cancel"].between(WINDOW_START, WINDOW_END)).sum()), "placed licences cancelled in the window, before removing re-issued addresses"),
           ("exits_2023_2025", int(placed["exit"].sum()), "of those, cancellations with no new licence at the same address and unit within 90 days"),
           ("active_total_all_toronto", int(active.sum()), "active licences, including any not placed")]
pd.DataFrame(summary, columns=["item", "count", "meaning"]).to_csv("data/toronto_match_summary.csv", index=False)
placed[["Licence No.", "lat", "lon", "how", "area_code", "active", "live_2023", "exit", "issued", "cancel"]].to_csv(RAW + "placed_licences.csv", index=False)  # raw folder only, used by build_toronto_construction.py
print(pd.DataFrame(summary, columns=["item", "count", "meaning"]).iloc[:, :2].to_string(index=False))
print(per_nb.sort_values("per_1000_residents", ascending=False).head(5).to_string(index=False))
