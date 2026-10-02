"""Build docs/dashboard.html (the dashboard) from the CSV files in data/.
Every number on the page is read from the CSVs or computed here. Nothing is typed in by hand
(the share of loss-making restaurants is in data/restaurant_counts_2024.csv).
Run from the repo root:  python analysis/build_dashboard.py
Requires: pandas
"""
import html
import pandas as pd

# ---------- design tokens (Option A: "Ledger", light, navy + one gold accent) ----------
INK, NAVY, SLATE, MUTED, GRID = "#0F1B2D", "#12355B", "#5B7189", "#4B5563", "#D5DAE1"
GOLD, GOLD_TXT, GREEN, RED = "#B7791F", "#8A5A00", "#1B7F5C", "#B42318"

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
    bw, gap = 74, (W - 16 - 5 * 74) / 4; run = 0
    for i, (lbl, v, c) in enumerate(steps):
        x = 8 + i * (bw + gap)
        if c is None:
            y, h, col, txt, run = ypx(v), bot - ypx(v), NAVY, d(v), v
        else:
            y, h, col, txt = ypx(run + v), ypx(run) - ypx(run + v), c, "+" + d(v); run += v
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw}" height="{h:.1f}" fill="{col}"/>')
        s.append(f'<text x="{x+bw/2:.1f}" y="{y-7:.1f}" text-anchor="middle" class="lb" fill="{INK}">{txt}</text>')
        a, b = (lbl.split(" ", 1) + [""])[:2] if c else lbl.split(" ", 1)
        s.append(f'<text x="{x+bw/2:.1f}" y="{bot+17}" text-anchor="middle" class="ax">{a}</text>'
                 f'<text x="{x+bw/2:.1f}" y="{bot+32}" text-anchor="middle" class="ax">{b}</text>')
    return "".join(s) + "</svg>"

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

