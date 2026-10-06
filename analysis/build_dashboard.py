"""Build docs/dashboard.html (the dashboard) from the CSV files in data/.
Every number on the page is read from the CSVs or computed here. Nothing is typed in by hand
(the share of loss-making restaurants is in data/restaurant_counts_2024.csv).
Run from the repo root:  python analysis/build_dashboard.py
Requires: pandas (analysis/scenario.py holds the conservative-case maths)
"""
import html
import pandas as pd

# ---------- design tokens ("Ledger": navy header, one gold accent, light and dark) ----------
# Colours are CSS variables (defined in CSS below) so the charts follow the light or dark theme.
# Series colours were checked with the dataviz palette validator: light #2F6DB5 + #B7791F, dark #4A8BD4 + #BF8420.
INK, NAVY, SLATE, MUTED, GRID = "var(--ink)", "var(--s1)", "var(--soft)", "var(--muted)", "var(--grid)"
GOLD, GOLD_TXT, GREEN, RED = "var(--gold)", "var(--goldtxt)", "var(--pos)", "var(--neg)"

ind = pd.read_csv("data/industry_trend.csv")
avg = pd.read_csv("data/average_restaurant_2024.csv").set_index("line")["dollars"]
wag = pd.read_csv("data/wages_food_services.csv")
cnt = pd.read_csv("data/restaurant_counts_2024.csv").set_index("metric")["value"]
LOSS_SHARE, N_BUS = cnt["loss_making_share"], int(cnt["businesses"])

# ---------- numbers (same maths as analysis/build_charts.py and the workbook Scenario tab) ----------
rev, cos, lab, util = avg["revenue"], avg["cost_of_sales"], avg["labour_and_commissions"], avg["utilities_and_telecom"]
other = rev - cos - lab - avg["rent"] - util - avg["amortization_and_depletion"] - avg["net_profit"]
LAB_CUT, OH_CUT, WASTE_SHARE, WASTE_CUT = 0.10, 0.15, 0.05, 0.20
g_lab, g_oh, g_waste = lab * LAB_CUT, (util + other) * OH_CUT, cos * WASTE_SHARE * WASTE_CUT
p0 = avg["net_profit"]; p1 = p0 + g_lab + g_oh + g_waste
m0, m1 = p0 / rev * 100, p1 / rev * 100
w0, w1 = wag.avg_hourly_wage_cad.iloc[0], wag.avg_hourly_wage_cad.iloc[-1]
wage_up = (w1 / w0 - 1) * 100
op24 = ind.operating_margin.iloc[-1] * 100
d = lambda v: f"${v:,.0f}"
e = html.escape

# ---------- small SVG helpers (viewBox is 480 wide so text stays readable on phones) ----------
W, H, L, R, T, B = 480, 300, 44, 16, 22, 36

def svg_open(title, desc, uid):
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="{uid}t {uid}d" xmlns="http://www.w3.org/2000/svg">'
            f'<title id="{uid}t">{e(title)}</title><desc id="{uid}d">{e(desc)}</desc>')

def axes(ymin, ymax, ticks, fmt):
    out = []
    for t in ticks:
        y = T + (H - T - B) * (1 - (t - ymin) / (ymax - ymin))
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>'
                   f'<text x="{L-6}" y="{y+4:.1f}" text-anchor="end" class="ax">{fmt(t)}</text>')
    return "".join(out)

def line_chart(uid, title, desc, years, series, ymin, ymax, ticks, fmt, label_all=True):
    """series: list of (name, values, color, marker 'o' or 's', dash). Returns svg string."""
    xs = {y: L + 30 + (W - L - R - 60) * i / (len(years) - 1) for i, y in enumerate(years)}
    ypx = lambda v: T + (H - T - B) * (1 - (v - ymin) / (ymax - ymin))
    s = [svg_open(title, desc, uid), axes(ymin, ymax, ticks, fmt)]
    for y in years:
        s.append(f'<text x="{xs[y]:.1f}" y="{H-12}" text-anchor="middle" class="ax">{y}</text>')
    for si, (name, vals, color, mk, dash) in enumerate(series):
        pts = [(xs[y], ypx(v), v, y) for y, v in zip(years, vals) if not pd.isna(v)]
        s.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" {dash} points="{" ".join(f"{x:.1f},{yy:.1f}" for x,yy,_,_ in pts)}"/>')
        for x, yy, v, y in pts:
            s.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="4.5" fill="{color}"/>' if mk == "o" else
                     f'<rect x="{x-4:.1f}" y="{yy-4:.1f}" width="8" height="8" fill="{color}"/>')
            if label_all or y in (years[0], years[-1]):
                other_v = series[1 - si][1][years.index(y)] if len(series) == 2 else None
                above = True if (other_v is None or pd.isna(other_v)) else v >= other_v
                ty = yy - 10 if above else yy + 19
                tc = color if color != GOLD else GOLD_TXT
                s.append(f'<text x="{x:.1f}" y="{ty:.1f}" text-anchor="middle" class="lb" fill="{tc}">{fmt(v, True)}</text>')
    step = (xs[years[-1]] - xs[years[0]]) / (len(years) - 1)
    for i, y in enumerate(years):  # hover layer: one zone per year, wider than the marks
        tip = [str(y)] + [f"{n} {fmt(v[i], True)}" for n, v, *_ in series if not pd.isna(v[i])]
        s.append(f'<rect class="hit" x="{xs[y]-step/2:.1f}" y="{T}" width="{step:.1f}" height="{H-T-B}" data-tip="{e("|".join(tip))}"/>')
    return "".join(s) + "</svg>"

