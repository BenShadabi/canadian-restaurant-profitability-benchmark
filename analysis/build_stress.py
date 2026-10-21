"""Build docs/stress.html (the cost-shock simulator) from data/average_restaurant_2024.csv. The preset table is computed by analysis/stress_model.py;
the sliders run the same formulas in JavaScript. Run from the repo root:  python analysis/build_stress.py
"""
import html, json, sys
sys.path.insert(0, "analysis")
import stress_model as m

b = m.base()
e = html.escape
d = lambda v: ("-$" if v < 0 else "$") + f"{abs(v):,.0f}"
pc = lambda v: f"{v:+.1%}"
rows = ""
for name, why, p in m.PRESETS:
    r = m.run(b, **p)
    be = "never" if r["be_vol"] is None else pc(r["be_vol"])
    rows += f'<tr><td><b>{e(name)}</b><br><span class="why">{e(why)}</span></td><td>{d(r["profit"])}</td><td>{r["margin"]:.1%}</td><td>{pc(r["price_needed"])}</td><td>{be}</td></tr>'
presets_js = json.dumps([{"n": n, "p": p} for n, _, p in m.PRESETS])
bench_js = json.dumps({k: round(float(v), 2) for k, v in b.items()})
base_margin = b["profit"] / b["rev"]
cushion = m.run(b, vol=-0.2)["be_vol"]

TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark">
<title>Stress-test the average restaurant | Ben Shadabi</title>
<meta name="description" content="Move food, wage, rent, menu price and sales sliders and see what happens to the average Canadian restaurant's profit. A what-if tool built on public ISED data.">
<style>
@font-face{font-family:Geist;src:url(fonts/geist-latin-wght.woff2) format("woff2");font-weight:100 900;font-display:swap}
:root{color-scheme:light dark;--ink:#0F1B2D;--muted:#4B5563;--grid:#D5DAE1;--bg:#F4F6F9;--card:#fff;--note:#FFF6E0;--gold:#B7791F;--link:#12355B;--bad:#B42318;--good:#1B7F4B;--r:12px;--sans:Geist,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
@media(prefers-color-scheme:dark){:root{--ink:#E8EEF6;--muted:#A7B4C6;--grid:#2A3750;--bg:#0A111F;--card:#111B2E;--note:#2A2412;--gold:#D19A3C;--link:#9CC3F0;--bad:#F97066;--good:#4ADE80}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 var(--sans);font-variant-numeric:tabular-nums}
.wrap{max-width:1000px;margin:0 auto;padding:0 20px}
header{background:#0E2745;color:#fff;border-bottom:4px solid #E3B965;padding:34px 0 30px}
.eyebrow{font-size:.8125rem;letter-spacing:.08em;text-transform:uppercase;color:#E3B965;font-weight:600;margin:0 0 10px}
h1{font:700 clamp(1.7rem,5vw,2.6rem)/1.1 var(--sans);letter-spacing:-.02em;margin:0 0 10px}header p{margin:0;color:#C9D8EA;max-width:62ch}
h2{font:700 1.4rem/1.25 var(--sans);letter-spacing:-.01em;margin:44px 0 10px}a{color:var(--link)}a:focus-visible,input:focus-visible,button:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.card{background:var(--card);border:1px solid var(--grid);border-radius:var(--r);padding:18px 20px;margin:16px 0}
.note{background:var(--note);border-left:4px solid var(--gold);padding:12px 18px;font-size:.9375rem;border-radius:0 var(--r) var(--r) 0;margin:20px 0}
.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px;align-items:start}
.ctl{display:grid;grid-template-columns:1fr auto;gap:4px 12px;margin:0 0 14px}.ctl label{font-size:.9375rem;color:var(--muted)}.ctl output{font-weight:700;font-size:.9375rem;min-width:4.5rem;text-align:right}
.ctl input[type=range]{grid-column:1/-1;width:100%;accent-color:var(--link);min-height:28px}
.presets{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}
button{min-height:42px;padding:0 14px;font:600 .9375rem var(--sans);border-radius:999px;border:1px solid var(--link);background:transparent;color:var(--link);cursor:pointer;transition:background .2s,color .2s}
button:hover,button.on{background:var(--link);color:var(--card)}
.big{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:0 0 14px}.big div{border-top:3px solid var(--gold);background:var(--bg);border-radius:8px;padding:10px 12px}
.big b{display:block;font:700 1.45rem/1.15 var(--sans)}.big span{font-size:.8125rem;color:var(--muted)}
.bad{color:var(--bad)}.good{color:var(--good)}
.row{display:grid;grid-template-columns:7.5rem 1fr 5.5rem;gap:8px;align-items:center;font-size:.875rem;margin:5px 0}.row .t{height:16px;position:relative;background:var(--bg);border-radius:4px}
.row .t i{position:absolute;top:0;height:100%;border-radius:3px;transition:left .5s ease,width .5s ease,background .3s}.row .v{text-align:right;font-weight:650}
.row .mid{position:absolute;left:50%;top:-3px;bottom:-3px;width:1px;background:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:.9375rem}th,td{text-align:right;padding:10px;border-bottom:1px solid var(--grid);vertical-align:top}th:first-child,td:first-child{text-align:left}th{color:var(--muted);font-weight:600}.why{color:var(--muted);font-size:.8125rem}
.src li{margin-bottom:10px}.src small{color:var(--muted)}
ul{padding-left:1.2em}footer{color:var(--muted);font-size:.875rem;padding:26px 0 44px}
@media(max-width:820px){.grid{grid-template-columns:1fr}.big{grid-template-columns:1fr}.row{grid-template-columns:6rem 1fr 5rem}}
</style><link rel="stylesheet" href="motion.css"></head><body>
<header><div class="wrap"><p class="eyebrow">Student project by Ben Shadabi · Business Analytics (BBA), George Brown College</p>
<h1>Stress-test the average restaurant</h1>
<p>Food, wages and rent keep climbing, and construction can empty a street. Move the sliders and see what happens to the profit of the average Canadian restaurant ($849,200 of sales and $21,500 of profit in 2024).</p></div></header>
<main class="wrap">
<p class="note"><strong>A what-if, not a forecast.</strong> The starting point is the ISED 2024 average for 65,071 restaurants (<a href="index.html">see the project page</a>). Averages hide big gaps between restaurants, and the sliders are yours to set. I did not find a public figure for how much construction cuts sales, so the construction preset is an illustration.</p>

<div class="grid">
<div class="card">
<div class="presets" role="group" aria-label="Presets" id="presets"></div>
<div class="ctl"><label for="food">Food and drink costs (cost of sales)</label><output id="o-food"></output><input id="food" type="range" min="-5" max="25" step="0.5" value="0"></div>
<div class="ctl"><label for="wage">Wage and labour rates</label><output id="o-wage"></output><input id="wage" type="range" min="-5" max="20" step="0.5" value="0"></div>
<div class="ctl"><label for="rent">Rent</label><output id="o-rent"></output><input id="rent" type="range" min="0" max="30" step="0.5" value="0"></div>
<div class="ctl"><label for="other">Utilities, insurance and other costs</label><output id="o-other"></output><input id="other" type="range" min="0" max="25" step="0.5" value="0"></div>
<div class="ctl"><label for="price">Menu prices you charge</label><output id="o-price"></output><input id="price" type="range" min="0" max="20" step="0.5" value="0"></div>
<div class="ctl"><label for="vol">Customers and sales volume (construction, traffic)</label><output id="o-vol"></output><input id="vol" type="range" min="-40" max="20" step="1" value="0"></div>
<div class="ctl"><label for="flex">Share of labour that shrinks when sales fall</label><output id="o-flex"></output><input id="flex" type="range" min="0" max="100" step="5" value="30"></div>
</div>
<div>
<div class="card" aria-live="polite">
<div class="big"><div><b id="r-profit">-</b><span>yearly profit (was $21,500)</span></div><div><b id="r-margin">-</b><span>net margin (was %%BM%%)</span></div><div><b id="r-change">-</b><span>change in profit</span></div></div>
<div class="big"><div><b id="r-price">-</b><span>menu price rise that restores $21,500 at this sales volume</span></div><div><b id="r-be">-</b><span id="r-be-t">sales change that makes profit zero</span></div><div><b id="r-rev">-</b><span>yearly sales</span></div></div>
</div>
<div class="card"><b>Where the profit change comes from</b><div id="wf" style="margin-top:8px"></div><p class="why" style="margin:8px 0 0">Steps are applied in the order shown, so each bar includes the effect of the ones above it. Green is good for profit.</p></div>
</div></div>

<h2>Presets, calculated</h2>
<div class="card" style="overflow-x:auto"><table><thead><tr><th>Scenario</th><th>Profit</th><th>Margin</th><th>Price rise needed</th><th>Sales change to break even</th></tr></thead><tbody>%%ROWS%%</tbody></table></div>
<p class="note">With a 2.5% margin the cushion is thin. In the baseline, sales can fall only %%CUSH%% before the average restaurant stops making money. That is why a 20% fall in sales during construction turns a $21,500 profit into a large loss.</p>

<h2>What has actually been reported</h2>
<ul class="card src">
<li><b>Menu prices.</b> Statistics Canada's consumer price index for food bought at restaurants rose 3.6% in 2024 and 2.6% in 2025 on an annual average basis. <small>I read these through a search summary of Statistics Canada's data, not from the table itself, so check them before quoting.</small></li>
<li><b>Minimum wage.</b> Ontario's general rate was $15.50 in October 2022, $16.55 in 2023, $17.20 in 2024 and $17.60 in 2025 (+2.3%). That is +13.5% from 2022 to 2025. <small>A law-firm guide lists $17.95 from 1 October 2026 and I could not confirm it on the government site.</small></li>
<li><b>Profitability.</b> A Restaurants Canada survey reported that 44% of operators were losing money or just breaking even in November 2025, against 12% in 2019, and that 89% named labour costs and 88% named food costs as top pressures. <small>Survey of operators, not a count of all restaurants.</small></li>
<li><b>Closures.</b> A Dalhousie University food analytics lab estimates a net loss of about 7,000 restaurant establishments in Canada in 2025, with about 4,000 more in 2026. <small>An estimate based on "active, viable" restaurants, so it differs from official counts.</small></li>
<li><b>Construction.</b> In 2020 two Toronto councillors counted 140 business closures along the Eglinton Crosstown LRT route between Black Creek Drive and Yonge Street, and Metrolinx said it did not compensate for lost business. <small>A councillors' count from news coverage at the time, not an audited figure, and it covers all business types.</small></li>
</ul>
<p>The <a href="toronto.html">Toronto map</a> shows where restaurant licences ended from 2023 to 2025, and an <a href="toronto.html#construction">exploratory check</a> found that licences near large construction sites ended more often, but about as much near sites that had already finished, so it cannot tell construction from rent, inflation or the kind of neighbourhood.</p>

<h2>How the model works</h2>
<ul>
<li>Start: the ISED 2024 average restaurant (sales $849,200; cost of sales $380,400; labour $200,200; rent $71,600; everything else $175,500 including a calculated line; profit $21,500).</li>
<li>Cost of sales moves with sales volume. Labour moves with it only for the share you choose. Rent and the "everything else" line stay fixed in dollars unless you move their sliders.</li>
<li>"Price rise needed" is the menu price change that brings profit back to $21,500 at the sales volume you set, assuming customers do not react to the price rise. In real life some will, so treat it as a lower bound.</li>
<li>The code is in <code>analysis/stress_model.py</code> and <code>analysis/build_stress.py</code>, and <code>checks.py</code> recomputes the preset table independently.</li>
</ul>
<p><a href="index.html">Back to the main project</a> · <a href="calculator.html">Compare your own restaurant</a> · <a href="https://github.com/BenShadabi/canadian-restaurant-profitability-benchmark">Code and data</a></p>
</main>
<footer><div class="wrap">Contains information licensed under the Open Government Licence - Canada. Font: Geist (SIL Open Font License). A what-if tool, not financial advice.</div></footer>
<script src="motion.js" defer></script>
<script>
const B=%%BENCH%%, PRESETS=%%PRESETS%%, $=id=>document.getElementById(id);
const IDS=["food","wage","rent","other","price","vol","flex"];
const money=v=>(v<0?"-$":"$")+Math.abs(Math.round(v)).toLocaleString("en-CA"), pct=(v,d=1)=>(v>=0?"+":"")+(v*100).toFixed(d)+"%", sgn=v=>(v>=0?"+":"-")+"$"+Math.abs(Math.round(v)).toLocaleString("en-CA");
function val(){const o={};IDS.forEach(k=>o[k]=parseFloat($(k).value)/100);return o}
function profit(p){const r=B.rev*(1+p.price)*(1+p.vol),c=B.cos*(1+p.food)*(1+p.vol),l=B.lab*(1+p.wage)*(1+p.flex*p.vol);
  return r-c-l-B.rent*(1+p.rent)-B.other*(1+p.other)}
function render(){
  const p=val(); IDS.forEach(k=>{$("o-"+k).textContent=(k==="flex"?Math.round(p[k]*100)+"%":pct(p[k]))});
  const pr=profit(p), rev=B.rev*(1+p.price)*(1+p.vol), cos=B.cos*(1+p.food)*(1+p.vol), lab=B.lab*(1+p.wage)*(1+p.flex*p.vol);
  const costs=cos+lab+B.rent*(1+p.rent)+B.other*(1+p.other);
  $("r-profit").textContent=money(pr); $("r-profit").className=pr<0?"bad":""; $("r-margin").textContent=(pr/rev*100).toFixed(1)+"%";
  const ch=pr-B.profit; $("r-change").textContent=sgn(ch); $("r-change").className=ch<0?"bad":ch>0?"good":"";
  $("r-price").textContent=pct((B.profit+costs)/(B.rev*(1+p.vol))-1); $("r-rev").textContent=money(rev);
  const q=Object.assign({},p,{vol:0}), p0=profit(q), R=B.rev*(1+p.price), C=B.cos*(1+p.food), L=B.lab*(1+p.wage), slope=R-C-L*p.flex;
  if(slope<=0){$("r-be").textContent="never";}else{const bv=-p0/slope;$("r-be").textContent=pct(bv);}
  $("r-be-t").textContent=p0>=0?"sales can fall this much (from today) before profit hits zero":"sales must change this much (from today) just to break even";
  // waterfall: apply steps in order
  const order=[["food","Food costs"],["wage","Wages"],["rent","Rent"],["other","Other costs"],["price","Menu prices"],["vol","Sales volume"]];
  const cur={food:0,wage:0,rent:0,other:0,price:0,vol:0,flex:p.flex}; let prev=B.profit; const steps=[];
  order.forEach(([k,n])=>{cur[k]=p[k];const v=profit(cur);steps.push([n,v-prev]);prev=v});
  const mx=Math.max(1,...steps.map(s=>Math.abs(s[1])));
  $("wf").innerHTML=steps.map(([n,v])=>{const w=Math.abs(v)/mx*50, left=v>=0?50:50-w;
    return '<div class="row"><span>'+n+'</span><span class="t"><span class="mid"></span><i style="left:'+left+'%;width:'+w+'%;background:var(--'+(v>=0?"good":"bad")+')"></i></span><span class="v">'+sgn(v)+'</span></div>'}).join("");
}
$("presets").innerHTML=PRESETS.map((x,i)=>'<button type="button" data-i="'+i+'">'+x.n+'</button>').join("")+'<button type="button" data-i="-1">Reset</button>';
$("presets").addEventListener("click",ev=>{const b=ev.target.closest("button");if(!b)return;const i=+b.dataset.i, pre=i<0?{}:PRESETS[i].p;
  IDS.forEach(k=>$(k).value=k==="flex"?30:Math.round((pre[k]||0)*1000)/10);
  document.querySelectorAll("#presets button").forEach(x=>x.classList.toggle("on",x===b&&i>=0)); render()});
IDS.forEach(k=>$(k).addEventListener("input",()=>{document.querySelectorAll("#presets button").forEach(x=>x.classList.remove("on"));render()}));
render();
</script>
</body></html>
"""
page = TEMPLATE
for k, v in {"ROWS": rows, "BENCH": bench_js, "PRESETS": presets_js, "BM": f"{base_margin:.1%}", "CUSH": f"{abs(cushion):.1%}"}.items():
    page = page.replace(f"%%{k}%%", v)
assert "%%" not in page and "—" not in page
open("docs/stress.html", "w", encoding="utf-8").write(page)
print("wrote docs/stress.html", len(page) // 1024, "KB")
