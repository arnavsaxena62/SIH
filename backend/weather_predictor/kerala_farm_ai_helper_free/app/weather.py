from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import requests

KERALA_CITIES = {
    "kochi": {"lat": 9.9312, "lon": 76.2673},
    "thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366},
    "thrissur": {"lat": 10.5276, "lon": 76.2144},
    "kottayam": {"lat": 9.5916, "lon": 76.5225},
    "alappuzha": {"lat": 9.4981, "lon": 76.3388},
    "ernakulam": {"lat": 9.9816, "lon": 76.2999},
    "kannur": {"lat": 11.8745, "lon": 75.3704},
    "kozhikode": {"lat": 11.2588, "lon": 75.7804},
    "kollam": {"lat": 8.8932, "lon": 76.6141},
    "kasaragod": {"lat": 12.5007, "lon": 74.9860},
}

BASE_URL = "https://api.open-meteo.com/v1/forecast"

@dataclass
class HourPoint:
    time: str
    temp_c: float
    precipitation_mm: float
    humidity: Optional[float]
    windspeed_ms: float
    windgust_ms: Optional[float]

@dataclass
class Forecast:
    latitude: float
    longitude: float
    timezone: str
    hourly: List[HourPoint]

def _choose_location(city: Optional[str], lat: Optional[float], lon: Optional[float]) -> Dict[str, float]:
    if lat is not None and lon is not None:
        return {"lat": float(lat), "lon": float(lon)}
    if city:
        key = city.strip().lower()
        if key in KERALA_CITIES:
            return KERALA_CITIES[key]
    return KERALA_CITIES["kochi"]

def get_hourly_forecast(city: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None, days: int = 3) -> Forecast:
    loc = _choose_location(city, lat, lon)
    params: Dict[str, Any] = {
        "latitude": loc["lat"],
        "longitude": loc["lon"],
        "hourly": "temperature_2m,precipitation,relativehumidity_2m,windspeed_10m,windgusts_10m",
        "forecast_days": days,
        "timezone": "auto",
    }
    resp = requests.get(BASE_URL, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    tz = data.get("timezone", "UTC")
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    precs = hourly.get("precipitation", [])
    hums = hourly.get("relativehumidity_2m", [])
    winds = hourly.get("windspeed_10m", [])
    gusts = hourly.get("windgusts_10m", [])

    points: List[HourPoint] = []
    n = len(times)
    for i in range(n):
        points.append(HourPoint(
            time=times[i],
            temp_c=float(temps[i]) if i < len(temps) else None,
            precipitation_mm=float(precs[i]) if i < len(precs) else 0.0,
            humidity=(float(hums[i]) if i < len(hums) else None),
            windspeed_ms=float(winds[i]) if i < len(winds) else 0.0,
            windgust_ms=(float(gusts[i]) if i < len(gusts) else None),
        ))

    return Forecast(latitude=loc["lat"], longitude=loc["lon"], timezone=tz, hourly=points)