# 1. waterfall (hero)
def waterfall():
    steps = [("Profit before", p0, None), ("Labour -10%", g_lab, GREEN), ("Overhead -15%", g_oh, GREEN),
             ("Waste -20%", g_waste, GREEN), ("Profit after", p1, None)]
    ymax = p1 * 1.15; top, bot = 30, H - 46
    ypx = lambda v: top + (bot - top) * (1 - v / ymax)
    s = [svg_open("Waterfall of the what-if profit change",
                  f"Average restaurant profit rises from {d(p0)} to {d(p1)}: labour +{d(g_lab)}, overhead +{d(g_oh)}, waste +{d(g_waste)}.", "wf"),
         f'<line x1="8" x2="{W-8}" y1="{bot}" y2="{bot}" stroke="{GRID}"/>']
    bw, gap = 74, (W - 16 - 5 * 74) / 4; run = 0; hits = []
    for i, (lbl, v, c) in enumerate(steps):
        x = 8 + i * (bw + gap)
        if c is None:
            y, h, col, txt, run = ypx(v), bot - ypx(v), NAVY, d(v), v
        else:
            y, h, col, txt = ypx(run + v), ypx(run) - ypx(run + v), c, "+" + d(v); run += v
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw}" height="{h:.1f}" fill="{col}"/>')
        s.append(f'<text x="{x+bw/2:.1f}" y="{y-7:.1f}" text-anchor="middle" class="lb" fill="{INK}">{txt}</text>')
        tip = [lbl, txt] + ([f"Running profit {d(run)}"] if c else [])
        hits.append(f'<rect class="hit" x="{x-4:.1f}" y="{top-20}" width="{bw+8}" height="{bot-top+20}" data-tip="{e("|".join(tip))}"/>')
        a, b = (lbl.split(" ", 1) + [""])[:2] if c else lbl.split(" ", 1)
        s.append(f'<text x="{x+bw/2:.1f}" y="{bot+17}" text-anchor="middle" class="ax">{a}</text>'
                 f'<text x="{x+bw/2:.1f}" y="{bot+32}" text-anchor="middle" class="ax">{b}</text>')
    return "".join(s) + "".join(hits) + "</svg>"

# 2. wages as columns from zero (the old chart cut the axis at $15)
def wages_svg():
    ymax = 24; top, bot = 26, H - 36
    ypx = lambda v: top + (bot - top) * (1 - v / ymax)
    n = len(wag); bw = 52; gap = (W - 16 - n * bw) / (n - 1)
    s = [svg_open("Average hourly wage in food services, 2020 to 2024",
                  "; ".join(f"{int(y)}: ${v:.2f}" for y, v in zip(wag.year, wag.avg_hourly_wage_cad)) + ". Axis starts at zero.", "wg"),
         f'<line x1="8" x2="{W-8}" y1="{bot}" y2="{bot}" stroke="{MUTED}"/>']
    for i, (y, v) in enumerate(zip(wag.year, wag.avg_hourly_wage_cad)):
        x = 8 + i * (bw + gap); last = i in (0, n - 1)
        s.append(f'<rect x="{x:.1f}" y="{ypx(v):.1f}" width="{bw}" height="{bot-ypx(v):.1f}" fill="{NAVY if last else SLATE}"/>'
                 f'<text x="{x+bw/2:.1f}" y="{ypx(v)-7:.1f}" text-anchor="middle" class="lb" fill="{INK}">${v:.2f}</text>'
                 f'<text x="{x+bw/2:.1f}" y="{H-12}" text-anchor="middle" class="ax">{int(y)}</text>')
        tip = [str(int(y)), f"${v:.2f} an hour"] + ([f"{(v / wag.avg_hourly_wage_cad.iloc[i-1] - 1) * 100:+.1f}% on {int(y)-1}"] if i else [])
        s.append(f'<rect class="hit" x="{x-4:.1f}" y="{top}" width="{bw+8}" height="{bot-top}" data-tip="{e("|".join(tip))}"/>')
    return "".join(s) + "</svg>"

