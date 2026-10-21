"""Recompute every headline number from the CSV files and check that the README, the dashboard, the SQL results
and the Excel workbook agree with the data. If a number is changed in one place and not the others, this fails.
Run from the repo root:  python checks.py        Exit code 0 means every check passed.
Requires: pandas, openpyxl (pip install -r requirements.txt)
"""
import sys
import pandas as pd
import openpyxl

sys.path.insert(0, "analysis")
import scenario

results = []


def check(name, ok):
    results.append((name, bool(ok)))
    print(("PASS  " if ok else "FAIL  ") + name)


usd = lambda v: f"${v:,.0f}"
read = lambda path: open(path, encoding="utf-8").read()

# ---------- 1. the data itself, recomputed here without using scenario.py ----------
a = pd.read_csv("data/average_restaurant_2024.csv").set_index("line")["dollars"]
ind = pd.read_csv("data/industry_trend.csv").set_index("year")
wag = pd.read_csv("data/wages_food_services.csv").set_index("year")["avg_hourly_wage_cad"]
cnt = pd.read_csv("data/restaurant_counts_2024.csv").set_index("metric")["value"]

rev, cos, lab, util = a["revenue"], a["cost_of_sales"], a["labour_and_commissions"], a["utilities_and_telecom"]
profit, rent, amort = a["net_profit"], a["rent"], a["amortization_and_depletion"]
other = rev - cos - lab - rent - util - amort - profit
g_lab, g_oh, g_waste = lab * 0.10, (util + other) * 0.15, cos * 0.05 * 0.20
g_util = util * 0.15
after, after_cons = profit + g_lab + g_oh + g_waste, profit + g_lab + g_util + g_waste

check("net margin is 2.5%", round(profit / rev * 100, 1) == 2.5)
check("average revenue is $849,200 and profit $21,500", rev == 849200 and profit == 21500)
check("42.3% of restaurants lost money", cnt["loss_making_share"] == 42.3 and round(cnt["profitable_share"] + cnt["loss_making_share"], 1) == 100.0)
check("2024 industry operating margin is 4.1%", ind.loc[2024, "operating_margin"] == 0.041)
check("cost of sales is 44.8% and labour 23.6% of revenue", round(cos / rev * 100, 1) == 44.8 and round(lab / rev * 100, 1) == 23.6)
check("cost of sales and labour take about 68 cents", round((cos + lab) / rev * 100) == 68)
check("rent is 8.4% of revenue", round(rent / rev * 100, 1) == 8.4)
check("calculated other expenses are $130,800", round(other) == 130800)
check("2020 operating margin: full-service 0.3%, limited-service 5.3%", ind.loc[2020, "full_service_margin"] == 0.003 and ind.loc[2020, "limited_service_margin"] == 0.053)
check("2021 limited-service margin is 6.9%", ind.loc[2021, "limited_service_margin"] == 0.069)
ahead = [int(y) for y in ind.index if ind.loc[y, "limited_service_revenue_bn"] > ind.loc[y, "full_service_revenue_bn"]]
check("limited-service revenue ahead in 2020, 2021 and 2024 only", ahead == [2020, 2021, 2024])
check("2024 segment revenue: $44.9B limited vs $44.2B full-service", ind.loc[2024, "limited_service_revenue_bn"] == 44.9 and ind.loc[2024, "full_service_revenue_bn"] == 44.2)
check("segments add to $89.1B against a $99.6B industry total", round(44.9 + 44.2, 1) == 89.1 and ind.loc[2024, "operating_revenue_bn"] == 99.6)
check("wages: $16.78 to $19.48 is +16.1%", wag[2020] == 16.78 and wag[2024] == 19.48 and round((wag[2024] / wag[2020] - 1) * 100, 1) == 16.1)
check("revenue growth 2020 is -25.5% against 2019", round((ind.loc[2020, "operating_revenue_bn"] / ind.loc[2019, "operating_revenue_bn"] - 1) * 100, 1) == -25.5)
check("revenue in 2022 is +7.4% against 2019", round((ind.loc[2022, "operating_revenue_bn"] / ind.loc[2019, "operating_revenue_bn"] - 1) * 100, 1) == 7.4)
check("quartiles: bottom -$13,000, top $90,600", a["bottom_quartile_profit"] == -13000 and a["top_quartile_profit"] == 90600)
check("+35% profit needs $7,525 (about $7,500): 3.8% of labour or 2.0% of cost of sales",
      round(profit * 0.35) == 7525 and round(profit * 0.35 / lab * 100, 1) == 3.8 and round(profit * 0.35 / cos * 100, 1) == 2.0)
