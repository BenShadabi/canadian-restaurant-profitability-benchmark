"""Build docs/toronto.html (the interactive Toronto neighbourhood page) from data/toronto_*.csv and the neighbourhood boundaries.
Every number on the page is read from the CSVs. The map is drawn as inline SVG, so the page needs no libraries and no network.
Run from the repo root after build_toronto.py:  python analysis/build_toronto_page.py
Requires: pandas, shapely
"""
import html, json, math, shutil
import pandas as pd
from shapely.geometry import shape

nb = pd.read_csv("data/toronto_neighbourhoods.csv", dtype={"area_code": str})
bia = pd.read_csv("data/toronto_bia.csv")
ms = pd.read_csv("data/toronto_match_summary.csv").set_index("item")["count"]
e, n = html.escape, lambda v: f"{int(v):,}"
rank = nb[~nb.low_sample]
placed_active = int(nb.active_licences.sum())
city_density = placed_active / nb.population_2021.sum() * 1000
city_exit = nb.exits_2023_2025.sum() / nb.live_at_2023_01_01.sum()
raw_exit = ms["raw_cancellations_2023_2025"] / nb.live_at_2023_01_01.sum()
top_d = nb.sort_values("per_1000_residents", ascending=False).iloc[0]
lo_x, hi_x = rank.sort_values("exit_rate_3yr").iloc[0], rank.sort_values("exit_rate_3yr").iloc[-1]
bia_rows = bia[~bia.low_sample].sort_values("active_licences", ascending=False).head(10)
bia_html = "".join(f"<tr><td>{e(r.bia_name)}</td><td>{n(r.active_licences)}</td><td>{n(r.live_at_2023_01_01)}</td><td>{r.exit_rate_3yr:.1%}</td></tr>" for r in bia_rows.itertuples())
for f in ("toronto_map.png", "toronto_rankings.png"): shutil.copy(f"assets/{f}", f"docs/{f}")  # still used by the README

# ---------- map: simplify the boundaries and project them to SVG paths ----------
feats = json.load(open("data/toronto_raw/neighbourhoods.geojson"))["features"]
geoms = {f["properties"]["AREA_SHORT_CODE"]: shape(f["geometry"]).simplify(0.0004, preserve_topology=True) for f in feats}
minx = min(g.bounds[0] for g in geoms.values()); maxx = max(g.bounds[2] for g in geoms.values())
miny = min(g.bounds[1] for g in geoms.values()); maxy = max(g.bounds[3] for g in geoms.values())
k = math.cos(math.radians(43.7)); scale = 1000 / ((maxx - minx) * k)
W, H = 1000, round((maxy - miny) * scale)
def path(g):
    out = []
    for poly in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        pts = [f"{(x - minx) * k * scale:.1f},{(maxy - y) * scale:.1f}" for x, y in poly.exterior.coords]
        out.append("M" + "L".join(pts) + "Z")
    return "".join(out)
paths = "".join(f'<path data-c="{c}" d="{path(g)}"/>' for c, g in geoms.items())
data = [{"c": r.area_code, "n": r.neighbourhood, "p": int(r.population_2021), "a": int(r.active_licences), "d": float(r.per_1000_residents),
         "l": int(r.live_at_2023_01_01), "x": int(r.exits_2023_2025), "r": None if pd.isna(r.exit_rate_3yr) else float(r.exit_rate_3yr), "low": bool(r.low_sample)}
        for r in nb.itertuples()]
rank_density = [[r.neighbourhood, float(r.per_1000_residents), int(r.active_licences)] for r in nb.sort_values("per_1000_residents", ascending=False).head(10).itertuples()]
rank_exit_lo = [[r.neighbourhood, float(r.exit_rate_3yr), int(r.live_at_2023_01_01)] for r in rank.sort_values("exit_rate_3yr").head(6).itertuples()]
rank_exit_hi = [[r.neighbourhood, float(r.exit_rate_3yr), int(r.live_at_2023_01_01)] for r in rank.sort_values("exit_rate_3yr", ascending=False).head(6).itertuples()]


# ---------- construction section (data/toronto_construction.csv) ----------
cx = pd.read_csv("data/toronto_construction.csv").set_index("analysis")
main_r = cx.iloc[0]; r20 = cx.loc["Larger sites only ($20M+), within 150 m"]; plc = cx.loc["Placebo: sites finished 2017-2021, within 150 m"]
dose3 = cx.loc["Dose: 3 or more active large sites within 150 m"]
pp = lambda v: f"{v * 100:+.1f}"
def forest():
    items = [("Large site ($5M+) under way 2023 to 2025, within 150 m", main_r, "var(--link)"), ("Larger sites only ($20M+)", r20, "var(--link)"),
             ("3 or more large sites under way nearby", dose3, "var(--link)"), ("Placebo: sites finished in 2017 to 2021", plc, "var(--gold)")]
    lo, hi, W_, L = -4.0, 14.0, 760, 10
    x = lambda v: L + (v - lo) / (hi - lo) * (W_ - L - 20)
    out = [f'<svg style="width:100%;height:auto" viewBox="0 0 {W_} {40 + 46 * len(items)}" role="img" aria-label="Estimated difference in licence closure share, in percentage points, with 95% ranges, for four comparisons.">']
    for t in (-4, 0, 4, 8, 12):
        out.append(f'<line x1="{x(t):.0f}" x2="{x(t):.0f}" y1="14" y2="{22 + 46 * len(items)}" stroke="var(--grid)" stroke-width="{2 if t == 0 else 1}"/><text x="{x(t):.0f}" y="{38 + 46 * len(items)}" text-anchor="middle" font-size="12" fill="var(--muted)">{t:+d}</text>')
    for i, (name, r, col) in enumerate(items):
        y = 40 + 46 * i
        out.append(f'<text x="0" y="{y - 12}" font-size="13" fill="var(--ink)">{html.escape(name)}</text>'
                   f'<line x1="{x(r.ci_low * 100):.1f}" x2="{x(r.ci_high * 100):.1f}" y1="{y}" y2="{y}" stroke="{col}" stroke-width="3" stroke-linecap="round"/>'
                   f'<circle cx="{x(r.adjusted_difference * 100):.1f}" cy="{y}" r="6" fill="{col}"/>')
    return "".join(out) + "</svg>"
