# Recommendations with flood & calamity predictor (weather only)
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from .weather import Forecast, HourPoint

@dataclass
class Advice:
    title: str
    details: str
    severity: str = "info"

def _sum_precip(hours: List[HourPoint], hours_window: int) -> float:
    total = 0.0
    for i, h in enumerate(hours):
        if i >= hours_window:
            break
        total += (h.precipitation_mm or 0.0)
    return total

def recommend_precautions(forecast: Forecast) -> List[Advice]:
    adv: List[Advice] = []
    hours = forecast.hourly if forecast else []

    # Precipitation windows
    precip_24h = _sum_precip(hours, 24)
    precip_48h = _sum_precip(hours, 48)
    precip_72h = _sum_precip(hours, 72)

    # Wind risks
    max_wind = max((h.windspeed_ms or 0 for h in hours[:72]), default=0.0)
    max_gust = max((h.windgust_ms or 0 for h in hours[:72]), default=0.0)

    # Flood risk
    if precip_24h >= 50.0:
        adv.append(Advice("High flood risk", f"~{precip_24h:.1f} mm rain in 24h. Prepare drainage & move livestock.", "danger"))
    elif precip_48h >= 75.0:
        adv.append(Advice("Moderate flood risk", f"~{precip_48h:.1f} mm rain in 48h. Monitor rivers & protect nurseries.", "warn"))
    elif precip_72h >= 100.0:
        adv.append(Advice("Sustained heavy rain", f"~{precip_72h:.1f} mm rain in 72h. Landslide risk in hills.", "warn"))

    # Wind alerts
    if max_gust >= 25.0 or max_wind >= 25.0:
        adv.append(Advice("Severe storm risk", f"Very high winds (up to {max_gust:.1f} m/s). Secure structures.", "danger"))
    elif max_gust >= 17.0 or max_wind >= 17.0:
        adv.append(Advice("High wind alert", f"Strong winds (up to {max_gust:.1f} m/s). Tie loose materials.", "warn"))

    # If no alerts
    if not adv:
        adv.append(Advice("All clear", "No major risks detected. Continue monitoring.", "info"))

    return adv
