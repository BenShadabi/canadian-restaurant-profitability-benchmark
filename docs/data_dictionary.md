# Data dictionary

## data/industry_trend.csv (Statistics Canada, The Daily, food services and drinking places)
| Column | Meaning | Unit |
|---|---|---|
| year | Calendar year | |
| operating_revenue_bn | Total operating revenue | $ billions |
| operating_expenses_bn | Total operating expenses | $ billions |
| operating_margin | (revenue - expenses) / revenue | share |
| full_service_revenue_bn / limited_service_revenue_bn | Revenue by restaurant type | $ billions |
| full_service_margin / limited_service_margin | Operating margin by type. Blank = not published in the releases | share |
| cogs_share_of_expenses | Cost of goods sold as share of operating expenses | share |
| wages_share_of_expenses | Wages as share of operating expenses | share |
| source | Release the row came from | text |

## data/average_restaurant_2024.csv (ISED Canadian Industry Statistics, NAICS 7225)
Average restaurant, 65,071 businesses, revenue $30k to $5M. All values in dollars per year.
Columns: revenue, cost_of_sales, labour_and_commissions, rent, utilities_and_telecom, amortization_and_depletion, net_profit, bottom_quartile_profit, top_quartile_profit.
"Other expenses" ($130,800) is calculated as revenue minus the listed expenses minus net profit; it is not a published line.

## data/wages_food_services.csv
Average hourly wage, accommodation and food services, dollars per hour (Statistics Canada Table 14-10-0206-01, via ISED), 2020 to 2024.

## data/restaurant_counts_2024.csv (ISED)
Columns: metric, value, unit, source. Business count (65,071) and the share of restaurants that were profitable (57.7%) or lost money (42.3%).

## data/sensitivity_labour_overhead.csv (calculated)
Average restaurant profit in dollars for labour cuts (rows) and overhead cuts (columns). The waste lever is not included. Written by `analysis/build_dashboard.py`.

## data/scenario_cases.csv (calculated)
One row each for before, conservative and headline. Columns: labour_gain, overhead_gain, waste_gain, profit, margin, note. Conservative applies the overhead cut to utilities and telecom only. Written by `analysis/build_scenarios.py`.

## data/lever_per_point.csv (calculated)
Profit gain in dollars from a 1% cut in cost of sales, labour and overhead (utilities plus calculated other expenses).

## data/waste_share_range.csv (calculated)
Profit in the conservative and headline cases for an assumed waste share of 2% to 8% of cost of sales.

## Notes
- ISED = net profit (small restaurants). Statistics Canada = operating profit (whole industry). Do not mix the two.
- 2019 and some 2022 values come from later releases that compare back to those years.