CSS = f"""
:root{{--ink:{INK};--navy:{NAVY};--slate:{SLATE};--muted:{MUTED};--grid:{GRID};--gold:{GOLD};--goldtxt:{GOLD_TXT};--green:{GREEN};--red:{RED};
--bg:#F6F8FA;--card:#fff;--sp1:4px;--sp2:8px;--sp3:16px;--sp4:24px;--sp5:32px;
--serif:"Source Serif 4",Georgia,"Times New Roman",serif;--sans:Inter,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
*{{box-sizing:border-box}}html{{-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 var(--sans)}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 var(--sp3)}}
.skip{{position:absolute;left:-999px}}.skip:focus{{left:var(--sp3);top:var(--sp2);background:#fff;padding:var(--sp2);z-index:9}}
header{{background:var(--navy);color:#fff;padding:36px 0 32px;border-bottom:4px solid #E3B965}}
.kicker{{margin:0 0 12px;font-size:.8125rem;letter-spacing:.08em;text-transform:uppercase;color:#E3B965;font-weight:600}}
header h1{{font:600 clamp(1.65rem,4.6vw,2.6rem)/1.15 var(--serif);letter-spacing:-.01em;margin:0;max-width:26ch}}
.by{{margin:14px 0 0;font-size:.9375rem;color:#DCE6F2}}.by strong{{color:#fff}}
.chips{{display:flex;gap:12px;flex-wrap:wrap;margin:22px 0 0;padding:0;list-style:none}}
.chips li{{padding:10px 14px;border-radius:6px;min-width:150px;flex:1 1 150px;max-width:260px;background:#1B4570;border:1px solid #3A6290}}
.chips b{{display:block;font:600 1.375rem/1.1 var(--serif)}}.chips span{{font-size:.8125rem;color:#DCE6F2}}
h2{{font:600 1.125rem/1.35 var(--serif);margin:0 0 var(--sp2);color:var(--ink)}}
.card{{background:var(--card);border:1px solid var(--grid);border-radius:6px;padding:var(--sp3) var(--sp3) var(--sp4)}}
.hero{{margin:var(--sp4) 0 var(--sp3)}}
.hero .in{{display:grid;grid-template-columns:3fr 2fr;gap:var(--sp4);align-items:center}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:var(--sp3);margin-bottom:var(--sp3)}}
.sub{{color:var(--muted);font-size:.875rem;margin:0 0 var(--sp2)}}
svg{{width:100%;height:auto;display:block}}svg .ax{{font:15px var(--sans);fill:var(--muted)}}svg .lb{{font:600 15px var(--sans)}}
.key{{display:flex;gap:var(--sp3);flex-wrap:wrap;font-size:.875rem;margin:var(--sp2) 0 0;padding:0;list-style:none}}
.key span{{display:inline-block;width:22px;height:0;border-top:3px solid;vertical-align:middle;margin-right:6px}}
.bars{{list-style:none;margin:0;padding:0}}.bars li{{display:grid;grid-template-columns:minmax(120px,38%) 1fr 56px;gap:var(--sp2);align-items:center;margin:0 0 var(--sp2);font-size:.9375rem}}
.bars .bar{{display:block;background:#EEF1F5;height:16px;border-radius:2px;position:relative}}.bars .bar i{{position:absolute;top:0;bottom:0;left:0;border-radius:2px}}
.bars .q i{{}}.bars .q u{{position:absolute;top:-3px;bottom:-3px;width:1px;background:var(--ink)}}.bars b{{text-align:right;font-variant-numeric:tabular-nums}}
.sens td{{text-align:right}}.sens small{{display:block;color:var(--muted)}}.sens td.hl{{background:#FFF8E6;font-weight:600}}
.note{{background:#FFF8E6;border-left:4px solid var(--gold);padding:var(--sp2) var(--sp3);font-size:.9375rem;margin:var(--sp3) 0 0}}
.notes{{margin:var(--sp4) 0;padding:var(--sp3);background:var(--card);border:1px solid var(--grid);border-radius:6px;font-size:.9375rem}}
.notes ul{{margin:var(--sp2) 0 0;padding-left:1.2em}}.notes li{{margin-bottom:var(--sp1)}}
details{{background:var(--card);border:1px solid var(--grid);border-radius:6px;margin-bottom:var(--sp2);padding:0 var(--sp3)}}
summary{{cursor:pointer;padding:var(--sp3) 0;font-weight:600;min-height:44px}}
summary:focus-visible,a:focus-visible{{outline:3px solid var(--gold);outline-offset:2px}}
.tw{{overflow-x:auto;margin-bottom:var(--sp3)}}table{{border-collapse:collapse;width:100%;font-size:.875rem;font-variant-numeric:tabular-nums}}
th,td{{padding:6px 10px;border-bottom:1px solid var(--grid);text-align:right;white-space:nowrap}}th:first-child,td:first-child{{text-align:left}}th{{background:#EEF1F5}}
footer{{color:var(--muted);font-size:.875rem;padding:var(--sp3) 0 var(--sp5)}}footer a,.notes a{{color:var(--navy)}}
@media(max-width:900px){{.hero .in{{grid-template-columns:1fr}}.grid{{grid-template-columns:1fr}}}}
@media(max-width:480px){{.bars li{{grid-template-columns:1fr 56px}}.bars .bar{{grid-column:1/-1;grid-row:2}}.bars .k{{grid-column:1}}.bars b{{grid-column:2;grid-row:1}}}}
@media print{{header{{background:#fff;color:#000}}header p,.by,.kicker,.chips span{{color:#000}}.chips li{{background:#fff;border-color:#000}}.card{{break-inside:avoid}}}}
"""

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Canadian Restaurant Profitability Benchmark</title>
<meta name="description" content="The average Canadian restaurant earned a {m0:.1f}% net margin in 2024, and {LOSS_SHARE}% lost money. Public Statistics Canada and ISED data, 2019 to 2024.">
<style>{CSS}</style></head><body>
<a class="skip" href="#main">Skip to content</a>
<header><div class="wrap"><p class="kicker">Canadian Restaurant Profitability Benchmark</p>
<h1>The average Canadian restaurant keeps {m0:.1f} cents of every dollar it sells</h1>
<p class="by"><strong>Ben Shadabi</strong> · Business Analytics (BBA), George Brown College · Built by a former restaurant owner</p>
<ul class="chips"><li><b>{m0:.1f}%</b><span>net margin, 2024</span></li><li><b>{LOSS_SHARE}%</b><span>of restaurants lost money</span></li><li><b>{d(p0)} to {d(p1)}</b><span>profit in my what-if</span></li></ul></div></header>
<main id="main" class="wrap">


<section class="card hero" aria-labelledby="h-wf"><div class="in"><div>
<h2 id="h-wf">Three cost levers would take the average restaurant from {d(p0)} to {d(p1)} a year</h2>
<p class="sub">What-if on the 2024 average restaurant. Annual profit, $.</p>{waterfall()}</div>
<div><p><b>Why it matters:</b> profit is only {m0:.1f}% of revenue, so a small cost change is a big profit change. Reaching +35% profit needs about $7,500 a year, a 3.8% labour cut on its own.</p>
<ul class="key" style="display:block"><li>Labour -10%: <b>+{d(g_lab)}</b></li><li>Overhead (utilities, telecom, other) -15%: <b>+{d(g_oh)}</b></li><li>Food waste -20%: <b>+{d(g_waste)}</b></li></ul>
<p class="note"><b>Assumption:</b> food waste is taken as {WASTE_SHARE*100:.0f}% of cost of sales. That share is my assumption, not source data. This is a what-if, not a forecast.</p></div></div></section>