check("headline gains: labour $20,020, overhead $22,845, waste $3,804", (round(g_lab), round(g_oh), round(g_waste)) == (20020, 22845, 3804))
check("headline profit $68,169 and margin 8.0%", round(after) == 68169 and round(after / rev * 100, 1) == 8.0)
check("conservative profit $48,549 and margin 5.7%", round(after_cons) == 48549 and round(after_cons / rev * 100, 1) == 5.7)
check("$19,620 of the overhead gain comes from the calculated line", round(other * 0.15) == 19620)
check("1% cut: cost of sales $3,804, labour $2,002, overhead $1,523", (round(cos * 0.01), round(lab * 0.01), round((util + other) * 0.01)) == (3804, 2002, 1523))
w2, w8 = profit + g_lab + g_oh + cos * 0.02 * 0.2, profit + g_lab + g_oh + cos * 0.08 * 0.2
check("waste share 2% to 8% moves headline profit between $65,887 and $70,451", (round(w2), round(w8)) == (65887, 70451))

# ---------- 2. the shared scenario module and the generated CSVs agree with the numbers above ----------
s = scenario.load()
check("analysis/scenario.py matches the numbers recomputed here",
      round(s["headline"]) == round(after) and round(s["conservative"]) == round(after_cons) and round(s["other"]) == round(other))
sens = pd.read_csv("data/sensitivity_labour_overhead.csv").set_index("labour_cut")
check("sensitivity grid: labour -10% and overhead -15% is the headline total less the waste gain",
      round(sens.loc[0.10, "overhead_cut_0.15"]) == round(after - g_waste))
cases = pd.read_csv("data/scenario_cases.csv").set_index("case")
check("data/scenario_cases.csv matches", round(cases.loc["Headline", "profit"]) == 68169 and round(cases.loc["Conservative", "profit"]) == 48549)
pp = pd.read_csv("data/lever_per_point.csv").set_index("line")["profit_gain_per_1pct_cut"]
check("data/lever_per_point.csv matches", list(pp.values) == [3804, 2002, 1523])
wr = pd.read_csv("data/waste_share_range.csv")
check("data/waste_share_range.csv matches", round(wr.profit_headline.min()) == 65887 and round(wr.profit_headline.max()) == 70451)

# ---------- 3. the README and the dashboard say the same thing ----------
readme, dash = read("README.md"), read("docs/dashboard.html")
for label, text in [
    ("2.5% net profit margin", "2.5%"), ("$21,500 on $849,200", "$21,500 on $849,200"), ("42.3% lost money", "42.3%"),
    ("4.1% operating margin", "4.1%"), ("44.8% and 23.6%", "44.8% and 23.6%"), ("rent 8.4%", "8.4%"),
    ("2020 margins 0.3% and 5.3%", "0.3% while limited-service places earned 5.3%"), ("$44.9B vs $44.2B", "$44.9B vs $44.2B"),
    ("wages $16.78 to $19.48, 16.1%", "$16.78 (2020) to $19.48 (2024), up 16.1%"), ("$7,500, 3.8%, 2.0%", "3.8% labour cut"),
    ("labour gain", usd(g_lab)), ("overhead gain", usd(g_oh)), ("waste gain", usd(g_waste)),
    ("headline total", "$21,500 to $68,169 (margin 2.5% to 8.0%)"), ("conservative total", "$21,500 to $48,549 (margin 2.5% to 5.7%)"),
    ("calculated line share", usd(other * 0.15)), ("waste range low", usd(w2)), ("waste range high", usd(w8)),
    ("1% cost of sales", usd(cos * 0.01)), ("1% labour", usd(lab * 0.01)),
    ("bottom quartile loss", "$13,000"), ("top quartile profit", "$90,600"),
]:
    check(f"README states {label}", text in readme)