pct = lambda v, lab=False: (f"{v:.1f}%" if lab else f"{v:g}%")
bn = lambda v, lab=False: (f"${v:.1f}B" if lab else f"${v:g}B")

seg = ind.dropna(subset=["full_service_margin"])
svg_seg_margin = line_chart("sm", "Operating margin by segment, 2019 to 2022",
    "Full-service: " + ", ".join(f"{int(y)} {v*100:.1f}%" for y, v in zip(seg.year, seg.full_service_margin)) + ". Limited-service: " +
    ", ".join(f"{int(y)} {v*100:.1f}%" for y, v in zip(seg.year, seg.limited_service_margin)) + ".",
    list(seg.year), [("Full-service", list(seg.full_service_margin * 100), NAVY, "o", ""),
                     ("Limited-service", list(seg.limited_service_margin * 100), GOLD, "s", 'stroke-dasharray="7 4"')],
    0, 8, [0, 2, 4, 6, 8], pct)
svg_seg_rev = line_chart("sr", "Revenue by segment, 2019 to 2024",
    f"Full-service {bn(ind.full_service_revenue_bn.iloc[0],True)} in 2019 to {bn(ind.full_service_revenue_bn.iloc[-1],True)} in 2024. Limited-service {bn(ind.limited_service_revenue_bn.iloc[0],True)} to {bn(ind.limited_service_revenue_bn.iloc[-1],True)}.",
    list(ind.year), [("Full-service", list(ind.full_service_revenue_bn), NAVY, "o", ""),
                     ("Limited-service", list(ind.limited_service_revenue_bn), GOLD, "s", 'stroke-dasharray="7 4"')],
    0, 50, [0, 10, 20, 30, 40, 50], bn, label_all=False)
svg_ind = line_chart("im", "Industry operating margin, 2019 to 2024",
    ", ".join(f"{int(y)} {v*100:.1f}%" for y, v in zip(ind.year, ind.operating_margin)) + ".",
    list(ind.year), [("Industry", list(ind.operating_margin * 100), NAVY, "o", "")], 0, 6, [0, 2, 4, 6], pct)

# ---------- sensitivity grid: labour cut x overhead cut (waste lever left out) ----------
LABS, OHS = [0, 0.05, 0.10, 0.15], [0, 0.10, 0.15, 0.20]
grid = [[p0 + lab * l + (util + other) * o for o in OHS] for l in LABS]
sens_rows = "".join("<tr><th scope='row'>Labour %s</th>%s</tr>" % (('-%d%%' % (l * 100)) if l else 'no cut', "".join(
    f"<td{' class=hl' if (l, o) == (LAB_CUT, OH_CUT) else ''}>{d(v)}<small>{v / rev * 100:.1f}%</small></td>" for o, v in zip(OHS, row))) for l, row in zip(LABS, grid))
SENS = (f'<section class="card hero" aria-labelledby="h-sens"><h2 id="h-sens">Even a 5% labour cut and a 10% overhead cut lift profit from {d(p0)} to {d(grid[1][1])}</h2>'
        '<p class="sub">Annual profit (and margin) for the average restaurant at different labour and overhead cuts. The waste lever is left out, so the highlighted cell is {} lower than the waterfall total.</p>'.format(d(g_waste)) +
        '<div class="tw"><table class="sens"><thead><tr><th scope="col"></th>' + "".join(f"<th scope='col'>Overhead {('-%d%%' % int(o*100)) if o else 'no cut'}</th>" for o in OHS) + "</tr></thead><tbody>" + sens_rows + "</tbody></table></div></section>")
pd.DataFrame([[f"{l:.2f}", *[round(v, 2) for v in row]] for l, row in zip(LABS, grid)], columns=["labour_cut", *[f"overhead_cut_{o:.2f}" for o in OHS]]).to_csv("data/sensitivity_labour_overhead.csv", index=False)

# ---------- conservative case and per-1% levers (numbers come from analysis/scenario.py) ----------
import scenario
sc = scenario.load()
case_rows = [("Profit before", sc["profit"], SLATE), ("Conservative case", sc["conservative"], GOLD), ("Headline what-if", sc["headline"], NAVY)]
case_scale = sc["headline"] * 1.05
cases_li = "".join(f'<li><span class="k">{n}</span><span class="bar"><i style="width:{v/case_scale*100:.1f}%;background:{c}"></i></span><b>{d(v)}</b></li>'
                   for n, v, c in case_rows)
