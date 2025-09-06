from __future__ import annotations
import argparse, os, sys, json
from rich.console import Console
from rich.table import Table
from rich import box
from app.weather import get_hourly_forecast
from app.recommendations import recommend_precautions

console = Console()


def print_hourly_forecast(points, limit):
    table = Table(title=f"Weather Outlook (next {limit} slots)", box=box.SIMPLE_HEAVY)
    table.add_column("Time")
    table.add_column("Temp °C")
    table.add_column("Humidity %")
    table.add_column("Precip mm")
    table.add_column("Wind (km/hr)")
    table.add_column("Gust (km/hr)")

    for p in points[:limit]:
        table.add_row(
            p.time,
            f"{p.temp_c:.1f}",
            f"{p.humidity if p.humidity is not None else '-'}",
            f"{p.precipitation_mm:.1f}",
            f"{p.windspeed_ms:.1f}",
            f"{p.windgust_ms:.1f}" if p.windgust_ms is not None else "-"
        )
    console.print(table)


def print_advice(items):
    table = Table(title="Disaster Risk Warnings", box=box.SIMPLE_HEAVY)
    table.add_column("Title", style="bold")
    table.add_column("Details", style="")
    for a in items:
        table.add_row(a.title, a.details)
    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="weather precautions")
    parser.add_argument("--city", type=str, help="City name (e.g., 'Kochi,IN' or 'Thiruvananthapuram,IN')")
    parser.add_argument("--slots", type=int, default=24, help="How many hourly slots to display (default 24 ~ 1 day)") 
    args = parser.parse_args()


       # Get forecast
    console.rule("[bold cyan]Fetching Weather Forecast")
    try:
        forecast = get_hourly_forecast(city=args.city, days=max(1, args.slots // 24 + 1))
        print_hourly_forecast(forecast.hourly, limit=args.slots)

    except Exception as e:
        console.print(f"[red]Could not fetch forecast:[/red] {e}")
        forecast = None

    # Advice
    console.rule("[bold cyan]Generating Precautions")
    advice = recommend_precautions(forecast)
    print_advice(advice)


if __name__ == "__main__":
    main()
