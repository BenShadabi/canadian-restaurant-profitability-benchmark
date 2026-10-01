# Methodology, definitions and sources

## Approach
1. Collected published restaurant financials and wage data from Statistics Canada and ISED.
2. Typed each value into CSV files with a source column (`data/`) and into the workbook (blue cells = typed inputs, black = formulas).
3. Checked growth rates against the releases' own statements (for example, 2020 revenue -25.5% vs 2019; 2022 revenue +7.4% vs 2019).
4. Built a scenario that applies labour, overhead and waste cuts to the average restaurant and solves for the cut that would give +35% profit.
5. Rebuilt all charts from the CSVs with `analysis/build_charts.py`.

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

## Sources
- ISED, Canadian Industry Statistics, NAICS 7225 financial performance: https://ised-isde.canada.ca/app/ixb/cis/performance/rev/7225
- ISED, Accommodation and food services (72), salaries and wages: https://ised-isde.canada.ca/app/ixb/cis/salaries-salaires/72
- Statistics Canada, The Daily, annual 2024: https://www150.statcan.gc.ca/n1/daily-quotidien/260309/dq260309a-eng.htm
- Statistics Canada, The Daily, 2023 financial data: https://www150.statcan.gc.ca/n1/daily-quotidien/250218/dq250218d-eng.htm
- Statistics Canada, 2022 sales surpass pre-pandemic levels: https://www.statcan.gc.ca/o1/en/plus/5832-sales-full-service-restaurants-and-limited-service-eating-places-surpass-pre-pandemic
- Statistics Canada, The Daily, annual 2021: https://www150.statcan.gc.ca/n1/daily-quotidien/230216/dq230216c-eng.htm
- Statistics Canada, The Daily, annual 2020: https://www150.statcan.gc.ca/n1/daily-quotidien/220412/dq220412e-eng.htm

## Known limitations
See the README. In short: averages, different bases between sources, approximations for 2019 and 2022, blank segment margins for 2023 and 2024, and the scenario is a what-if.