construction = f"""<h2 class="rv" id="construction">Do closures go with construction nearby?</h2>
<p class="sub rv">An exploratory check, and the answer is "not clearly". I took the {n(main_r.licences_exposed + main_r.licences_unexposed)} restaurant and bar licences that were live on 1 January 2023 and could be placed from a street address, and asked whether the ones within 150 m of a large construction site were more likely to end by the end of 2025. A large site is a City building permit with an estimated cost of $5 million or more ({n(main_r.sites)} sites under way at some point in 2023 to 2025).</p>
<div class="card rv" style="padding:20px">
<div class="cols" style="grid-template-columns:repeat(3,minmax(0,1fr))">
<div><b style="font-size:1.6rem">{main_r.rate_exposed:.1%}</b><br><span class="sub">of licences near a large site ended ({n(main_r.licences_exposed)} licences)</span></div>
<div><b style="font-size:1.6rem">{main_r.rate_unexposed:.1%}</b><br><span class="sub">of other licences ended ({n(main_r.licences_unexposed)} licences)</span></div>
<div><b style="font-size:1.6rem">{pp(main_r.adjusted_difference)} points</b><br><span class="sub">gap after comparing within each neighbourhood (95% range {pp(main_r.ci_low)} to {pp(main_r.ci_high)})</span></div></div>
<h3 style="font:700 1rem var(--sans);margin:22px 0 4px">Gap in the share of licences that ended, in percentage points</h3>
{forest()}
<p class="sub" style="font-size:.875rem;margin:6px 0 0">Dot = estimate, line = 95% range from resampling neighbourhoods. A line that crosses zero means the data cannot rule out no difference.</p></div>
<div class="limits rv" style="margin-top:16px">
<div class="card"><b>What it can show</b><p>Licences near large construction sites ended more often than other licences in the same neighbourhood: {pp(main_r.adjusted_difference)} points, a bit larger for the biggest sites ({pp(r20.adjusted_difference)}) and for 3 or more sites nearby ({pp(dose3.adjusted_difference)}, but only {n(dose3.neighbourhoods_compared)} neighbourhoods have both groups).</p></div>
<div class="card"><b>What it cannot show</b><p>That construction caused closures. The placebo comparison, sites that were already finished before 2022, shows a gap of {pp(plc.adjusted_difference)} points, as large as or larger than the main one. So the gap looks like a feature of the places (busy, redeveloping, higher rents), not of the dust and noise in 2023 to 2025.</p></div>
<div class="card"><b>What it misses</b><p>Metrolinx transit works (the Eglinton Crosstown, Ontario Line and Finch West LRT) are not in City building permits, so the construction people worry about most is not in this test. It also cannot see rent rises, ownership changes or why a licence was cancelled.</p></div>
</div>
<p class="sub rv" style="margin-top:12px">Method and files: <code>analysis/build_toronto_construction.py</code> and <code>data/toronto_construction.csv</code> (building permits, address points, licences). Sites are located by the City's address point for each permit. A permit's end date is when the City closed the file, which can be later than the real end of building work, so "under way" is generous. The placebo and main groups overlap (a licence can be near both kinds of site), which blurs the comparison a little.</p>
"""

TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark">
<title>Toronto restaurants by neighbourhood | Ben Shadabi</title>
<meta name="description" content="An interactive map of licensed restaurants and bars per 1,000 residents and licence closure shares for Toronto's 158 neighbourhoods. Licence counts, not profit.">
<meta property="og:title" content="Toronto restaurants by neighbourhood"><meta property="og:description" content="Interactive map of restaurant licences and closures across Toronto's 158 neighbourhoods. Licence counts, not profit.">
<style>
@font-face{font-family:Geist;src:url(fonts/geist-latin-wght.woff2) format("woff2");font-weight:100 900;font-display:swap}
:root{color-scheme:light dark;--ink:#0F1B2D;--muted:#4B5563;--grid:#D5DAE1;--bg:#F4F6F9;--card:#fff;--note:#FFF6E0;--gold:#B7791F;--link:#12355B;--r:12px;
--d0:#E6EEF8;--d1:#12355B;--e0:#FBEFD0;--e1:#8A4B0F;--none:#DDE2EA;--stroke:#fff;--shadow:0 1px 2px rgba(15,27,45,.06),0 8px 24px rgba(15,27,45,.06);
--sans:Geist,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
@media(prefers-color-scheme:dark){:root{--ink:#E8EEF6;--muted:#A7B4C6;--grid:#2A3750;--bg:#0A111F;--card:#111B2E;--note:#2A2412;--gold:#D19A3C;--link:#9CC3F0;
--d0:#1B2B47;--d1:#7DB4F2;--e0:#3A2C12;--e1:#F0B35A;--none:#243049;--stroke:#0A111F;--shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.25)}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.65 var(--sans);font-variant-numeric:tabular-nums}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px}
a{color:var(--link)}a:focus-visible,button:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
header{position:relative;overflow:hidden;background:linear-gradient(135deg,#0B2038,#12355B 55%,#0E2745);color:#fff;padding:56px 0 64px;border-bottom:4px solid #E3B965}
header:before{content:"";position:absolute;inset:-40%;background:radial-gradient(circle at 20% 30%,rgba(227,185,101,.22),transparent 40%),radial-gradient(circle at 80% 70%,rgba(125,180,242,.18),transparent 45%);animation:drift 18s ease-in-out infinite alternate}
@keyframes drift{to{transform:translate3d(4%,3%,0) scale(1.08)}}
header .wrap{position:relative}
.eyebrow{font-size:.8125rem;letter-spacing:.08em;text-transform:uppercase;color:#E3B965;font-weight:600;margin:0 0 14px}
h1{font:700 clamp(2rem,6vw,3.4rem)/1.05 var(--sans);letter-spacing:-.03em;margin:0 0 16px;max-width:16ch}
.lede{margin:0;color:#C9D8EA;max-width:60ch;font-size:1.125rem}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:34px}
.stat{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);backdrop-filter:blur(6px);border-radius:var(--r);padding:16px 18px}
.stat b{display:block;font:700 clamp(1.7rem,4vw,2.3rem)/1.05 var(--sans);letter-spacing:-.02em;color:#fff}.stat span{font-size:.9375rem;color:#C9D8EA}
.callout{margin:-28px auto 0;position:relative;z-index:2}
.note{background:var(--note);border-left:4px solid var(--gold);padding:12px 18px;font-size:.9375rem;border-radius:0 var(--r) var(--r) 0;box-shadow:var(--shadow)}
h2{font:700 clamp(1.4rem,3vw,1.8rem)/1.2 var(--sans);letter-spacing:-.02em;margin:56px 0 8px}.sub{color:var(--muted);margin:0 0 18px;max-width:68ch}
.card{background:var(--card);border:1px solid var(--grid);border-radius:var(--r);box-shadow:var(--shadow)}
.mapgrid{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:18px;align-items:start}
.mapcard{padding:14px}
.seg{display:inline-flex;background:var(--bg);border:1px solid var(--grid);border-radius:999px;padding:4px;margin-bottom:10px}
.seg button{border:0;background:transparent;color:var(--muted);font:600 .9375rem var(--sans);padding:9px 16px;border-radius:999px;cursor:pointer;min-height:40px;transition:background .25s,color .25s}
.seg button[aria-pressed=true]{background:var(--link);color:var(--card)}
svg#map{width:100%;height:auto;display:block}
svg#map path{fill:var(--none);stroke:var(--stroke);stroke-width:.8;cursor:pointer;transition:fill .5s ease,opacity .2s,stroke .2s}
svg#map path:hover,svg#map path.sel{stroke:var(--gold);stroke-width:2.4}
svg#map.dim path:not(.sel):not(:hover){opacity:.55}
.mapwrap{position:relative;overflow:hidden;border-radius:calc(var(--r) - 2px);cursor:grab;touch-action:pan-y;user-select:none;-webkit-user-select:none}.mapwrap.drag{cursor:grabbing}
svg#map path{vector-effect:non-scaling-stroke}
.zoomctl{position:absolute;top:10px;right:10px;display:flex;flex-direction:column;gap:6px;z-index:2}
.zoomctl button{width:38px;height:38px;padding:0;border-radius:999px;border:1px solid var(--link);background:var(--card);color:var(--link);display:grid;place-items:center;cursor:pointer;transition:background .2s,color .2s}
.zoomctl button:hover{background:var(--link);color:var(--card)}.zoomctl button:focus-visible{outline:3px solid var(--gold);outline-offset:2px}.zoomctl svg{width:16px;height:16px}
.zoomtag{position:absolute;left:10px;bottom:10px;padding:4px 10px;border-radius:999px;background:var(--card);border:1px solid var(--grid);font-size:.75rem;font-weight:600;color:var(--muted);font-variant-numeric:tabular-nums;pointer-events:none}
.mapnote{font-size:.8125rem;color:var(--muted);margin:8px 0 0}
#labels text{font:600 11px var(--sans);fill:var(--ink);paint-order:stroke;stroke:var(--card);stroke-width:3px;stroke-linejoin:round;text-anchor:middle;dominant-baseline:central;pointer-events:none}
.strip{margin:16px 0 0}.strip small{display:block;color:var(--muted);font-size:.8125rem;margin:0 0 4px}.strip svg{width:100%;height:auto;display:block}
.strip .base{stroke:var(--grid);stroke-width:2}.strip .tk{stroke:var(--soft,#6C819A);stroke-width:1;opacity:.45}.strip .city{stroke:var(--ink);stroke-width:1.5;stroke-dasharray:3 2}.strip .me{fill:var(--gold);stroke:var(--card);stroke-width:2}
.strip text{font:600 9px var(--sans);fill:var(--muted)}
.legend{display:flex;align-items:center;gap:10px;font-size:.8125rem;color:var(--muted);margin-top:6px}.legend i{flex:1;height:8px;border-radius:4px;max-width:260px}
.panel{padding:20px;position:sticky;top:16px}.panel h3{font:700 1.25rem/1.2 var(--sans);margin:0 0 4px}.panel .hint{color:var(--muted);font-size:.9375rem;margin:0}
.kv{display:grid;grid-template-columns:1fr auto;gap:6px 12px;margin:14px 0 0;font-size:.9375rem}.kv dt{color:var(--muted)}.kv dd{margin:0;font-weight:650;text-align:right}
.search{width:100%;min-height:46px;padding:0 14px;margin:0 0 14px;font:inherit;color:var(--ink);background:var(--bg);border:1px solid var(--grid);border-radius:10px}
.tip{position:fixed;z-index:20;pointer-events:none;background:var(--ink);color:var(--bg);padding:6px 10px;border-radius:8px;font-size:.8125rem;opacity:0;transform:translateY(4px);transition:opacity .15s,transform .15s;white-space:nowrap}
.tip.on{opacity:1;transform:none}
.bars{display:grid;gap:10px;padding:18px}.bars h3{font:700 1rem/1.3 var(--sans);margin:0 0 6px}
.bar{display:grid;grid-template-columns:minmax(0,10.5rem) 1fr auto;gap:10px;align-items:center;font-size:.9375rem}
.bar .t{height:14px;background:var(--bg);border-radius:7px;overflow:hidden}.bar .t i{display:block;height:100%;width:0;border-radius:7px;background:var(--link);transition:width 1.1s cubic-bezier(.2,.7,.2,1)}
.bar.hi .t i{background:var(--gold)}.bar .v{font-weight:650;min-width:3.4rem;text-align:right}.bar .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cols{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
table{width:100%;border-collapse:collapse;font-size:.9375rem}th,td{text-align:right;padding:10px 12px;border-bottom:1px solid var(--grid)}th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600;background:var(--card);position:sticky;top:0}th button{all:unset;cursor:pointer;font-weight:600}th button:hover{color:var(--ink)}
tbody tr{transition:background .15s}tbody tr:hover{background:var(--bg)}
.scroll{max-height:460px;overflow:auto;border-radius:var(--r)}
details.card{padding:0}details summary{cursor:pointer;padding:16px 20px;font-weight:650;list-style:none}details summary::after{content:"+";float:right;transition:transform .25s}details[open] summary::after{transform:rotate(45deg)}
.limits{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.limits div{padding:18px;border-top:3px solid var(--gold)}.limits b{display:block;margin-bottom:4px}.limits p{margin:0;font-size:.9375rem;color:var(--muted)}
ul{padding-left:1.2em}li{margin-bottom:8px}code{font-size:.9em;background:var(--grid);padding:1px 6px;border-radius:4px}
footer{color:var(--muted);font-size:.875rem;padding:30px 0 48px}
.rv{opacity:0;transform:translateY(18px);transition:opacity .7s ease,transform .7s ease}.rv.in{opacity:1;transform:none}
@media(max-width:860px){.mapgrid{grid-template-columns:1fr}.panel{position:static}.cols,.limits{grid-template-columns:1fr}.stats{grid-template-columns:1fr}.bar{grid-template-columns:minmax(0,8rem) 1fr auto}}
@media(prefers-reduced-motion:reduce){*,*:before{animation:none!important;transition:none!important}.rv{opacity:1;transform:none}html{scroll-behavior:auto}.bar .t i{transition:none}}
</style></head><body>
<header><div class="wrap">
<p class="eyebrow">Side project · separate from the national profit analysis</p>
<h1>Toronto restaurants, neighbourhood by neighbourhood</h1>
<p class="lede">Where the city's licensed restaurants and bars are, and where licences have been ending. Counts from City of Toronto open data. They say nothing about profit.</p>
<div class="stats">
<div class="stat"><b data-count="%%PLACED%%">%%PLACED_FMT%%</b><span>active restaurant and bar licences placed on the map (of %%ACTIVE_ALL%% in Toronto)</span></div>
<div class="stat"><b data-count="%%DENS%%" data-dec="1">%%DENS%%</b><span>per 1,000 residents across the city (2021 census population)</span></div>
<div class="stat"><b data-count="%%EXITP%%" data-dec="1" data-suffix="%">%%EXITP%%%</b><span>of licences live on 1 Jan 2023 ended by the end of 2025, after removing re-issued addresses (%%RAWP%% before)</span></div>
</div></div></header>

<main class="wrap">
<div class="callout"><p class="note"><strong>Read this first.</strong> The national benchmark on the <a href="index.html">project page</a> comes from Statistics Canada and ISED financial data. Nobody publishes profit for a Toronto neighbourhood, so this page does not estimate it. It only counts licences: how many there are per resident, and how many ended. A licence ending is not always a failed restaurant (see the limits below).</p></div>

<h2 class="rv">Explore the map</h2>
<p class="sub rv">Switch the measure, zoom in, hover or tap a neighbourhood, or search for yours.</p>
<div class="mapgrid rv">
<div class="card mapcard">
<div class="seg" role="group" aria-label="Measure"><button id="m-d" aria-pressed="true">Restaurants per 1,000 residents</button><button id="m-e" aria-pressed="false">Licences that ended, 2023 to 2025</button></div>
<div class="mapwrap" id="mapwrap"><svg id="map" viewBox="0 0 %%W%% %%H%%" role="img" aria-label="Map of Toronto's 158 neighbourhoods coloured by the selected measure. The same numbers are in the table below.">%%PATHS%%<g id="labels"></g></svg><div class="zoomctl" role="group" aria-label="Map zoom"><button id="z-in" type="button" aria-label="Zoom in"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M8 3v10M3 8h10"/></svg></button><button id="z-out" type="button" aria-label="Zoom out"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M3 8h10"/></svg></button><button id="z-reset" type="button" aria-label="Show the whole city"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 6V2.5H6M13.5 6V2.5H10M2.5 10v3.5H6M13.5 10v3.5H10"/></svg></button></div><span class="zoomtag" id="zoomtag" aria-live="polite">Whole city</span></div>
<p class="mapnote">Drag to move the map. Zoom with the buttons, a pinch, or Ctrl or Cmd with the scroll wheel. Double-click a neighbourhood to zoom to it; names appear as you zoom in.</p>
<div class="legend"><span id="lg-lo"></span><i id="lg-bar"></i><span id="lg-hi"></span></div>
<p class="sub" id="lg-note" style="margin:8px 0 0;font-size:.875rem"></p>
</div>
<aside class="card panel" aria-live="polite">
<input class="search" id="find" list="names" placeholder="Find a neighbourhood" aria-label="Find a neighbourhood"><datalist id="names"></datalist>
<h3 id="p-name">Pick a neighbourhood</h3><p class="hint" id="p-hint">Hover over the map or search above.</p>
<dl class="kv" id="p-kv"></dl>
<div class="strip" id="p-strip"></div>
</aside>
</div>
<div class="tip" id="tip" role="tooltip"></div>

<h2 class="rv">How the neighbourhoods compare</h2>
<p class="sub rv">Most licences per resident, and the lowest and highest shares of licences that ended (only neighbourhoods with 50 or more licences). %%TOP_D_NAME%% has the most per resident, %%TOP_D_VAL%% per 1,000 against %%DENS%% for the whole city. Downtown cores rank high partly because office workers and visitors eat there but do not live there. Among the %%NRANK%% rankable neighbourhoods the share that ended runs from %%LO_VAL%% (%%LO_NAME%%) to %%HI_VAL%% (%%HI_NAME%%), but with 50 to 250 licences each a few cases move these numbers, so treat gaps of a few points as noise.</p>
<div class="cols rv">
<div class="card bars" id="b-d"><h3>Most licences per 1,000 residents</h3></div>
<div class="card bars" id="b-lo"><h3>Lowest share ended, 2023 to 2025</h3></div>
<div class="card bars" id="b-hi"><h3>Highest share ended, 2023 to 2025</h3></div>
</div>

<h2 class="rv">Business improvement areas</h2>
<p class="sub rv">The ten named shopping streets (BIAs) with the most active licences. BIAs with fewer than 50 licences are left out. BIA boundaries overlap neighbourhoods, so a licence counts in both.</p>
<div class="card rv"><table><thead><tr><th>BIA</th><th>Active licences</th><th>Live on 1 Jan 2023</th><th>Ended 2023 to 2025</th></tr></thead><tbody>%%BIA%%</tbody></table></div>

<h2 class="rv">All 158 neighbourhoods</h2>
<details class="card rv"><summary>Show the full table (sort by any column)</summary>
<div class="scroll"><table id="tbl"><thead><tr><th><button data-k="n">Neighbourhood</button></th><th><button data-k="p">Residents</button></th><th><button data-k="a">Licences</button></th><th><button data-k="d">Per 1,000</button></th><th><button data-k="r">Ended 2023 to 2025</button></th></tr></thead><tbody></tbody></table></div></details>

%%CONSTRUCTION%%
<h2 class="rv">Limits</h2>
<div class="limits rv">
<div class="card"><b>Not profit.</b><p>There is no income, rent or cost data here. The 2.5% net margin on the main page is a national average and is not split by area.</p></div>
<div class="card"><b>A cancelled licence is not always a closure.</b><p>I only count a cancellation as a closure when no other licence starts at the same address and unit within 90 days. That still misses some owner changes and any restaurant replaced within 90 days. Use the share to compare areas, not as a true closure rate (the raw cancellation share was %%RAWP%%).</p></div>
<div class="card"><b>Placing licences is approximate.</b><p>The licence file has no coordinates. %%ADDR%% of %%SCOPE%% were placed by matching the street address to a DineSafe health-inspection premises, %%POSTAL%% at the average position of premises sharing their postal code (they can land in a neighbouring area), and %%NOTPLACED%% could not be placed and are left out.</p></div>
<div class="card"><b>Only one licence type.</b><p>I count "Eating or drinking establishment" licences. Take-out and retail food licences, food trucks and sidewalk cafes are separate categories and are not counted. Bars are included with restaurants.</p></div>
<div class="card"><b>Old population data.</b><p>Residents come from the 2021 census, and some neighbourhoods have grown a lot since.</p></div>
<div class="card"><b>Most neighbourhoods are too small to rank.</b><p>%%NLOW%% of 158 have fewer than 50 licences, so their closure shares are not shown on the map or in the rankings.</p></div>
</div>

<h2 class="rv">How I built it</h2>
<ul class="rv">
<li>Python (pandas, shapely, matplotlib) reads City of Toronto datasets and writes small CSVs to the <code>data</code> folder (<code>toronto_neighbourhoods.csv</code>, <code>toronto_bia.csv</code>, <code>toronto_match_summary.csv</code> and <code>toronto_construction.csv</code>). The raw files are about 450 MB and are downloaded by a script rather than stored.</li>
<li>Licences come from the Municipal Licensing and Standards business licences file (snapshot taken 21 October 2026). Coordinates come from DineSafe. Boundaries are the City's 158 neighbourhoods and its BIAs. Population is the 2021 Neighbourhood Profiles.</li>
<li>This page is plain HTML, CSS and a little JavaScript, with the map drawn as inline SVG. The code is <code>analysis/toronto_download.py</code>, <code>build_toronto.py</code>, <code>build_toronto_charts.py</code> and <code>build_toronto_page.py</code>, and <code>checks.py</code> checks that the numbers on this page match the CSVs.</li>
</ul>
<p><a href="index.html">Back to the national benchmark</a> · <a href="dashboard.html">Dashboard</a> · <a href="calculator.html">Compare your restaurant</a> · <a href="https://github.com/BenShadabi/canadian-restaurant-profitability-benchmark">Code and data</a></p>
</main>
<footer><div class="wrap">Student project by Ben Shadabi, Business Analytics (BBA), George Brown College. Contains information licensed under the <a href="https://open.toronto.ca/open-data-licence/">Open Government Licence – Toronto</a> (City of Toronto Open Data). This project is not endorsed by the City of Toronto. Font: Geist (SIL Open Font License).</div></footer>

<script src="motion.js" defer></script>
<script>
const D=%%DATA%%, RD=%%RD%%, RLO=%%RLO%%, RHI=%%RHI%%;
const byC=Object.fromEntries(D.map(d=>[d.c,d])), $=id=>document.getElementById(id);
const reduce=matchMedia("(prefers-reduced-motion: reduce)").matches;
const fmt=v=>v.toLocaleString("en-CA"), pct=v=>(v*100).toFixed(1)+"%";
let mode="d", sel=null;
const maxD=Math.max(...D.map(d=>d.d)), rates=D.filter(d=>!d.low&&d.r!=null).map(d=>d.r), minR=Math.min(...rates), maxR=Math.max(...rates);
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const rgb=h=>{h=h.replace("#","");return[0,2,4].map(i=>parseInt(h.substr(i,2),16))};
const mix=(a,b,t)=>"rgb("+rgb(a).map((x,i)=>Math.round(x+(rgb(b)[i]-x)*t)).join(",")+")";
function fill(d){ if(mode==="d")return mix(css("--d0"),css("--d1"),Math.sqrt(d.d/maxD));
  if(d.low||d.r==null)return css("--none"); return mix(css("--e0"),css("--e1"),(d.r-minR)/(maxR-minR||1)); }
function paint(){
  document.querySelectorAll("#map path").forEach(p=>p.style.fill=fill(byC[p.dataset.c]));
  const a=mode==="d"?[css("--d0"),css("--d1")]:[css("--e0"),css("--e1")];
  $("lg-bar").style.background="linear-gradient(90deg,"+a[0]+","+a[1]+")";
  $("lg-lo").textContent=mode==="d"?"0":pct(minR); $("lg-hi").textContent=mode==="d"?maxD.toFixed(1)+" per 1,000":pct(maxR);
  $("lg-note").textContent=mode==="d"?"Downtown cores look high because many customers do not live there.":"Grey = fewer than 50 licences, too few to compare. Licence data, not profit.";
  if(sel)show(byC[sel]);
}
// ---- zoom, pan, labels and richer details ----
const mapEl=$("map"), wrap=$("mapwrap"), VB=mapEl.getAttribute("viewBox").split(" ").map(Number), MW=VB[2], MH=VB[3];
let view={x:0,y:0,w:MW,h:MH}, tween=0, moved=false;
const clampV=v=>{v.w=Math.min(MW,Math.max(MW/14,v.w));v.h=v.w*MH/MW;v.x=Math.min(MW-v.w,Math.max(0,v.x));v.y=Math.min(MH-v.h,Math.max(0,v.y));return v};
function apply(v){view=v;mapEl.setAttribute("viewBox",v.x.toFixed(1)+" "+v.y.toFixed(1)+" "+v.w.toFixed(1)+" "+v.h.toFixed(1));
  const z=MW/v.w;wrap.style.touchAction=z>1.02?"none":"pan-y";$("zoomtag").textContent=z<1.05?"Whole city":z.toFixed(1)+"x";labels()}
function goTo(t,ms){t=clampV(t);cancelAnimationFrame(tween);if(reduce||!ms){apply(t);return}
  const a={...view},t0=performance.now();(function f(now){const k=Math.min(1,(now-t0)/ms),e=1-Math.pow(1-k,3);
    apply({x:a.x+(t.x-a.x)*e,y:a.y+(t.y-a.y)*e,w:a.w+(t.w-a.w)*e,h:a.h+(t.h-a.h)*e});if(k<1)tween=requestAnimationFrame(f)})(t0)}
function pt(cx,cy){const r=mapEl.getBoundingClientRect();return[view.x+(cx-r.left)/r.width*view.w,view.y+(cy-r.top)/r.height*view.h]}
function zoomBy(f,cx,cy){const r=mapEl.getBoundingClientRect(),[px,py]=cx==null?[view.x+view.w/2,view.y+view.h/2]:pt(cx,cy),w=view.w/f,h=w*MH/MW;
  const fx=cx==null?.5:(cx-r.left)/r.width,fy=cy==null?.5:(cy-r.top)/r.height;goTo({x:px-fx*w,y:py-fy*h,w,h},220)}
function zoomTo(c){const p=document.querySelector('#map path[data-c="'+c+'"]');if(!p)return;const b=p.getBBox();
  const w=Math.max(b.width*2.4,b.height*2.4*MW/MH,MW/9),h=w*MH/MW;goTo({x:b.x+b.width/2-w/2,y:b.y+b.height/2-h/2,w,h},520)}
$("z-in").onclick=()=>zoomBy(1.6);$("z-out").onclick=()=>zoomBy(1/1.6);$("z-reset").onclick=()=>goTo({x:0,y:0,w:MW,h:MH},420);
wrap.addEventListener("wheel",ev=>{if(!(ev.ctrlKey||ev.metaKey))return;ev.preventDefault();zoomBy(Math.exp(-ev.deltaY*.01),ev.clientX,ev.clientY)},{passive:false});
const ptrs=new Map();let last=0,startPt=null;
wrap.addEventListener("pointerdown",ev=>{if(ev.target.closest(".zoomctl"))return;ptrs.set(ev.pointerId,[ev.clientX,ev.clientY]);moved=false;startPt=[ev.clientX,ev.clientY];last=ptrs.size===2?Math.hypot(...[...ptrs.values()].reduce((a,b)=>[a[0]-b[0],a[1]-b[1]])):0});
addEventListener("pointermove",ev=>{if(!ptrs.has(ev.pointerId))return;const o=ptrs.get(ev.pointerId),dx=ev.clientX-o[0],dy=ev.clientY-o[1];ptrs.set(ev.pointerId,[ev.clientX,ev.clientY]);
  if(startPt&&Math.hypot(ev.clientX-startPt[0],ev.clientY-startPt[1])>5){moved=true;wrap.classList.add("drag")}
  if(!moved)return;cancelAnimationFrame(tween);
  if(ptrs.size===2){const [a,b]=[...ptrs.values()],d=Math.hypot(a[0]-b[0],a[1]-b[1]);if(last)zoomBy(d/last,(a[0]+b[0])/2,(a[1]+b[1])/2);last=d;return}
  const r=mapEl.getBoundingClientRect();apply(clampV({x:view.x-dx/r.width*view.w,y:view.y-dy/r.height*view.h,w:view.w,h:view.h}))});
["pointerup","pointercancel"].forEach(n=>addEventListener(n,ev=>{ptrs.delete(ev.pointerId);wrap.classList.remove("drag");last=0;setTimeout(()=>moved=false,0)}));
// neighbourhood names appear once there is room for them
const NS="http://www.w3.org/2000/svg", lab=$("labels"), LB=[];
document.querySelectorAll("#map path").forEach(p=>{const b=p.getBBox(),t=document.createElementNS(NS,"text");t.textContent=byC[p.dataset.c].n;t.setAttribute("x",b.x+b.width/2);t.setAttribute("y",b.y+b.height/2);t.style.display="none";lab.appendChild(t);LB.push([t,b,byC[p.dataset.c].n.length])});
function labels(){const r=mapEl.getBoundingClientRect(),k=r.width/view.w,z=MW/view.w,fs=11/k;
  LB.forEach(([t,b,n])=>{const on=z>=2&&b.width*k>n*5.4&&b.x+b.width>view.x&&b.x<view.x+view.w&&b.y+b.height>view.y&&b.y<view.y+view.h;t.style.display=on?"":"none";if(on){t.style.fontSize=fs+"px";t.style.strokeWidth=(3/k)+"px"}})}
addEventListener("resize",labels);
// details: rank, city average and where it sits among all neighbourhoods
const cityD=D.reduce((s,d)=>s+d.a,0)/D.reduce((s,d)=>s+d.p,0)*1000, cityX=D.reduce((s,d)=>s+d.x,0)/D.reduce((s,d)=>s+d.l,0);
const byD=[...D].sort((a,b)=>b.d-a.d), byR=D.filter(d=>!d.low&&d.r!=null).sort((a,b)=>b.r-a.r);
function strip(d){const W=300,isD=mode==="d",val=isD?d.d:d.r;if(val==null||(!isD&&d.low))return"";
  const sc=isD?v=>Math.sqrt(v/maxD):v=>(v-minR)/(maxR-minR||1),X=v=>8+sc(v)*(W-16),vals=isD?D.map(x=>x.d):rates,city=isD?cityD:cityX;
  return '<small>'+(isD?"Where it sits among all 158 neighbourhoods":"Where it sits among neighbourhoods with 50+ licences")+'</small><svg viewBox="0 0 300 40" role="img" aria-label="Position of this neighbourhood on the scale"><line class="base" x1="8" x2="292" y1="22" y2="22"/>'
   +vals.map(v=>'<line class="tk" x1="'+X(v).toFixed(1)+'" x2="'+X(v).toFixed(1)+'" y1="16" y2="28"/>').join("")
   +'<line class="city" x1="'+X(city).toFixed(1)+'" x2="'+X(city).toFixed(1)+'" y1="9" y2="35"/><text x="'+X(city).toFixed(1)+'" y="8" text-anchor="middle">Toronto</text>'
   +'<circle class="me" cx="'+X(val).toFixed(1)+'" cy="22" r="6"/></svg>'}
function show(d){
  const rd=byD.indexOf(d)+1, rr=byR.indexOf(d)+1, okR=!d.low&&d.r!=null;
  $("p-name").textContent=d.n; $("p-hint").textContent="Neighbourhood "+d.c;
  $("p-kv").innerHTML=[["Residents (2021)",fmt(d.p)],["Active licences",fmt(d.a)],["Per 1,000 residents",d.d.toFixed(1)],["City average, per 1,000",cityD.toFixed(1)],["Rank for density","#"+rd+" of "+D.length],
   ["Live on 1 Jan 2023",fmt(d.l)],["Ended 2023 to 2025",fmt(d.x)],["Share ended",okR?pct(d.r):"too few to compare"],["City average, share ended",pct(cityX)],
   ["Rank for share ended",okR?"#"+rr+" of "+byR.length+" (1 = most ended)":"not ranked"]].map(r=>"<dt>"+r[0]+"</dt><dd>"+r[1]+"</dd>").join("");
  $("p-strip").innerHTML=strip(d);
}
function select(c){ sel=c; document.querySelectorAll("#map path").forEach(p=>p.classList.toggle("sel",p.dataset.c===c));
  $("map").classList.toggle("dim",!!c); if(c)show(byC[c]); }
const tip=$("tip");
document.querySelectorAll("#map path").forEach(p=>{
  p.addEventListener("pointermove",ev=>{const d=byC[p.dataset.c];tip.textContent=d.n+" · "+(mode==="d"?d.d.toFixed(1)+" per 1,000":(d.low||d.r==null?"too few to compare":pct(d.r)+" ended"));
    tip.style.left=Math.min(ev.clientX+14,innerWidth-tip.offsetWidth-8)+"px";tip.style.top=(ev.clientY-34)+"px";tip.classList.add("on");if(!sel)show(d);});
  p.addEventListener("pointerleave",()=>{tip.classList.remove("on");if(!sel)resetPanel();});
  p.addEventListener("click",()=>{if(moved)return;select(sel===p.dataset.c?null:p.dataset.c)});
  p.addEventListener("dblclick",()=>{select(p.dataset.c);zoomTo(p.dataset.c)});
});
function resetPanel(){ $("p-name").textContent="Pick a neighbourhood"; $("p-hint").textContent="Hover over the map or search above."; $("p-kv").innerHTML=""; $("p-strip").innerHTML=""; }
$("m-d").onclick=()=>{mode="d";$("m-d").setAttribute("aria-pressed",true);$("m-e").setAttribute("aria-pressed",false);paint()};
$("m-e").onclick=()=>{mode="e";$("m-e").setAttribute("aria-pressed",true);$("m-d").setAttribute("aria-pressed",false);paint()};
$("names").innerHTML=D.map(d=>'<option value="'+d.n.replace(/"/g,"&quot;")+'">').join("");
$("find").addEventListener("change",ev=>{const d=D.find(x=>x.n.toLowerCase()===ev.target.value.trim().toLowerCase());if(d){select(d.c);zoomTo(d.c);wrap.scrollIntoView({block:"nearest",behavior:reduce?"auto":"smooth"})}});
matchMedia("(prefers-color-scheme: dark)").addEventListener("change",paint);

function bars(id,rows,fmtv,hi,max){ const el=$(id); rows.forEach(r=>{const b=document.createElement("div");b.className="bar"+(hi?" hi":"");
  b.innerHTML='<span class="nm" title="'+r[0]+'">'+r[0]+'</span><span class="t"><i data-w="'+(r[1]/max*100)+'"></i></span><span class="v">'+fmtv(r)+'</span>';el.appendChild(b);}); }
bars("b-d",RD,r=>r[1].toFixed(1),false,Math.max(...RD.map(r=>r[1])));
bars("b-lo",RLO,r=>pct(r[1]),false,maxR); bars("b-hi",RHI,r=>pct(r[1]),true,maxR);

let rows=D.map(d=>d), key="d", asc=false;
function table(){ rows.sort((a,b)=>{const x=a[key],y=b[key];const nx=x==null||(key==="r"&&a.low),ny=y==null||(key==="r"&&b.low);if(nx!==ny)return nx?1:-1;
    return (typeof x==="string"?x.localeCompare(y):(x-y))*(asc?1:-1)});
  document.querySelector("#tbl tbody").innerHTML=rows.map(d=>"<tr><td>"+d.n+"</td><td>"+fmt(d.p)+"</td><td>"+fmt(d.a)+"</td><td>"+d.d.toFixed(1)+"</td><td>"+(d.low||d.r==null?"n/a":pct(d.r))+"</td></tr>").join(""); }
document.querySelectorAll("#tbl th button").forEach(b=>b.onclick=()=>{asc=key===b.dataset.k?!asc:b.dataset.k==="n";key=b.dataset.k;table()});

function countUp(el){ const end=parseFloat(el.dataset.count),dec=+(el.dataset.dec||0),suf=el.dataset.suffix||""; if(reduce){return}
  const t0=performance.now(),dur=1400; (function f(t){const k=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-k,3);
    el.textContent=(dec?(end*e).toFixed(dec):fmt(Math.round(end*e)))+suf; if(k<1)requestAnimationFrame(f)})(t0); }
const io=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){en.target.classList.add("in");en.target.querySelectorAll(".bar .t i").forEach(i=>i.style.width=i.dataset.w+"%");io.unobserve(en.target)}}),{threshold:.15});
document.querySelectorAll(".rv").forEach(el=>io.observe(el));
if(reduce)document.querySelectorAll(".bar .t i").forEach(i=>i.style.width=i.dataset.w+"%");
document.querySelectorAll("[data-count]").forEach(countUp);
paint(); table();
</script>
</body></html>
"""
repl = {"PLACED": str(placed_active), "PLACED_FMT": n(placed_active), "ACTIVE_ALL": n(ms["active_total_all_toronto"]), "DENS": f"{city_density:.1f}",
        "EXITP": f"{city_exit * 100:.1f}", "RAWP": f"{raw_exit:.0%}", "W": str(W), "H": str(H), "PATHS": paths, "BIA": bia_html,
        "TOP_D_NAME": e(top_d.neighbourhood), "TOP_D_VAL": f"{top_d.per_1000_residents:.1f}", "NRANK": str(len(rank)),
        "LO_VAL": f"{lo_x.exit_rate_3yr:.1%}", "LO_NAME": e(lo_x.neighbourhood), "HI_VAL": f"{hi_x.exit_rate_3yr:.1%}", "HI_NAME": e(hi_x.neighbourhood),
        "ADDR": n(ms["address_match"]), "SCOPE": n(ms["licences_in_scope"]), "POSTAL": n(ms["postal_code_centre"]), "NOTPLACED": n(ms["not_placed"]), "NLOW": str(int(nb.low_sample.sum())),
        "CONSTRUCTION": construction, "DATA": json.dumps(data, separators=(",", ":")), "RD": json.dumps(rank_density), "RLO": json.dumps(rank_exit_lo), "RHI": json.dumps(rank_exit_hi)}
page = TEMPLATE
for key, val in repl.items(): page = page.replace(f"%%{key}%%", val)
assert "%%" not in page and "—" not in page
open("docs/toronto.html", "w", encoding="utf-8").write(page)
print("wrote docs/toronto.html", len(page) // 1024, "KB")
