import json

# Load the JSON file
with open("weather_ui.json", "r") as f:
    data = json.load(f)

# Extract the code (stored under "content")
code = data["code"]

# Run the code
exec(code)
