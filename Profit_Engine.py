from Soil_Engine import fetch_soilgrids, estimate_npk, classify_npk
from Market_Engine import market_recommendation

CROP_DATA = {
    "rice":    {"yield": 4000, "seed_rate": 80, "seed_cost": 700, "lifespan_years": 1, "establishment_cost_extra": 0},
    "coconut": {"yield": 5500, "seed_rate": 200, "seed_cost": 84.75, "lifespan_years": 30, "establishment_cost_extra": 20000},
    "rubber":  {"yield": 1750, "seed_rate": 460, "seed_cost": 75, "lifespan_years": 25, "establishment_cost_extra": 50000}
}

# ✅ Updated labour costs (Rubber reduced to 1.5L/ha)
LABOUR_COST = {
    "rice": 48000,
    "coconut": 20000,
    "rubber": 150000
}

YIELD_PENALTIES = {
    "rice": {
        "Nitrogen": (0.05, 0.12),     # 5–12% yield drop
        "Phosphorus": (0.03, 0.07),   # 3–7%
        "Potassium": (0.04, 0.08),    # 4–8%
    },
    "coconut": {
        "Nitrogen": (0.04, 0.08),
        "Phosphorus": (0.02, 0.05),
        "Potassium": (0.06, 0.12),
    },
    "rubber": {
        "Nitrogen": (0.03, 0.07),
        "Phosphorus": (0.02, 0.04),
        "Potassium": (0.05, 0.10),
    }
}


def adjust_yield(base_yield, classification, crop):
    factor = 1.0
    penalties = YIELD_PENALTIES[crop.lower()]
    for rec in classification:
        if "LOW" in rec:
            for nutrient, (low_drop, high_drop) in penalties.items():
                if nutrient in rec:
                    factor *= (1 - low_drop)  # use lower bound only
    return base_yield * factor


def amortize_establishment_cost(crop_key, area_ha):
    info = CROP_DATA[crop_key]
    one_time = info["seed_rate"]*info["seed_cost"]*area_ha + info["establishment_cost_extra"]*area_ha
    if info["lifespan_years"] <= 1: return one_time
    return one_time / info["lifespan_years"]


def calculate_profitability(crop, area, classification, price_per_kg):
    key = crop.lower()
    info = CROP_DATA[key]

    # Base and adjusted yield
    base_yield = info["yield"]
    adj_yield = adj_yield = adjust_yield(base_yield, classification, key)

    # Base scenario (ideal soil)
    total_yield_base = base_yield * area
    revenue_base = total_yield_base * price_per_kg
    annual_estab = amortize_establishment_cost(key, area)
    labour = LABOUR_COST[key] * area
    misc_base = 0.05 * revenue_base
    fert_cost_base = 0  # assume no penalty if soil is good
    total_cost_base = annual_estab + fert_cost_base + labour + misc_base
    net_profit_base = revenue_base - total_cost_base

    # Adjusted scenario (actual soil)
    total_yield_adj = adj_yield * area
    revenue_adj = total_yield_adj * price_per_kg
    misc_adj = 0.05 * revenue_adj
    fert_cost_adj = sum([2000 if "Nitrogen LOW" in c else 1500 for c in classification if "LOW" in c])
    total_cost_adj = annual_estab + fert_cost_adj + labour + misc_adj
    net_profit_adj = revenue_adj - total_cost_adj

    # Per hectare values
    net_profit_base_per_ha = net_profit_base / area
    net_profit_adj_per_ha = net_profit_adj / area

    # Break-even (with adjusted yield)
    be_price = total_cost_adj / total_yield_adj if total_yield_adj > 0 else None

    # Profit reduction %
    profit_drop_pct = round(100 * (net_profit_base - net_profit_adj) / net_profit_base, 2) if net_profit_base > 0 else 0.0

    return {
        "crop": crop.capitalize(),
        "ideal_net_profit_per_ha_₹": round(net_profit_base_per_ha, 2),
        "ideal_net_profit_total_₹": round(net_profit_base, 2),
        "actual_net_profit_per_ha_₹": round(net_profit_adj_per_ha, 2),
        "actual_net_profit_total_₹": round(net_profit_adj, 2),
        "break_even_price_₹_per_kg": round(be_price, 2) if be_price else None,
        "profit_reduction_pct": profit_drop_pct
    }

def profitability_recommendation(lat, lon, area, crop):
    soil = fetch_soilgrids(lat, lon)
    npk = estimate_npk(soil)
    classification = classify_npk(npk, crop)

    mandi = market_recommendation(crop)
    if not mandi["best_mandi"]:
        raise ValueError(f"No mandi price available for {crop}")
    price_per_kg = mandi["best_mandi"]["latest_price_₹_per_kg"]


    return calculate_profitability(crop, area, classification, price_per_kg)

