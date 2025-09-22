import requests

BASE_URL = "http://172.18.65.5:5001/api/v1/ext-data"
WEATHER_URL = f"{BASE_URL}/weather-data"
ALERTS_URL = f"{BASE_URL}/weather-alerts/"

def fetch_weather(lat, lon):
    resp = requests.get(WEATHER_URL, params={"lat": lat, "lon": lon}, timeout=10).json()
    data = resp.get("data", {})
    if not data:
        return None
    avg_temp = (data["maxTemperature"] + data["minTemperature"]) / 2
    return {
        "description": data.get("weatherDescription", "N/A"),
        "avg_temp": avg_temp,
        "rain": data.get("precipitationSum", 0),
        "sunrise": data.get("sunrise"),
        "sunset": data.get("sunset"),
        "annual_rainfall": data.get("annualRainfall")
    }

def fetch_alerts(lat, lon):
    resp = requests.get(ALERTS_URL, params={"lat": lat, "lon": lon}, timeout=10).json()
    return resp.get("data", "No data")

def weather_recommendation_farmer(lat, lon, crop):
    weather = fetch_weather(lat, lon)
    alerts = fetch_alerts(lat, lon)

    if not weather:
        return {"crop": crop.capitalize(), "weather_advice": ["No weather data available"]}

    crop_conditions = {
        "rice": {"temp": (20, 35), "rain_max": 30},
        "coconut": {"temp": (20, 35), "rain_max": 40},
        "rubber": {"temp": (25, 35), "rain_max": 35}
    }

    recs = []
    cond = crop_conditions.get(crop.lower())
    if cond:
        temp = weather["avg_temp"]
        rain = weather["rain"]

        if temp < cond["temp"][0]:
            recs.append(f"Temperature is {temp:.1f}°C, too low for {crop}. Wait before sowing.")
        elif temp > cond["temp"][1]:
            recs.append(f"Temperature is {temp:.1f}°C, too high for {crop}. Provide irrigation or shade if possible.")

        if rain > cond["rain_max"]:
            recs.append(f"Rainfall is {rain:.1f} mm, postpone sowing/harvest to avoid losses.")

    if alerts and alerts != "No alerts":
        recs.append(f"Weather alert issued: {alerts}. Follow official instructions.")

    if not recs:
        recs.append(f"Weather looks good for {crop}. You can continue with normal farm work.")

    return {
        "crop": crop.capitalize(),
        "weather": weather,
        "alerts": alerts,
        "advice": recs
    }