for label, text in [
    ("headline profit", usd(after)), ("starting profit", usd(profit)), ("conservative profit", usd(after_cons)),
    ("labour gain", usd(g_lab)), ("overhead gain", usd(g_oh)), ("waste gain", usd(g_waste)),
    ("2.5% net margin", "2.5%"), ("42.3% lost money", "42.3%"), ("1% cost of sales", usd(cos * 0.01)),
    ("wage change", "16.1%"), ("waste range low", usd(w2)), ("waste range high", usd(w8)),
]:
    check(f"docs/dashboard.html shows {label}", text in dash)
page = read("docs/index.html")
for label, text in [("2.5%", "2.5%"), ("42.3%", "42.3%"), ("revenue and profit", "$21,500 on $849,200"), ("headline profit", usd(after)),
                    ("conservative profit", usd(after_cons)), ("conservative margin", "5.7%"), ("calculated line", usd(other)),
                    ("bottom quartile", "$13,000"), ("top quartile", "$90,600"), ("labour gain", usd(g_lab)), ("overhead gain", usd(g_oh)), ("waste gain", usd(g_waste)),
                    ("1% cost of sales", usd(cos * 0.01)), ("1% labour", usd(lab * 0.01)), ("1% overhead", usd((util + other) * 0.01))]:
    check(f"docs/index.html shows {label}", text in page)