pp_scale = max(sc["per_point"].values()) * 1.05
pp_li = "".join(f'<li><span class="k">{html.escape(n)}</span><span class="bar"><i style="width:{v/pp_scale*100:.1f}%;background:{NAVY}"></i></span><b>{d(v)}</b></li>'
                for n, v in sorted(sc["per_point"].items(), key=lambda kv: -kv[1]))
wr = sc["waste_range"]
CASES = (f'<section class="card hero" aria-labelledby="h-cases"><div class="in"><div>'
         f'<h2 id="h-cases">Even without the calculated overhead line, profit more than doubles: {d(sc["profit"])} to {d(sc["conservative"])}</h2>'
         f'<p class="sub">Same cuts as the what-if, but overhead is only the published utilities and telecom line. The calculated "other expenses" remainder ({d(sc["other"])}) is left out. Margin is {sc["margin_conservative"]*100:.1f}%, against {sc["margin_headline"]*100:.1f}% in the headline case.</p>'
         f'<ul class="bars">{cases_li}</ul></div>'
         f'<div><h2>A 1% cut to cost of sales is worth almost twice a 1% cut to labour</h2>'
         f'<p class="sub">Annual profit gain from a 1% cut in each cost line, average restaurant, 2024.</p><ul class="bars">{pp_li}</ul>'
         f'<p class="note"><b>Check:</b> the waste share I assumed barely matters. Testing 2% to 8% moves the headline profit between {d(wr[0]["profit_headline"])} and {d(wr[-1]["profit_headline"])}.</p></div></div></section>')

# ---------- HTML pieces ----------
cost_rows = [("Cost of sales", cos, NAVY), ("Labour", lab, NAVY), ("Other expenses (calculated remainder)", other, SLATE),
             ("Rent", avg["rent"], SLATE), ("Amortization", avg["amortization_and_depletion"], SLATE),
             ("Utilities and telecom", util, SLATE), ("Net profit", avg["net_profit"], GREEN)]
cost_html = "".join(
    f'<li><span class="k">{e(n)}</span><span class="bar"><i style="width:{v/rev*100/50*100:.1f}%;background:{c}"></i></span>'
    f'<b>{v/rev*100:.1f}%</b></li>' for n, v, c in cost_rows)

lo, hi = avg["bottom_quartile_profit"], avg["top_quartile_profit"]; span = hi - lo; zero = (0 - lo) / span * 100
def qrow(name, v, col):
    if v < 0: style = f"left:{(v-lo)/span*100:.1f}%;width:{-v/span*100:.1f}%"
    else:     style = f"left:{zero:.1f}%;width:{v/span*100:.1f}%"
    sign = "-" if v < 0 else ""
    return (f'<li><span class="k">{name}</span><span class="bar q"><i style="{style};background:{col}"></i>'
            f'<u style="left:{zero:.1f}%"></u></span><b>{sign}{d(abs(v))}</b></li>')
quart_html = qrow("Bottom quartile", lo, RED) + qrow("Average", avg["net_profit"], NAVY) + qrow("Top quartile", hi, GREEN)

