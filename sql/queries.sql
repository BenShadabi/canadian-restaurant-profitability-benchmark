-- Queries on the project CSVs, loaded into SQLite by sql/run_queries.py.
-- Tables: industry_trend, average_restaurant, wages, restaurant_counts

-- 1. Revenue growth and margin by year (window function)
SELECT year,
       operating_revenue_bn AS revenue_bn,
       ROUND((operating_revenue_bn / LAG(operating_revenue_bn) OVER (ORDER BY year) - 1) * 100, 1) AS growth_pct,
       ROUND(operating_margin * 100, 1) AS operating_margin_pct
FROM industry_trend ORDER BY year;

-- 2. Which segment had the higher margin each year? (rows with both margins published)
SELECT year,
       ROUND(full_service_margin * 100, 1) AS full_service_pct,
       ROUND(limited_service_margin * 100, 1) AS limited_service_pct,
       CASE WHEN limited_service_margin > full_service_margin THEN 'limited-service'
            ELSE 'full-service' END AS higher_margin
FROM industry_trend
WHERE full_service_margin IS NOT NULL AND limited_service_margin IS NOT NULL ORDER BY year;

-- 3. Cost structure of the average restaurant, with the calculated "other expenses" line
WITH a AS (
  SELECT MAX(CASE WHEN line='revenue' THEN dollars END) AS revenue,
         MAX(CASE WHEN line='cost_of_sales' THEN dollars END) AS cost_of_sales,
         MAX(CASE WHEN line='labour_and_commissions' THEN dollars END) AS labour,
         MAX(CASE WHEN line='rent' THEN dollars END) AS rent,
         MAX(CASE WHEN line='utilities_and_telecom' THEN dollars END) AS utilities,
         MAX(CASE WHEN line='amortization_and_depletion' THEN dollars END) AS amortization,
         MAX(CASE WHEN line='net_profit' THEN dollars END) AS net_profit
  FROM average_restaurant)
SELECT 'Cost of sales' AS line, cost_of_sales AS dollars, ROUND(cost_of_sales * 100.0 / revenue, 1) AS pct_of_revenue FROM a
UNION ALL SELECT 'Labour', labour, ROUND(labour * 100.0 / revenue, 1) FROM a
UNION ALL SELECT 'Other expenses (calculated)', revenue - cost_of_sales - labour - rent - utilities - amortization - net_profit,
       ROUND((revenue - cost_of_sales - labour - rent - utilities - amortization - net_profit) * 100.0 / revenue, 1) FROM a
UNION ALL SELECT 'Rent', rent, ROUND(rent * 100.0 / revenue, 1) FROM a
UNION ALL SELECT 'Amortization', amortization, ROUND(amortization * 100.0 / revenue, 1) FROM a
UNION ALL SELECT 'Utilities and telecom', utilities, ROUND(utilities * 100.0 / revenue, 1) FROM a
UNION ALL SELECT 'Net profit', net_profit, ROUND(net_profit * 100.0 / revenue, 1) FROM a;

-- 4. What-if: labour -10%, overhead -15%, waste -20% of an assumed 5% waste share of cost of sales
WITH a AS (
  SELECT MAX(CASE WHEN line='revenue' THEN dollars END) AS revenue,
         MAX(CASE WHEN line='cost_of_sales' THEN dollars END) AS cos,
         MAX(CASE WHEN line='labour_and_commissions' THEN dollars END) AS labour,
         MAX(CASE WHEN line='rent' THEN dollars END) AS rent,
         MAX(CASE WHEN line='utilities_and_telecom' THEN dollars END) AS util,
         MAX(CASE WHEN line='amortization_and_depletion' THEN dollars END) AS amort,
         MAX(CASE WHEN line='net_profit' THEN dollars END) AS profit
  FROM average_restaurant),
