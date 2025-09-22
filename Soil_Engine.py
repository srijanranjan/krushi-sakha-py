
import requests


def fetch_soilgrids(lat, lon):
    url = f"http://172.18.65.5:5001/api/v1/ext-data/soil-data?lat={lat}&lon={lon}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Request failed: {e}")
        return {}

    if not data or "data" not in data:
        print("Unexpected API response")
        return {}

    d = data["data"]

    soil = {
        "pH": d.get("pH"),
        "OC": d.get("organicCarbon") / 10.0 if d.get("organicCarbon") else 0,
        "CEC": d.get("CEC"),
        "clay": d.get("clayContent") / 10.0 if d.get("clayContent") else 0,
        "BD": d.get("bulkDensity") / 100.0 if d.get("bulkDensity") else 0,
        # If API ever gives nitrogen, scale it the same way
        "N_total_gkg": d.get("nitrogen") / 100.0 if d.get("nitrogen") else 0
    }

    return soil


def estimate_npk(soil):
    N_available = 0.03 * soil.get("N_total_gkg", 0) * 1000
    P_index = (0.4 * soil.get("OC",0) +
               0.6 * max(0, 7 - abs(soil.get("pH",6.5) - 6.5)) +
               0.2 * soil.get("clay",0))
    K_index = (0.7 * soil.get("CEC",0) + 0.3 * soil.get("clay",0))
    return {"N": N_available, "P": P_index, "K": K_index}

def classify_npk(values, crop):
    crop_thresholds = {
        "rice": {"N": (280, 560), "P": (10, 25), "K": (100, 250)},
        "coconut": {"N": (250, 400), "P": (8, 20), "K": (120, 300)},
        "rubber": {"N": (200, 350), "P": (8, 18), "K": (150, 250)},
    }
    thresholds = crop_thresholds[crop.lower()]
    result = []
    for nutrient, value in values.items():
        low, high = thresholds[nutrient]
        low_tolerance = low * 0.92  # 8% below lower bound
        if value < low_tolerance:
            result.append(f"{nutrient} LOW → Apply fertilizer")
        elif value > high:
            result.append(f"{nutrient} HIGH")
        else:
            result.append(f"{nutrient} OPTIMAL")
    return result

def soil_recommendation(lat, lon, crop):
    soil = fetch_soilgrids(lat, lon)
    npk = estimate_npk(soil)
    classification = classify_npk(npk, crop)
    soil_alerts = [c for c in classification if "LOW" in c]
    return {"crop": crop.capitalize(), "soil_alerts": soil_alerts}
