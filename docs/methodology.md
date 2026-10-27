# Methodology, definitions and sources

## Approach
1. Collected published restaurant financials and wage data from Statistics Canada and ISED.
2. Typed each value into CSV files with a source column (`data/`) and into the workbook (blue cells = typed inputs, black = formulas).
3. Checked growth rates against the releases' own statements (for example, 2020 revenue -25.5% vs 2019; 2022 revenue +7.4% vs 2019).
4. Built a scenario that applies labour, overhead and waste cuts to the average restaurant and solves for the cut that would give +35% profit.
5. Rebuilt all charts from the CSVs with `analysis/build_charts.py`, the dashboard with `analysis/build_dashboard.py`, and ran 8 SQL queries (`sql/`) on the same data.
6. Re-checked the 2020 to 2024 figures against the Statistics Canada releases (October 2026). The 2019 limited-service margin could not be confirmed, so it is left blank.
7. Added a conservative case that leaves out the calculated "other expenses" line, a per-1% lever table and a waste-share range (`analysis/build_scenarios.py`).
8. Added `checks.py`, which recomputes every headline number from the CSVs and compares it with the README, the dashboard, the SQL results and the workbook inputs. It runs on every push.

## Definitions
- **Average restaurant:** ISED Canadian Industry Statistics, NAICS 7225 (full-service restaurants and limited-service eating places), 65,071 businesses with revenue $30,000 to $5,000,000, 2024.
- **Net profit margin:** net profit / revenue (ISED).
- **Operating profit margin:** (operating revenue - operating expenses) / operating revenue (Statistics Canada, all food services and drinking places).
- **Other expenses (workbook):** revenue less cost of sales, labour, rent, utilities, amortization and net profit. It is calculated, not published.
- **Limited-service eating places:** counter service and take-out style restaurants (NAICS 7222). **Full-service restaurants:** table service (NAICS 7221).

## Scenario formulas
- Labour saving = labour x cut
- Overhead saving = (utilities + other expenses) x cut
- Waste saving = cost of sales x assumed waste share x reduction
- Cut needed for +35% profit = 0.35 x profit / base cost line
- Conservative case: the same labour and waste cuts, but the overhead cut applies to utilities and telecom only (published line), not to the calculated other expenses
- Profit gain from a 1% cut in a line = line x 0.01
- Waste share range: 2% to 8% of cost of sales (my assumption, not source data)

## Sources
- ISED, Canadian Industry Statistics, NAICS 7225 financial performance: https://ised-isde.canada.ca/app/ixb/cis/performance/rev/7225
- ISED, Accommodation and food services (72), salaries and wages: https://ised-isde.canada.ca/app/ixb/cis/salaries-salaires/72
- Statistics Canada, The Daily, food services and drinking places, December 2025 (2025 sales, monthly survey): https://www150.statcan.gc.ca/n1/daily-quotidien/260225/dq260225d-eng.htm
- Statistics Canada, The Daily, annual 2024: https://www150.statcan.gc.ca/n1/daily-quotidien/260309/dq260309a-eng.htm
- Statistics Canada, The Daily, 2023 financial data: https://www150.statcan.gc.ca/n1/daily-quotidien/250218/dq250218d-eng.htm
- Statistics Canada, 2022 sales surpass pre-pandemic levels: https://www.statcan.gc.ca/o1/en/plus/5832-sales-full-service-restaurants-and-limited-service-eating-places-surpass-pre-pandemic
- Statistics Canada, The Daily, annual 2021: https://www150.statcan.gc.ca/n1/daily-quotidien/230216/dq230216c-eng.htm
- Statistics Canada, The Daily, annual 2020: https://www150.statcan.gc.ca/n1/daily-quotidien/220412/dq220412e-eng.htm

## Known limitations
See the README. In short: segment revenue does not add up to the industry total, 2020 was later revised, averages, different bases between sources, approximations for 2019 and 2022, blank segment margins for 2023 and 2024, and the scenario is a what-if.

## 2025 sales
`data/sales_2025.csv` holds 2025 sales from the monthly Survey of Food Services and Drinking Places. It is not the same measure as the annual operating revenue in `industry_trend.csv`, so the two series are not mixed. The figures were first read from news coverage, then checked against the December 2025 release in The Daily (2026-02-25) on 2026-10-24. No 2025 margins, cost shares or wages were found.

## Sales since 1998
`data/sales_history.csv` holds every full year of the monthly Survey of Food Services and Drinking Places (Table 21-10-0019-01), which starts in January 1998. Each year is the sum of the twelve unadjusted months, so it is close to but not the same as the seasonally adjusted totals in The Daily (2025: $100.2B here, $101.4B there). The average growth rate is the compound rate from 1998 to 2025: (100.19 / 31.91) ^ (1/27) - 1 = 4.3% a year. Figures are in current dollars, so part of the growth is price. I looked for a longer wage series too, but could not download it on 2026-10-26, so the wage chart stays at 2020 to 2024.

## Toronto neighbourhoods (side project)
Separate from the profit analysis above. Sources, all City of Toronto Open Data (open.toronto.ca): Municipal Licensing and Standards business licences (category "Eating or Drinking Establishment"), DineSafe (used only for coordinates), Neighbourhoods and Business Improvement Areas boundaries, and the 2021 Neighbourhood Profiles (population). Snapshot downloaded 2026-10-21.
- **Active** = issued on or before the snapshot and not cancelled. **Live on 2023-01-01** = issued before it and not cancelled before it. A **closure** = a live licence cancelled between 2023-01-01 and 2025-12-31 with no other licence at the same address and unit issued within 90 days of its cancel date.
- **Placing:** the street address (units, punctuation and street-type spelling normalised) is matched to a DineSafe premises; otherwise the postal code's average DineSafe position is used. Unmatched licences are left out. Points are assigned to neighbourhoods and BIAs by point-in-polygon.
- **Limits:** counts only, no profit; cancellations are not always closures; placement is approximate; one licence category only; 2021 population; closure shares are not shown below 50 licences.
- The City's open data is licensed under the Open Government Licence – Toronto (https://open.toronto.ca/open-data-licence/), which allows commercial and derivative use with the attribution used in the page footer. Checked 2026-10-21.
- **Construction check (exploratory).** `analysis/build_toronto_construction.py` compares licences live on 2023-01-01 and placed from a street address (5,936) with City building permits (cleared since 2017 plus active) with an estimated cost of $5M or more, located by City address point. A licence is "exposed" if such a site was under way (issued by 2025-12-31 and not completed before 2023-01-01) within 150 m. The gap in the share of licences that ended is compared within each neighbourhood and pooled with Mantel-Haenszel weights, and the 95% range comes from resampling neighbourhoods 2,000 times. A placebo uses sites finished in 2017 to 2021. It shows association only. Metrolinx transit construction is not in City permits, a permit's completion date is the date the City closed the file, and the exposed and placebo groups overlap.
