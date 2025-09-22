import requests
from datetime import datetime

# Top 10 districts in Kerala (hardcoded for hackathon demo)
TOP_DISTRICTS = [
    "Thrissur", "Palakkad", "Kottayam", "Ernakulam", "Malappuram",
    "Alappuzha", "Kollam", "Kozhikode", "Kannur", "Idukki"
]

API_URL = "http://172.18.65.5:5001/api/v1/ext-data/market-price"


def market_recommendation(commodity: str):
    results = []

    for district in TOP_DISTRICTS:
        try:
            r = requests.get(API_URL, params={"commodity": commodity, "district": district}, timeout=5)
            if r.status_code != 200:
                continue

            data = r.json()
            market_data = data.get("data", [])

            if not market_data:
                continue

            # ✅ Sort by date (latest first)
            for item in market_data:
                item["arrivalDate"] = datetime.strptime(item["arrivalDate"], "%d/%m/%Y")
            market_data.sort(key=lambda x: x["arrivalDate"], reverse=True)

            # ✅ Normalize: price ₹/quintal → ₹/kg
            for item in market_data:
                item["price_₹_per_kg"] = item["price"] / 100.0

            latest = market_data[0]["price_₹_per_kg"]
            oldest = market_data[-1]["price_₹_per_kg"]

            if latest > oldest:
                trend = "Rising"
            elif latest < oldest:
                trend = "Falling"
            else:
                trend = "Neutral"

            percent_change = round(((latest - oldest) / oldest) * 100, 2) if oldest != 0 else 0

            results.append({
                "district": market_data[0]["district"],
                "commodity": commodity,
                "latest_date": market_data[0]["arrivalDate"].strftime("%d/%m/%Y"),
                "latest_price_₹_per_kg": round(latest, 2),
                "trend": f"{trend} ({percent_change}%)"
            })

        except Exception as e:
            print(f"⚠️ Error fetching {commodity} price for {district}: {e}")
            continue

    if not results:
        return {
            "commodity": commodity,
            "best_mandi": None,
            "other_mandis": [],
            "message": f"No price data available for {commodity} right now."
        }

    # ✅ Best mandi = highest latest price
    best = max(results, key=lambda x: x["latest_price_₹_per_kg"])
    others = [r for r in results if r["district"] != best["district"]]

    return {
        "commodity": commodity,
        "best_mandi": best,
        "other_mandis": others
    }
