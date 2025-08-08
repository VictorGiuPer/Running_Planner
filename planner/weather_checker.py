# planner/weather.py
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
OPEN_WEATHER_KEY = os.getenv("OPEN_WEATHER_KEY")

def fetch_hourly_forecast(lat, lon):
    """Fetch 5-day / 3-hour forecast from OpenWeatherMap."""
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPEN_WEATHER_KEY,
        "units": "metric"
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def extract_day_forecast(data, target_date):
    """Filter hourly forecast for a given date."""
    forecasts = []
    for entry in data["list"]:
        dt = datetime.fromtimestamp(entry["dt"])
        if dt.date() == target_date:
            forecasts.append({
                "time": dt.strftime("%H:%M"),
                "temp": entry["main"]["temp"],
                "feels_like": entry["main"]["feels_like"],
                "wind": entry["wind"]["speed"],
                "rain_prob": entry.get("pop", 0) * 100
            })
    return forecasts