g AS (SELECT *, revenue - cos - labour - rent - util - amort - profit AS other FROM a)
SELECT profit AS profit_before,
       labour * 0.10 AS labour_gain,
       (util + other) * 0.15 AS overhead_gain,
       cos * 0.05 * 0.20 AS waste_gain,
       profit + labour * 0.10 + (util + other) * 0.15 + cos * 0.05 * 0.20 AS profit_after,
       ROUND(profit * 100.0 / revenue, 1) AS margin_before_pct,
       ROUND((profit + labour * 0.10 + (util + other) * 0.15 + cos * 0.05 * 0.20) * 100.0 / revenue, 1) AS margin_after_pct
FROM g;

-- 5. Wage growth year over year and since 2020
SELECT year, avg_hourly_wage_cad AS wage,
       ROUND((avg_hourly_wage_cad / LAG(avg_hourly_wage_cad) OVER (ORDER BY year) - 1) * 100, 1) AS yoy_pct,
       ROUND((avg_hourly_wage_cad / FIRST_VALUE(avg_hourly_wage_cad) OVER (ORDER BY year) - 1) * 100, 1) AS since_2020_pct
FROM wages ORDER BY year;

-- 6. Spread between top and bottom quartile profit
SELECT MAX(CASE WHEN line='bottom_quartile_profit' THEN dollars END) AS bottom_quartile,
       MAX(CASE WHEN line='net_profit' THEN dollars END) AS average,
       MAX(CASE WHEN line='top_quartile_profit' THEN dollars END) AS top_quartile,
       MAX(CASE WHEN line='top_quartile_profit' THEN dollars END) - MAX(CASE WHEN line='bottom_quartile_profit' THEN dollars END) AS spread
FROM average_restaurant;

-- 7. Conservative case: same cuts, but overhead is only the published utilities line
WITH a AS (
  SELECT MAX(CASE WHEN line='revenue' THEN dollars END) AS revenue,
         MAX(CASE WHEN line='cost_of_sales' THEN dollars END) AS cos,
         MAX(CASE WHEN line='labour_and_commissions' THEN dollars END) AS labour,
         MAX(CASE WHEN line='utilities_and_telecom' THEN dollars END) AS util,
         MAX(CASE WHEN line='net_profit' THEN dollars END) AS profit
  FROM average_restaurant)
SELECT profit AS profit_before,
       labour * 0.10 AS labour_gain,
       util * 0.15 AS utilities_gain,
       cos * 0.05 * 0.20 AS waste_gain,
       profit + labour * 0.10 + util * 0.15 + cos * 0.05 * 0.20 AS profit_after,
       ROUND(profit * 100.0 / revenue, 1) AS margin_before_pct,
       ROUND((profit + labour * 0.10 + util * 0.15 + cos * 0.05 * 0.20) * 100.0 / revenue, 1) AS margin_after_pct
FROM a;

-- 8. Profit gain from a 1% cut in each cost line
WITH a AS (
  SELECT MAX(CASE WHEN line='revenue' THEN dollars END) AS revenue,
         MAX(CASE WHEN line='cost_of_sales' THEN dollars END) AS cos,
         MAX(CASE WHEN line='labour_and_commissions' THEN dollars END) AS labour,
         MAX(CASE WHEN line='rent' THEN dollars END) AS rent,
         MAX(CASE WHEN line='utilities_and_telecom' THEN dollars END) AS util,
         MAX(CASE WHEN line='amortization_and_depletion' THEN dollars END) AS amort,
         MAX(CASE WHEN line='net_profit' THEN dollars END) AS profit
  FROM average_restaurant),
g AS (SELECT *, revenue - cos - labour - rent - util - amort - profit AS other FROM a)
SELECT 'Cost of sales' AS line, ROUND(cos * 0.01) AS gain_per_1pct_cut FROM g
UNION ALL SELECT 'Labour', ROUND(labour * 0.01) FROM g
UNION ALL SELECT 'Overhead (utilities + calculated other)', ROUND((util + other) * 0.01) FROM g
ORDER BY gain_per_1pct_cut DESC;