{SENS}
<div class="grid">
<section class="card" aria-labelledby="h-cost"><h2 id="h-cost">Cost of sales and labour take about {(cos+lab)/rev*100:.0f} cents of each revenue dollar</h2>
<p class="sub">Share of revenue, average restaurant, 2024 (ISED). "Other expenses" is revenue minus every listed line and profit.</p><ul class="bars">{cost_html}</ul></section>
<section class="card" aria-labelledby="h-q"><h2 id="h-q">Averages hide a wide gap: the bottom quartile lost {d(-lo)}, the top quartile made {d(hi)}</h2>
<p class="sub">Average profit per restaurant by quartile, 2024 (ISED). The line marks $0.</p><ul class="bars">{quart_html}</ul></section>
<section class="card" aria-labelledby="h-sm"><h2 id="h-sm">In 2020 full-service margin fell to 0.3% while limited-service held {ind.limited_service_margin.iloc[1]*100:.1f}%</h2>
<p class="sub">Operating margin by segment, 2019 to 2022 (Statistics Canada). Segment margins for 2023 and 2024 were not published, and the 2019 limited-service margin is not stated in the releases. 2020 was later revised (full-service 0.5%).</p>{svg_seg_margin}
<ul class="key"><li><span style="border-color:{NAVY}"></span>Full-service</li><li><span style="border-color:{GOLD};border-top-style:dashed"></span>Limited-service</li></ul></section>
<section class="card" aria-labelledby="h-sr"><h2 id="h-sr">Limited-service revenue was ahead of full-service in 2020, 2021 and 2024 ({bn(ind.limited_service_revenue_bn.iloc[-1],True)} vs {bn(ind.full_service_revenue_bn.iloc[-1],True)})</h2>
<p class="sub">Revenue by segment, $ billion, 2019 to 2024 (Statistics Canada).</p>{svg_seg_rev}
<ul class="key"><li><span style="border-color:{NAVY}"></span>Full-service</li><li><span style="border-color:{GOLD};border-top-style:dashed"></span>Limited-service</li></ul></section>
<section class="card" aria-labelledby="h-im"><h2 id="h-im">Industry operating margin stayed between {ind.operating_margin.min()*100:.1f}% and {ind.operating_margin.max()*100:.1f}%, and was {op24:.1f}% in 2024</h2>
<p class="sub">All food services and drinking places (Statistics Canada). Operating margin, not net margin.</p>{svg_ind}</section>
<section class="card" aria-labelledby="h-wg"><h2 id="h-wg">Average hourly pay in food services rose {wage_up:.1f}%, from ${w0:.2f} to ${w1:.2f}</h2>
<p class="sub">Average hourly wage, 2020 to 2024 (Statistics Canada Table 14-10-0206-01). Axis starts at $0.</p>{wages_svg()}</section>
</div>

<section class="notes" aria-labelledby="h-n"><h2 id="h-n">How to read these numbers</h2><ul>
<li><b>Two sources, two bases.</b> ISED reports <b>net profit</b> for small restaurants ({m0:.1f}% margin). Statistics Canada reports <b>operating profit</b> for the whole industry ({op24:.1f}%). Compare lines within one source only.</li>
<li>Full-service plus limited-service revenue is less than the industry total because drinking places and other food services are not shown ($89.1B vs $99.6B in 2024). Some 2019 and 2022 figures come from later releases that compare back to those years. Blank margins were not published.</li>
<li>The what-if applies cuts to an average restaurant. It does not describe any one business.</li></ul>
<p>Method and sources: <a href="methodology.md">methodology</a> and <a href="data_dictionary.md">data dictionary</a>. Contains information licensed under the Open Government Licence - Canada.</p></section>

<h2 style="margin-top:var(--sp4)">Data behind the charts</h2>
<details><summary>Industry trend, 2019 to 2024</summary>{t_ind}</details>
<details><summary>Average restaurant, 2024</summary>{t_avg}</details>
<details><summary>Hourly wage, 2020 to 2024</summary>{t_wag}</details>
</main>
<footer><div class="wrap">Generated by <code>analysis/build_dashboard.py</code> from the CSV files in <code>data/</code>. Sources: Statistics Canada and ISED Canadian Industry Statistics.</div></footer>
</body></html>"""
open("docs/dashboard.html", "w", encoding="utf-8").write(page)
print("wrote docs/dashboard.html", f"({len(page)/1024:.0f} KB)", f"profit {p0:,.0f}->{p1:,.0f} margin {m0:.1f}->{m1:.1f}")