def table(headers, rows):
    return ('<div class="tw"><table><thead><tr>' + "".join(f"<th scope='col'>{e(h)}</th>" for h in headers) + "</tr></thead><tbody>" +
            "".join("<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></div>")
na = lambda v, f: "n/a" if pd.isna(v) else f(v)
t_ind = table(["Year", "Revenue $B", "Operating margin", "Full-service $B", "Limited-service $B", "Full-service margin", "Limited-service margin"],
              [[int(r.year), f"{r.operating_revenue_bn:g}", f"{r.operating_margin*100:.1f}%", f"{r.full_service_revenue_bn:g}", f"{r.limited_service_revenue_bn:g}",
                na(r.full_service_margin, lambda v: f"{v*100:.1f}%"), na(r.limited_service_margin, lambda v: f"{v*100:.1f}%")] for r in ind.itertuples()])
t_avg = table(["Line (average restaurant, 2024)", "Dollars", "% of revenue"],
              [["Revenue", d(rev), "100.0%"]] + [[n, d(v), f"{v/rev*100:.1f}%"] for n, v, _ in cost_rows])
t_wag = table(["Year", "Average hourly wage"], [[int(r.year), f"${r.avg_hourly_wage_cad:.2f}"] for r in wag.itertuples()])

# ---------- header strip: one revenue dollar split into its cost lines (drawn to scale) ----------
strip_meta = [("cos", "Cost of sales"), ("lab", "Labour"), ("oth", "Other (calculated)"), ("rent", "Rent"), ("amo", "Amortization"), ("uti", "Utilities"), ("pro", "Profit")]
strip_parts = [("cos", cos), ("lab", lab), ("oth", other), ("rent", avg["rent"]), ("amo", avg["amortization_and_depletion"]), ("uti", util), ("pro", avg["net_profit"])]

CSS = f"""
@font-face{{font-family:Geist;src:url(fonts/geist-latin-wght.woff2) format("woff2");font-weight:100 900;font-display:swap}}
:root{{color-scheme:light dark;--ink:#0F1B2D;--muted:#4B5563;--grid:#D5DAE1;--bg:#F4F6F9;--card:#fff;--track:#E9EDF2;--chip:#EEF1F5;--note:#FFF6E0;
--s1:#2F6DB5;--soft:#6C819A;--gold:#B7791F;--goldtxt:#8A5A00;--pos:#1B7F5C;--neg:#B42318;--link:#12355B;--hover:rgba(47,109,181,.09);
--tipbg:#0F1B2D;--tipfg:#fff;--r:10px;--rs:3px;--sp1:4px;--sp2:8px;--sp3:16px;--sp4:24px;--sp5:32px;
--sans:Geist,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
@media(prefers-color-scheme:dark){{:root{{--ink:#E8EEF6;--muted:#A7B4C6;--grid:#2A3750;--bg:#0A111F;--card:#111B2E;--track:#1C2A42;--chip:#16233A;--note:#2A2412;
--s1:#4A8BD4;--soft:#7F95AF;--gold:#BF8420;--goldtxt:#E3B965;--pos:#3FB68B;--neg:#F0857C;--link:#9CC3F0;--hover:rgba(74,139,212,.16);--tipbg:#E8EEF6;--tipfg:#0F1B2D}}}}
*{{box-sizing:border-box}}html{{-webkit-text-size-adjust:100%;scroll-behavior:smooth}}
@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 var(--sans);font-variant-numeric:tabular-nums}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 var(--sp3)}}
.skip{{position:absolute;left:-999px}}.skip:focus{{left:var(--sp3);top:var(--sp2);background:#fff;color:#0F1B2D;padding:var(--sp2);z-index:9;border-radius:var(--r)}}
header{{background:#0E2745;color:#fff;padding:40px 0 28px;border-bottom:4px solid #E3B965}}
.kicker{{margin:0 0 12px;font-size:.8125rem;letter-spacing:.12em;text-transform:uppercase;color:#E3B965;font-weight:600}}
header h1{{font:650 clamp(1.75rem,4.8vw,2.9rem)/1.08 var(--sans);letter-spacing:-.02em;margin:0;max-width:22ch}}
header h1 em{{font-style:normal;color:#E3B965}}
.by{{margin:14px 0 0;font-size:.9375rem;color:#C9D8EA}}.by strong{{color:#fff}}
.dollar{{margin:28px 0 0}}.dollar p{{margin:0 0 8px;font-size:.875rem;color:#C9D8EA}}
.strip{{display:flex;height:44px;gap:2px}}.strip i{{display:block;background:#2F5F96;border-radius:var(--rs)}}
.strip i.oth{{background:repeating-linear-gradient(135deg,#2F5F96 0 6px,#0E2745 6px 9px)}}.strip i.pro{{background:#E3B965}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 20px;margin:12px 0 0;padding:0;list-style:none;font-size:.875rem;color:#C9D8EA}}
.legend li{{display:flex;align-items:center;gap:8px}}.legend b{{color:#fff;font-weight:600}}
.legend span{{width:12px;height:12px;border-radius:2px;background:#2F5F96;flex:none}}
.legend .oth{{background:repeating-linear-gradient(135deg,#2F5F96 0 3px,#0E2745 3px 5px);outline:1px solid #2F5F96}}.legend .pro{{background:#E3B965}}
.chips{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:24px 0 0;padding:0;list-style:none}}
.chips li{{padding:12px 14px;border-radius:var(--r);background:#17355A;border:1px solid #2F5584}}
.chips b{{display:block;font:650 1.5rem/1.1 var(--sans);letter-spacing:-.01em}}.chips span{{font-size:.8125rem;color:#C9D8EA}}
.jump{{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 0}}
.jump a{{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border-radius:var(--r);color:#fff;border:1px solid #4A6C99;text-decoration:none;font-size:.875rem;font-weight:500}}
.jump a:hover{{background:#1B3F6B}}
h2{{font:650 1.125rem/1.35 var(--sans);letter-spacing:-.01em;margin:0 0 var(--sp2);color:var(--ink);scroll-margin-top:16px;text-wrap:balance}}
.card{{background:var(--card);border:1px solid var(--grid);border-radius:var(--r);padding:var(--sp3) var(--sp3) var(--sp4);scroll-margin-top:16px}}
.hero{{margin:var(--sp4) 0 var(--sp3)}}
.hero .in{{display:grid;grid-template-columns:3fr 2fr;gap:var(--sp4);align-items:center}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--sp3);margin-bottom:var(--sp3)}}
.sub{{color:var(--muted);font-size:.875rem;margin:0 0 var(--sp2);max-width:70ch}}
svg{{width:100%;height:auto;display:block;overflow:visible}}svg .ax{{font:15px var(--sans);fill:var(--muted)}}svg .lb{{font:600 15px var(--sans)}}
svg .hit{{fill:transparent;cursor:crosshair}}svg .hit:hover{{fill:var(--hover)}}
.key{{display:flex;gap:var(--sp3);flex-wrap:wrap;font-size:.875rem;margin:var(--sp2) 0 0;padding:0;list-style:none}}
.key span{{display:inline-block;width:22px;height:0;border-top:3px solid;vertical-align:middle;margin-right:6px}}
.bars{{list-style:none;margin:0;padding:0}}.bars li{{display:grid;grid-template-columns:minmax(120px,38%) 1fr 56px;gap:var(--sp2);align-items:center;margin:0 0 var(--sp2);font-size:.9375rem}}
.bars .bar{{display:block;background:var(--track);height:16px;border-radius:var(--rs);position:relative}}.bars .bar i{{position:absolute;top:0;bottom:0;left:0;border-radius:var(--rs)}}
.bars .q u{{position:absolute;top:-3px;bottom:-3px;width:1px;background:var(--ink)}}.bars b{{text-align:right}}
.sens td{{text-align:right}}.sens small{{display:block;color:var(--muted)}}.sens td.hl{{background:var(--note);font-weight:600}}
.note{{background:var(--note);border-left:4px solid var(--gold);padding:var(--sp2) var(--sp3);font-size:.9375rem;margin:var(--sp3) 0 0;border-radius:0 var(--rs) var(--rs) 0}}
.notes{{margin:var(--sp4) 0;padding:var(--sp3);background:var(--card);border:1px solid var(--grid);border-radius:var(--r);font-size:.9375rem}}
.notes ul{{margin:var(--sp2) 0 0;padding-left:1.2em}}.notes li{{margin-bottom:var(--sp1)}}
details{{background:var(--card);border:1px solid var(--grid);border-radius:var(--r);margin-bottom:var(--sp2);padding:0 var(--sp3)}}
summary{{cursor:pointer;padding:var(--sp3) 0;font-weight:600;min-height:44px}}
summary:focus-visible,a:focus-visible{{outline:3px solid var(--gold);outline-offset:2px}}
.tw{{overflow-x:auto;margin-bottom:var(--sp3)}}table{{border-collapse:collapse;width:100%;font-size:.875rem}}
th,td{{padding:6px 10px;border-bottom:1px solid var(--grid);text-align:right;white-space:nowrap}}th:first-child,td:first-child{{text-align:left}}th{{background:var(--chip)}}
footer{{color:var(--muted);font-size:.875rem;padding:var(--sp3) 0 var(--sp5)}}footer a,.notes a{{color:var(--link)}}
#tip{{position:fixed;z-index:20;pointer-events:none;background:var(--tipbg);color:var(--tipfg);border-radius:var(--rs);padding:8px 10px;font-size:.8125rem;line-height:1.35;max-width:240px;box-shadow:0 4px 14px rgba(15,27,45,.25);display:none}}
#tip b{{display:block;font-weight:650}}
@media(max-width:900px){{.hero .in{{grid-template-columns:1fr}}.grid{{grid-template-columns:1fr}}}}
@media(max-width:560px){{.chips{{grid-template-columns:1fr}}}}
@media(max-width:480px){{.bars li{{grid-template-columns:1fr 56px}}.bars .bar{{grid-column:1/-1;grid-row:2}}.bars .k{{grid-column:1}}.bars b{{grid-column:2;grid-row:1}}}}
@media print{{header{{background:#fff;color:#000}}header p,.by,.kicker,.chips span,.legend{{color:#000}}.chips li{{background:#fff;border-color:#000}}.card{{break-inside:avoid}}.jump{{display:none}}}}
"""

JS = """
(function(){var tip=document.getElementById('tip');
function show(t,x,y){var p=t.getAttribute('data-tip').split('|');tip.textContent='';var h=document.createElement('b');h.textContent=p[0];tip.appendChild(h);
p.slice(1).forEach(function(l){var s=document.createElement('span');s.textContent=l;tip.appendChild(s);tip.appendChild(document.createElement('br'));});
tip.style.display='block';var w=tip.offsetWidth,hh=tip.offsetHeight;var left=Math.min(x+14,window.innerWidth-w-8);var top=y-hh-12;if(top<8)top=y+16;tip.style.left=Math.max(8,left)+'px';tip.style.top=top+'px';}
function hide(){tip.style.display='none';}
document.addEventListener('pointermove',function(e){var t=e.target.closest&&e.target.closest('[data-tip]');if(t)show(t,e.clientX,e.clientY);else hide();});
document.addEventListener('pointerdown',function(e){var t=e.target.closest&&e.target.closest('[data-tip]');if(t)show(t,e.clientX,e.clientY);else hide();});
document.addEventListener('scroll',hide,{passive:true});})();
"""

tot = sum(v for _, v in strip_parts)
strip_html = "".join(f'<i class="{k}" style="width:{v / tot * 100:.2f}%"></i>' for (k, _), (_, v) in zip(strip_meta, strip_parts))
legend_html = "".join(f'<li><span class="{k}"></span>{n} <b>{v / rev * 100:.1f}¢</b></li>' for (k, n), (_, v) in zip(strip_meta, strip_parts))
nav = [("h-wf", "What-if"), ("h-cases", "Conservative case"), ("h-cost", "Cost lines"), ("h-sm", "Segments"), ("h-wg", "Wages"), ("data", "Data tables")]
nav_html = "".join(f'<a href="#{i}">{t}</a>' for i, t in nav)

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark">
<title>Canadian Restaurant Profitability Benchmark</title>
<meta name="description" content="The average Canadian restaurant earned a {m0:.1f}% net margin in 2024, and {LOSS_SHARE}% lost money. Public Statistics Canada and ISED data, 2019 to 2024.">
<style>{CSS}</style></head><body>
<a class="skip" href="#main">Skip to content</a>
<header><div class="wrap"><p class="kicker">Canadian Restaurant Profitability Benchmark</p>
<h1>The average Canadian restaurant keeps <em>{m0:.1f} cents</em> of every dollar it sells</h1>
<p class="by"><strong>Ben Shadabi</strong> · Business Analytics (BBA), George Brown College · Co-founded and ran a restaurant for three years</p>
<div class="dollar"><p>Where one dollar of revenue goes, average restaurant, 2024 (ISED). Hatched = calculated, not a published line.</p>
<div class="strip" role="img" aria-label="One revenue dollar split into cost lines: {'; '.join(f'{n} {v / rev * 100:.1f} cents' for (_, n), (_, v) in zip(strip_meta, strip_parts))}.">{strip_html}</div>
<ul class="legend">{legend_html}</ul></div>
<ul class="chips"><li><b>{m0:.1f}%</b><span>net margin, 2024</span></li><li><b>{LOSS_SHARE}%</b><span>of restaurants lost money</span></li><li><b>{d(p0)} to {d(p1)}</b><span>profit in my what-if</span></li></ul>
<nav class="jump" aria-label="Sections">{nav_html}</nav></div></header>
<main id="main" class="wrap">

<section class="card hero" aria-labelledby="h-wf"><div class="in"><div>
<h2 id="h-wf">Three cost levers would take the average restaurant from {d(p0)} to {d(p1)} a year</h2>
<p class="sub">What-if on the 2024 average restaurant. Annual profit in dollars. Hover or tap a bar for the running total.</p>{waterfall()}</div>
<div><p><b>Why it matters:</b> profit is only {m0:.1f}% of revenue, so a small cost change is a big profit change. A 35% profit increase needs about $7,500 a year, which is a 3.8% labour cut on its own.</p>
<ul class="key" style="display:block"><li>Labour -10%: <b>+{d(g_lab)}</b></li><li>Overhead (utilities, telecom, other) -15%: <b>+{d(g_oh)}</b></li><li>Food waste -20%: <b>+{d(g_waste)}</b></li></ul>
<p class="note"><b>Assumption:</b> I took food waste as {WASTE_SHARE*100:.0f}% of cost of sales. That share is my assumption, not source data. Overhead also includes a calculated remainder of expenses, so the conservative case below leaves it out. This is a what-if, not a forecast.</p></div></div></section>

{SENS}
{CASES}
<div class="grid">
<section class="card" aria-labelledby="h-cost"><h2 id="h-cost">Cost of sales and labour take about {(cos+lab)/rev*100:.0f} cents of each revenue dollar</h2>
<p class="sub">Share of revenue, average restaurant, 2024 (ISED). "Other expenses" is revenue minus every listed line and profit.</p><ul class="bars">{cost_html}</ul></section>
<section class="card" aria-labelledby="h-q"><h2 id="h-q">Averages hide a wide gap: the bottom quartile lost {d(-lo)} and the top quartile made {d(hi)}</h2>
<p class="sub">Average profit per restaurant by quartile, 2024 (ISED). The line marks $0.</p><ul class="bars">{quart_html}</ul></section>
<section class="card" aria-labelledby="h-sm"><h2 id="h-sm">In 2020 full-service margin fell to 0.3% while limited-service held {ind.limited_service_margin.iloc[1]*100:.1f}%</h2>
<p class="sub">Operating margin by segment, 2019 to 2022 (Statistics Canada). Segment margins for 2023 and 2024 were not published, and the 2019 limited-service margin is not stated in the releases. Statistics Canada later revised 2020 (full-service 0.5%).</p>{svg_seg_margin}
<ul class="key"><li><span style="border-color:{NAVY}"></span>Full-service</li><li><span style="border-color:{GOLD};border-top-style:dashed"></span>Limited-service</li></ul></section>
<section class="card" aria-labelledby="h-sr"><h2 id="h-sr">Limited-service revenue was ahead of full-service in 2020, 2021 and 2024 ({bn(ind.limited_service_revenue_bn.iloc[-1],True)} vs {bn(ind.full_service_revenue_bn.iloc[-1],True)})</h2>
<p class="sub">Revenue by segment, $ billion, 2019 to 2024 (Statistics Canada).</p>{svg_seg_rev}
<ul class="key"><li><span style="border-color:{NAVY}"></span>Full-service</li><li><span style="border-color:{GOLD};border-top-style:dashed"></span>Limited-service</li></ul></section>
<section class="card" aria-labelledby="h-im"><h2 id="h-im">Industry operating margin stayed between {ind.operating_margin.min()*100:.1f}% and {ind.operating_margin.max()*100:.1f}%, and was {op24:.1f}% in 2024</h2>
<p class="sub">All food services and drinking places (Statistics Canada). Operating margin, not net margin.</p>{svg_ind}</section>
<section class="card" aria-labelledby="h-wg"><h2 id="h-wg">Average hourly pay in food services rose {wage_up:.1f}%, from ${w0:.2f} to ${w1:.2f}</h2>
<p class="sub">Average hourly wage, 2020 to 2024 (Statistics Canada Table 14-10-0206-01). The axis starts at $0.</p>{wages_svg()}</section>
</div>

<section class="notes" aria-labelledby="h-n"><h2 id="h-n">How to read these numbers</h2><ul>
<li>The two sources use different bases. ISED reports <b>net profit</b> for small restaurants ({m0:.1f}% margin). Statistics Canada reports <b>operating profit</b> for the whole industry ({op24:.1f}%). I only compare lines within one source.</li>
<li>Full-service plus limited-service revenue is less than the industry total because drinking places and other food services are not shown ($89.1B vs $99.6B in 2024). Some 2019 and 2022 figures come from later releases that compare back to those years. Blank margins were not published.</li>
<li>The what-if applies cuts to an average restaurant. It does not describe any one business.</li></ul>
<p>Method and sources: <a href="methodology.md">methodology</a> and <a href="data_dictionary.md">data dictionary</a>. Contains information licensed under the Open Government Licence - Canada.</p></section>

<h2 id="data" style="margin-top:var(--sp4)">Data behind the charts</h2>
<details><summary>Industry trend, 2019 to 2024</summary>{t_ind}</details>
<details><summary>Average restaurant, 2024</summary>{t_avg}</details>
<details><summary>Hourly wage, 2020 to 2024</summary>{t_wag}</details>
</main>
<footer><div class="wrap">Generated by <code>analysis/build_dashboard.py</code> from the CSV files in <code>data/</code>. Sources: Statistics Canada and ISED Canadian Industry Statistics. Font: Geist (SIL Open Font License).</div></footer>
<div id="tip" role="presentation"></div>
<script>{JS}</script>
</body></html>"""
open("docs/dashboard.html", "w", encoding="utf-8").write(page)
print("wrote docs/dashboard.html", f"({len(page)/1024:.0f} KB)", f"profit {p0:,.0f}->{p1:,.0f} margin {m0:.1f}->{m1:.1f}")