n_sql = len([q for q in open("sql/queries.sql", encoding="utf-8").read().split(";") if "SELECT" in q])
check("README and project page say how many SQL queries there are", f"{n_sql} SQL queries" in readme and "Eight SQL queries" in page and n_sql == 8)
check("no em dashes in README, project page, dashboard or docs", not any("\u2014" in read(f) for f in ["README.md", "docs/index.html", "docs/dashboard.html", "docs/methodology.md", "docs/data_dictionary.md"]))
import struct
png = open("assets/banner.png", "rb").read(24)
check("assets/banner.png is 1280x640", png[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", png[16:24]) == (1280, 640))
sql_out = read("sql/results.md")
check("sql/results.md has the headline and conservative totals", "68169" in sql_out and "48549" in sql_out and "130800" in sql_out)

# ---------- 4. the Excel workbook inputs match the CSVs ----------
wb = openpyxl.load_workbook("data/Canadian_Restaurant_Benchmark.xlsx")  # formulas are not evaluated; typed inputs are compared
bm, sc, wg, it = wb["Benchmark"], wb["Scenario"], wb["Wages"], wb["Industry_Trend"]
check("workbook Benchmark inputs equal the CSV",
      [bm[c].value for c in ("B5", "B6", "B7", "B8", "B9", "B10", "B12", "B17", "B19")] == [rev, cos, lab, rent, util, amort, profit, a["bottom_quartile_profit"], a["top_quartile_profit"]])
check("workbook Wages equal the CSV", [wg[f"B{r}"].value for r in range(5, 10)] == [wag[y] for y in range(2020, 2025)])
cols = {"B": "operating_revenue_bn", "C": "operating_expenses_bn", "D": "operating_margin", "E": "full_service_revenue_bn",
        "F": "limited_service_revenue_bn", "G": "full_service_margin", "H": "limited_service_margin",
        "I": "cogs_share_of_expenses", "J": "wages_share_of_expenses"}
bad = []
for r, y in zip(range(5, 11), range(2019, 2025)):
    for col, name in cols.items():
        want, got = ind.loc[y, name], it[f"{col}{r}"].value
        if (pd.isna(want) and got is not None) or (not pd.isna(want) and got != want):
            bad.append(f"{col}{r}")
check("workbook Industry_Trend equals the CSV" + (f" (differs: {', '.join(bad)})" if bad else ""), not bad)
check("workbook Scenario inputs are 10%, 15%, 5% and 20%", [sc[c].value for c in ("B5", "B6", "B7", "B8")] == [0.10, 0.15, 0.05, 0.20])
check("workbook has the conservative case formulas", sc["C28"].value == "=Benchmark!B9*B28" and sc["C30"].value == "=C11+C29")

# ---------- 5. 2025 sales and the calculator page ----------
s25 = pd.read_csv("data/sales_2025.csv").set_index("segment")
tot, ls, fs = s25.loc["Food services and drinking places (total)"], s25.loc["Limited-service eating places"], s25.loc["Full-service restaurants"]
check("2025 sales: $101.4B total (+5.6%), limited-service $47.3B, full-service $43.6B",
      (tot.sales_2025_bn, tot.change_vs_2024_pct, ls.sales_2025_bn, fs.sales_2025_bn) == (101.4, 5.6, 47.3, 43.6))
check("limited-service stayed ahead of full-service in 2025", ls.sales_2025_bn > fs.sales_2025_bn)
for label, text in [("total", "$101.4B"), ("limited-service", "$47.3B"), ("full-service", "$43.6B")]:
    check(f"README and project page state 2025 {label} sales", text in readme and text in page)
calc = read("docs/calculator.html")
check("calculator benchmark inputs equal the CSV",
      f"rev:{rev}, cos:{cos}, lab:{lab}, rent:{rent}, util:{util}, amort:{amort}, profit:{profit}" in calc)
check("calculator text states the benchmark shares",
      all(t in calc for t in ["44.8%", "23.6%", "8.4%", "2.5%", "2.7%", "15.4%", "65,071", "42.3%"]))
check("dashboard shows the 2025 sales card", all(t in dash for t in ["$101.4B", "$47.3B", "$43.6B", "$44.7B", "$41.2B"]))
check("README embeds the 2025 chart and the calculator picture", "assets/sales_2025.png" in readme and "assets/calculator.png" in readme)
check("no em dashes in the calculator", "\u2014" not in calc)
check("project page and README link the calculator", "calculator.html" in page and "calculator.html" in readme)

# ---------- 6. Toronto side project (counts of licences, kept separate from the profit numbers above) ----------
tn = pd.read_csv("data/toronto_neighbourhoods.csv", dtype={"area_code": str})
tb = pd.read_csv("data/toronto_bia.csv")
tm = pd.read_csv("data/toronto_match_summary.csv").set_index("item")["count"]
check("Toronto: 158 neighbourhoods and 86 BIAs", len(tn) == 158 and len(tb) == 86 and tn.area_code.is_unique)
check("Toronto: placement counts add up to the licences in scope", tm["address_match"] + tm["postal_code_centre"] + tm["not_placed"] == tm["licences_in_scope"])
check("Toronto: nothing placed outside the neighbourhood boundaries", tm["outside_neighbourhoods"] == 0)
check("Toronto: neighbourhood active licences equal the placed active licences", tn.active_licences.sum() <= tm["active_total_all_toronto"] and tn.active_licences.sum() >= 0.95 * tm["active_total_all_toronto"])
check("Toronto: exits and live counts are consistent (exits <= live, rate = exits / live)",
      (tn.exits_2023_2025 <= tn.live_at_2023_01_01).all() and (tn.exits_2023_2025.sum() == tm["exits_2023_2025"])
      and ((tn.exits_2023_2025 / tn.live_at_2023_01_01.where(tn.live_at_2023_01_01 > 0)).round(4).fillna(0) == tn.exit_rate_3yr.fillna(0)).all())
check("Toronto: removing re-issued addresses lowers the cancellation count", tm["exits_2023_2025"] < tm["raw_cancellations_2023_2025"])
check("Toronto: per 1,000 residents is recomputed from the counts", ((tn.active_licences / tn.population_2021 * 1000).round(2) == tn.per_1000_residents).all())
check("Toronto: closure shares are flagged as low sample below 50 licences", (tn.low_sample == (tn.live_at_2023_01_01 < 50)).all() and (tb.low_sample == (tb.live_at_2023_01_01 < 50)).all())
tor = read("docs/toronto.html")
tcity = tn.active_licences.sum() / tn.population_2021.sum() * 1000
check("Toronto page shows the placed total, city density and closure share",
      f"{int(tn.active_licences.sum()):,}" in tor and f"{tcity:.1f}" in tor and f"{tn.exits_2023_2025.sum() / tn.live_at_2023_01_01.sum():.1%}" in tor)
check("Toronto page says it is not profit and lists its limits", "not profit" in tor.lower() and ">Limits</h2>" in tor and "Not profit." in tor)
check("Toronto page, README and project page link each other", "toronto.html" in readme and "toronto.html" in page and "index.html" in tor)
check("no em dashes on the Toronto page", "\u2014" not in tor)
check("the national profit numbers do not use Toronto data", "toronto" not in open("analysis/scenario.py", encoding="utf-8").read().lower())

# ---------- 7. shared design files ----------
import os
check("shared motion.css and motion.js exist and every page loads them",
      os.path.exists("docs/motion.css") and os.path.exists("docs/motion.js") and all("motion.js" in read(f"docs/{p}.html") for p in ("index", "dashboard", "calculator", "toronto")))
check("no em dashes in motion.css or motion.js", "\u2014" not in read("docs/motion.css") + read("docs/motion.js"))
check("Toronto page credits the Open Government Licence - Toronto", "Open Government Licence" in tor and "open.toronto.ca/open-data-licence" in tor)

# ---------- 8. stress test page: recompute the preset table here without analysis/stress_model.py ----------
stress = read("docs/stress.html")
def shock(food=0, wage=0, rent_=0, other_=0, price=0, vol=0, flex=0.3):
    other_base = rev - cos - lab - rent - profit
    r = rev * (1 + price) * (1 + vol)
    costs = cos * (1 + food) * (1 + vol) + lab * (1 + wage) * (1 + flex * vol) + rent * (1 + rent_) + other_base * (1 + other_)
    p0 = rev * (1 + price) - cos * (1 + food) - lab * (1 + wage) - rent * (1 + rent_) - other_base * (1 + other_)
    slope = rev * (1 + price) - cos * (1 + food) - lab * (1 + wage) * flex
    return r - costs, (r - costs) / r, (profit + costs) / (rev * (1 + vol)) - 1, -p0 / slope
dm = lambda v: ("-$" if v < 0 else "$") + f"{abs(v):,.0f}"
cases = [dict(food=0.04, wage=0.023, rent_=0.03, other_=0.03, price=0.026), dict(wage=0.023), dict(vol=-0.20),
         dict(food=0.08, wage=0.05, rent_=0.05, other_=0.05, price=0.03, vol=-0.05)]
ok = True
for cs in cases:
    pr, mg, pn, bv = shock(**cs)
    ok = ok and dm(pr) in stress and f"{mg:.1%}" in stress and f"{pn:+.1%}" in stress and f"{bv:+.1%}" in stress
check("stress page preset table matches an independent recomputation", ok)
check("stress page: construction preset (sales -20%) turns $21,500 into -$60,248", round(shock(vol=-0.20)[0]) == -60248)
check("stress page: baseline cushion is a 5.3% fall in sales", round(-shock()[3] * 100, 1) == 5.3 and "5.3%" in stress)
check("stress page says it is a what-if and lists what was reported", "not a forecast" in stress and "What has actually been reported" in stress and "stress.html" in read("docs/motion.js"))
check("stress page, README link each other and the nav", "stress.html" in readme and "index.html" in stress)

# ---------- 9. construction and closures (exploratory) ----------
cx = pd.read_csv("data/toronto_construction.csv")
check("construction file: rates equal exits / licences and 95% ranges contain the estimate",
      ((cx.exits_exposed / cx.licences_exposed).round(4) == cx.rate_exposed).all() and ((cx.exits_unexposed / cx.licences_unexposed).round(4) == cx.rate_unexposed).all()
      and ((cx.ci_low <= cx.adjusted_difference) & (cx.adjusted_difference <= cx.ci_high)).all())
check("construction file: main comparison uses all 5,936 licences and has a placebo row",
      int(cx.iloc[0].licences_exposed + cx.iloc[0].licences_unexposed) == 5936 and cx.analysis.str.startswith("Placebo").any())
plc_row = cx[cx.analysis.str.startswith("Placebo")].iloc[0]
check("placebo gap is at least as large as the main gap, so the page must not claim construction caused closures",
      plc_row.adjusted_difference >= cx.iloc[0].adjusted_difference and "cannot show" in tor.lower() and "That construction caused closures" in tor)
check("Toronto page shows the construction numbers", f"{cx.iloc[0].rate_exposed:.1%}" in tor and f"{cx.iloc[0].rate_unexposed:.1%}" in tor and f"{cx.iloc[0].adjusted_difference * 100:+.1f}" in tor)
check("Toronto page says Metrolinx transit works are not covered", "Metrolinx" in tor and "not in City building permits" in tor)

# ---------- result ----------
failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)} of {len(results)} checks passed")
if failed:
    print("Failed:\n  " + "\n  ".join(failed))
    sys.exit(1)
