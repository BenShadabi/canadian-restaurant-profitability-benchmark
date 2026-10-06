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

# ---------- result ----------
failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)} of {len(results)} checks passed")
if failed:
    print("Failed:\n  " + "\n  ".join(failed))
    sys.exit(1)
