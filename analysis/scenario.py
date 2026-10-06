"""Scenario maths for the average restaurant, read straight from the CSV files in data/.
Used by build_scenarios.py, build_dashboard.py and checks.py. Run those from the repo root.

Two cases are calculated:
  headline      labour -10%, overhead -15% (utilities + the calculated "other expenses" line), waste -20%
  conservative  the same cuts, but overhead is only the published utilities and telecom line
The calculated "other expenses" line is revenue minus every listed cost and profit. It is not a published figure,
so the conservative case leaves it out.
"""
import pandas as pd

LAB_CUT, OH_CUT, WASTE_SHARE, WASTE_CUT = 0.10, 0.15, 0.05, 0.20
WASTE_SHARES = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]  # range tested for the assumed waste share


def load(path="data/average_restaurant_2024.csv"):
    a = pd.read_csv(path).set_index("line")["dollars"]
    rev, cos, lab = a["revenue"], a["cost_of_sales"], a["labour_and_commissions"]
    util, rent, amort, profit = a["utilities_and_telecom"], a["rent"], a["amortization_and_depletion"], a["net_profit"]
    other = rev - cos - lab - rent - util - amort - profit

    gain_lab = lab * LAB_CUT
    gain_oh = (util + other) * OH_CUT          # headline: includes the calculated remainder
    gain_util = util * OH_CUT                   # conservative: published utilities line only
    gain_waste = cos * WASTE_SHARE * WASTE_CUT

    headline = profit + gain_lab + gain_oh + gain_waste
    conservative = profit + gain_lab + gain_util + gain_waste

    per_point = {  # profit gain from a 1% cut in each line
        "Cost of sales": cos * 0.01,
        "Labour": lab * 0.01,
        "Overhead (utilities + calculated other)": (util + other) * 0.01,
    }
    waste_range = []
    for s in WASTE_SHARES:
        g = cos * s * WASTE_CUT
        waste_range.append({"waste_share": s, "waste_gain": g,
                            "profit_conservative": profit + gain_lab + gain_util + g,
                            "profit_headline": profit + gain_lab + gain_oh + g})
    return {
        "rev": rev, "cos": cos, "lab": lab, "util": util, "rent": rent, "amort": amort, "profit": profit, "other": other,
        "gain_lab": gain_lab, "gain_oh": gain_oh, "gain_util": gain_util, "gain_waste": gain_waste,
        "headline": headline, "conservative": conservative,
        "margin_before": profit / rev, "margin_headline": headline / rev, "margin_conservative": conservative / rev,
        "overhead_residual_gain": other * OH_CUT,    # the part of the headline overhead gain that comes from the calculated line
        "per_point": per_point, "waste_range": waste_range,
    }
