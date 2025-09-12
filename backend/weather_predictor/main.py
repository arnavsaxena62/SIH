from datetime import datetime, timedelta
import pytz
import json
from weather import get_hourly_forecast

LOCAL_TZ = pytz.timezone("Asia/Kolkata")

def analyze_forecast(forecast, slots: int = 24):
    now = datetime.now(LOCAL_TZ)
    hourly = forecast.hourly

    # Find the starting index from "now"
    start_idx = 0
    for i, point in enumerate(hourly):
        point_time = datetime.fromisoformat(point.time)
        if point_time.tzinfo is None:
            point_time = pytz.UTC.localize(point_time).astimezone(LOCAL_TZ)
        if point_time >= now:
            start_idx = i
            break

    selected = hourly[start_idx:start_idx + slots]

    # Collect stats for alerts
    total_rain = sum(p.precipitation_mm for p in selected)
    max_wind = max(p.windspeed_ms for p in selected)
    max_gust = max((p.windgust_ms for p in selected if p.windgust_ms is not None), default=0)

    alerts = []

    # Rain/flood alerts
    if total_rain >= 50:
        alerts.append({"type": "flood", "level": "high", "message": f"High flood risk: {total_rain:.1f} mm rain expected in {slots}h"})
    elif total_rain >= 30:
        alerts.append({"type": "flood", "level": "moderate", "message": f"Moderate flood risk: {total_rain:.1f} mm rain expected"})
    else:
        alerts.append({"type": "flood", "level": "low", "message": "Low flood risk"})

    # Wind alerts
    if max_gust >= 25 or max_wind >= 20:
        alerts.append({"type": "wind", "level": "storm", "message": f"Storm warning: Winds up to {max_gust:.1f} km/hr"})
    elif max_gust >= 15:
        alerts.append({"type": "wind", "level": "strong", "message": f"Strong winds: Gusts up to {max_gust:.1f} km/hr"})
    else:
        alerts.append({"type": "wind", "level": "normal", "message": "No severe wind expected"})

    # All-clear if both rain and wind are low
    if total_rain <= 5 and max_wind <= 15:
        alerts.append({"type": "general", "level": "safe", "message": "All clear: No major risks detected."})

    return alerts


def main():
    city = input("Enter city name (default = Kochi): ").strip() or "Kochi"
    slots = input("Enter hours to check (default = 24): ").strip()
    slots = int(slots) if slots.isdigit() else 24

    forecast = get_hourly_forecast(city, slots)
    if forecast:
        alerts = analyze_forecast(forecast, slots)
        print(json.dumps({"city": city, "alerts": alerts}, indent=4))
    else:
        print(json.dumps({"error": f"Could not fetch forecast for {city}"}))


if __name__ == "__main__":
    main()
