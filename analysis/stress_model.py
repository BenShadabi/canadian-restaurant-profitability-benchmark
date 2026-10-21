"""Cost-shock model for the average restaurant, shared by build_stress.py and checks.py. docs/stress.html runs the same formulas in JavaScript.
Inputs are changes as fractions (0.05 = +5%). Cost of sales moves with sales volume, labour moves with it only partly (flex), and rent, utilities,
amortization and the calculated other-expenses line are fixed. The base is the ISED 2024 average restaurant in data/average_restaurant_2024.csv.
"""
import pandas as pd


def base(path="data/average_restaurant_2024.csv"):
    a = pd.read_csv(path).set_index("line")["dollars"]
    rev, cos, lab, rent = a["revenue"], a["cost_of_sales"], a["labour_and_commissions"], a["rent"]
    other = rev - cos - lab - rent - a["net_profit"]          # utilities + amortization + calculated other expenses
    return {"rev": rev, "cos": cos, "lab": lab, "rent": rent, "other": other, "profit": a["net_profit"]}


STEPS = ["food", "wage", "rent", "other", "price", "vol"]


def profit(b, food=0, wage=0, rent=0, other=0, price=0, vol=0, flex=0.3):
    rev = b["rev"] * (1 + price) * (1 + vol)
    cos = b["cos"] * (1 + food) * (1 + vol)
    lab = b["lab"] * (1 + wage) * (1 + flex * vol)
    return rev - cos - lab - b["rent"] * (1 + rent) - b["other"] * (1 + other)


def run(b, **p):
    p.setdefault("flex", 0.3)
    prof = profit(b, **p)
    rev = b["rev"] * (1 + p.get("price", 0)) * (1 + p.get("vol", 0))
    vol = p.get("vol", 0)
    cos = b["cos"] * (1 + p.get("food", 0)) * (1 + vol)
    lab = b["lab"] * (1 + p.get("wage", 0)) * (1 + p["flex"] * vol)
    costs = cos + lab + b["rent"] * (1 + p.get("rent", 0)) + b["other"] * (1 + p.get("other", 0))
    price_needed = (b["profit"] + costs) / (b["rev"] * (1 + vol)) - 1      # price rise that restores today's profit at this volume
    # sales change (from today's volume) at which profit is exactly zero, with the other inputs as set but vol = 0 as the starting point
    q = dict(p); q["vol"] = 0
    p0 = profit(b, **q)
    R, C, L = b["rev"] * (1 + p.get("price", 0)), b["cos"] * (1 + p.get("food", 0)), b["lab"] * (1 + p.get("wage", 0))
    slope = R - C - L * p["flex"]
    be_vol = -p0 / slope if slope > 0 else None
    return {"profit": prof, "margin": prof / rev, "revenue": rev, "change": prof - b["profit"], "price_needed": price_needed, "profit_at_today_volume": p0, "be_vol": be_vol}


PRESETS = [
    ("A typical recent year", "Menu prices +2.6% and the Ontario minimum wage +2.3% (both reported figures), with food costs +4% and rent +3% as my assumptions",
     dict(food=0.04, wage=0.023, rent=0.03, other=0.03, price=0.026)),
    ("Minimum wage step only", "Labour costs +2.3% (the October 2025 Ontario step) and nothing else changes",
     dict(wage=0.023)),
    ("Construction outside the door", "Sales fall 20% for the length of the works and costs do not change. The 20% is an illustration, not a measured figure",
     dict(vol=-0.20)),
    ("Everything at once", "Food +8%, wages +5%, rent +5%, other costs +5%, menu prices +3%, sales -5%. An illustrative squeeze, not a forecast",
     dict(food=0.08, wage=0.05, rent=0.05, other=0.05, price=0.03, vol=-0.05)),
]
