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
`data/sales_2025.csv` holds 2025 sales from the monthly Survey of Food Services and Drinking Places. It is not the same measure as the annual operating revenue in `industry_trend.csv`, so the two series are not mixed. The figures were read from the December 2025 release as reported by Retail Insider while statcan.gc.ca was unavailable, and should be re-checked against The Daily. No 2025 margins, cost shares or wages were found.

## Toronto neighbourhoods (side project)
Separate from the profit analysis above. Sources, all City of Toronto Open Data (open.toronto.ca): Municipal Licensing and Standards business licences (category "Eating or Drinking Establishment"), DineSafe (used only for coordinates), Neighbourhoods and Business Improvement Areas boundaries, and the 2021 Neighbourhood Profiles (population). Snapshot downloaded 2026-10-21.
- **Active** = issued on or before the snapshot and not cancelled. **Live on 2023-01-01** = issued before it and not cancelled before it. A **closure** = a live licence cancelled between 2023-01-01 and 2025-12-31 with no other licence at the same address and unit issued within 90 days of its cancel date.
- **Placing:** the street address (units, punctuation and street-type spelling normalised) is matched to a DineSafe premises; otherwise the postal code's average DineSafe position is used. Unmatched licences are left out. Points are assigned to neighbourhoods and BIAs by point-in-polygon.
- **Limits:** counts only, no profit; cancellations are not always closures; placement is approximate; one licence category only; 2021 population; closure shares are not shown below 50 licences.
- The City's open data terms are assumed to be the Open Government Licence - Toronto; confirm on the portal before reuse.
