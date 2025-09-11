import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime, timedelta
import pytz
from weather import get_hourly_forecast

LOCAL_TZ = pytz.timezone("Asia/Kolkata")

def analyze_forecast_ui(forecast, slots, output_widget):
    output_widget.delete(1.0, tk.END)  # Clear previous output
    now = datetime.now(LOCAL_TZ)
    hourly = forecast.hourly

    start_idx = 0
    for i, point in enumerate(hourly):
        point_time = datetime.fromisoformat(point.time)
        if point_time.tzinfo is None:
            point_time = pytz.UTC.localize(point_time).astimezone(LOCAL_TZ)
        if point_time >= now:
            start_idx = i
            break

    selected = hourly[start_idx:start_idx + slots]

    total_rain = sum(p.precipitation_mm for p in selected)
    max_wind = max(p.windspeed_ms for p in selected)
    max_gust = max((p.windgust_ms for p in selected if p.windgust_ms is not None), default=0)

    # --- Forecast output ---
    output_widget.insert(tk.END, "--- Weather Forecast ---\n")
    for point in selected:
        t = datetime.fromisoformat(point.time)
        if t.tzinfo is None:
            t = pytz.UTC.localize(t).astimezone(LOCAL_TZ)
        day = t.strftime("%A")
        date = t.strftime("%d-%b-%Y")
        start = t.strftime("%I %p").lstrip("0")
        end = (t + timedelta(hours=1)).strftime("%I %p").lstrip("0")
        output_widget.insert(
            tk.END,
            f"{day}, {date} | {start}–{end}: {point.temp_c}°C, "
            f"Rain: {point.precipitation_mm}mm, "
            f"Wind: {point.windspeed_ms:.1f} km/hr, "
            f"Gusts: {point.windgust_ms:.1f} km/hr\n"
        )

    # --- Alerts ---
    output_widget.insert(tk.END, "\n=== Alerts ===\n")
    # Rain/flood alerts
    if total_rain >= 50:
        output_widget.insert(tk.END, f"⚠️ High flood risk: {total_rain:.1f} mm rain expected in {slots}h\n")
    elif total_rain >= 30:
        output_widget.insert(tk.END, f"⚠️ Moderate flood risk: {total_rain:.1f} mm rain expected\n")
    else:
        output_widget.insert(tk.END, "✅ Low flood risk\n")

    # Wind alerts
    if max_gust >= 25 or max_wind >= 20:
        output_widget.insert(tk.END, f"🌪️ Storm warning: Winds up to {max_gust:.1f} km/hr\n")
    elif max_gust >= 15:
        output_widget.insert(tk.END, f"💨 Strong winds: Gusts up to {max_gust:.1f} km/hr\n")
    else:
        output_widget.insert(tk.END, "✅ No severe wind expected\n")

    # All-clear if both rain and wind are low
    if total_rain <= 5 and max_wind <= 15:
        output_widget.insert(tk.END, "✅ All clear: No major risks detected.\n")

def fetch_forecast(city_entry, hours_entry, output_widget):
    city = city_entry.get().strip() or "Kochi"
    try:
        slots = int(hours_entry.get() or 24)
        if slots <= 0:
            raise ValueError
    except ValueError:
        messagebox.showwarning("Input Warning", "Invalid hours entered. Using default 24 hours.")
        slots = 24

    forecast = get_hourly_forecast(city, slots)
    if forecast:
        analyze_forecast_ui(forecast, slots, output_widget)
    else:
        messagebox.showerror("Error", f"Could not fetch forecast for '{city}'.")

def main():
    # --- Tkinter UI ---
    root = tk.Tk()
    root.title("Weather Forecast")
    root.geometry("700x500")

    tk.Label(root, text="City:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    city_entry = tk.Entry(root, width=30)
    city_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(root, text="Hours to forecast:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    hours_entry = tk.Entry(root, width=10)
    hours_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    fetch_btn = tk.Button(root, text="Get Forecast", command=lambda: fetch_forecast(city_entry, hours_entry, output_widget))
    fetch_btn.grid(row=2, column=0, columnspan=2, pady=10)

    output_widget = scrolledtext.ScrolledText(root, width=85, height=25)
    output_widget.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    root.mainloop()
    