"""Build assets/banner.png (1280x640), the title picture used on GitHub (social preview) and at the top of the README.
Every number on the picture is read from data/. The bar is drawn to scale: one revenue dollar split into its cost lines.
Run from the repo root:  python analysis/build_banner.py
Requires: pandas and playwright with chromium (pip install playwright). Not part of the CI checks, because it needs a browser.
"""
import base64
import pandas as pd
from playwright.sync_api import sync_playwright

a = pd.read_csv("data/average_restaurant_2024.csv").set_index("line")["dollars"]
cnt = pd.read_csv("data/restaurant_counts_2024.csv").set_index("metric")["value"]
rev = a["revenue"]
other = rev - a["cost_of_sales"] - a["labour_and_commissions"] - a["rent"] - a["utilities_and_telecom"] - a["amortization_and_depletion"] - a["net_profit"]
parts = [("cos", "Cost of sales", a["cost_of_sales"]), ("lab", "Labour", a["labour_and_commissions"]),
         ("oth", "Other expenses (calculated)", other), ("rent", "Rent", a["rent"]),
         ("amo", "Amortization", a["amortization_and_depletion"]), ("uti", "Utilities", a["utilities_and_telecom"]),
         ("pro", "Profit", a["net_profit"])]
total = sum(v for _, _, v in parts)  # equals revenue
cents = {k: v / rev * 100 for k, _, v in parts}
x, left = 0.0, {}
for k, _, v in parts:
    left[k] = x
    x += v / total * 100
W = 1136  # width of the bar in pixels
px = lambda pct: pct / 100 * W
font = base64.b64encode(open("docs/fonts/geist-latin-wght.woff2", "rb").read()).decode()

segs = "".join(f'<i class="s {k}" style="left:{px(left[k]):.1f}px;width:{px(v / total * 100) - 3:.1f}px"></i>' for k, _, v in parts)
cap = lambda k, name: (f'<div class="cap" style="left:{px(left[k]):.1f}px"><b>{cents[k]:.1f}¢</b><span>{name}</span></div>')
thin_l, thin_r = px(left["amo"]), px(left["pro"]) - 3
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Geist;src:url(data:font/woff2;base64,{font}) format("woff2");font-weight:100 900}}
*{{box-sizing:border-box;margin:0}}
body{{width:1280px;height:640px;background:#0E2745;color:#fff;font-family:Geist,sans-serif;position:relative;overflow:hidden}}
.k{{position:absolute;left:72px;top:60px;font-size:17px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#E3B965}}
h1{{position:absolute;left:72px;top:100px;width:1060px;font-size:58px;line-height:1.08;font-weight:650;letter-spacing:-.02em}}
h1 em{{font-style:normal;color:#E3B965}}
.sub{{position:absolute;left:72px;top:246px;font-size:22px;color:#C9D8EA}}
.lbl{{position:absolute;left:72px;top:330px;font-size:16px;color:#9FB6D1;letter-spacing:.01em}}
.bar{{position:absolute;left:72px;top:376px;width:{W}px;height:78px}}
.s{{position:absolute;top:0;height:78px;background:#2F5F96}}
.s.oth{{background:repeating-linear-gradient(135deg,#2F5F96 0 7px,#0E2745 7px 10px)}}
.s.pro{{background:#E3B965}}
.cap{{position:absolute;top:88px;font-size:15px;color:#C9D8EA;line-height:1.25;white-space:nowrap}}
.cap b{{display:block;font-size:24px;font-weight:650;color:#fff;letter-spacing:-.01em;font-variant-numeric:tabular-nums}}
.thin{{position:absolute;top:84px;left:{thin_l:.1f}px;width:{thin_r - thin_l:.1f}px;border-top:2px solid #6F8FB5}}
.thinCap{{position:absolute;top:140px;right:{W - thin_r:.1f}px;font-size:14px;color:#C9D8EA;text-align:right;white-space:nowrap}}
.pro-call{{position:absolute;right:0;top:-98px;text-align:right;color:#E3B965;font-size:20px;line-height:1.2;font-weight:600;white-space:nowrap}}
.pro-call b{{display:block;font-size:38px;font-weight:700;letter-spacing:-.02em}}
.pro-call:after{{content:"";position:absolute;right:{px(cents['pro']) / 2 - 1:.1f}px;top:100%;height:14px;border-right:2px solid #E3B965}}
.foot{{position:absolute;left:72px;right:72px;bottom:44px;display:flex;justify-content:space-between;font-size:17px;color:#C9D8EA}}
.foot b{{color:#fff;font-weight:600}}
</style></head><body>
<div class="k">Canadian Restaurant Profitability Benchmark</div>
<h1>The average Canadian restaurant keeps <em>{cents['pro']:.1f} cents</em> of every dollar it sells</h1>
<div class="sub">{cnt['loss_making_share']}% of restaurants lost money in 2024.</div>
<div class="lbl">Where one dollar of revenue goes. Average restaurant, 2024 (ISED). Bar drawn to scale; hatched = calculated, not published.</div>
<div class="bar">{segs}
<div class="pro-call"><b>{cents['pro']:.1f}¢</b>profit</div>
{cap('cos', 'Cost of sales')}{cap('lab', 'Labour')}{cap('oth', 'Other (calculated)')}{cap('rent', 'Rent')}
<div class="thin"></div><div class="thinCap">Amortization {cents['amo']:.1f}¢<br>Utilities {cents['uti']:.1f}¢</div></div>
<div class="foot"><span><b>Ben Shadabi</b> &nbsp;·&nbsp; Business Analytics (BBA), George Brown College</span><span>Statistics Canada and ISED data, 2019 to 2024</span></div>
</body></html>"""

open("assets/banner_source.html", "w", encoding="utf-8").write(html)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 640}, device_scale_factor=1)
    pg.goto("file:///" + __import__("os").path.abspath("assets/banner_source.html").lstrip("/"))
    pg.wait_for_timeout(300)
    pg.screenshot(path="assets/banner.png")
    b.close()
import os
os.remove("assets/banner_source.html")
print("wrote assets/banner.png", {k: round(v, 1) for k, v in cents.items()})
