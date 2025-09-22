from fastapi import FastAPI
from Soil_Engine import soil_recommendation
from Profit_Engine import profitability_recommendation
from Market_Engine import market_recommendation
from Weather_Engine import weather_recommendation_farmer

app = FastAPI()
@app.get("/soil/")
def soil(lat: float, lon: float, crop: str):
    return soil_recommendation(lat, lon, crop)

# 💰 Profitability module
@app.get("/profitability/")
def profitability(lat: float, lon: float, area: float, crop: str):
    return profitability_recommendation(lat, lon, area, crop)

# 🏪 Market module
@app.get("/market/")
def market(commodity: str):
    return market_recommendation(commodity)

# 🌦️ Weather module
@app.get("/weather/")
def weather(lat: float, lon: float, crop: str):
    return weather_recommendation_farmer(lat, lon, crop)

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Farmer DSS API",
        "routes": {
            "/soil/": "Check soil fertility & fertilizer needs (requires crop)",
            "/profitability/": "Check profitability (requires crop & area)",
            "/market/": "Find best mandi (requires commodity)",
            "/weather/": "Get weather advice (requires crop)"
        }
    }
