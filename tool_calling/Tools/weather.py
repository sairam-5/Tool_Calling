import requests
import json

def get_weather_forecast(location: str, forecast_days: int = 1) -> dict:
    """
    Fetches weather forecast data for a specified location from Open-Meteo.

    Args:
        location (str): The name of the city or location.
        forecast_days (int): Number of days for the forecast (1-16). Defaults to 1 (current weather).

    Returns:
        dict: A dictionary containing weather data or an error message.
    """
    try:
        # Geocoding to get latitude and longitude from location name.
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}"
        geo_data = requests.get(geo_url).json()

        if not geo_data.get('results'):
            return {"error": True, "message": f"Weather tool: Location '{location}' not found."}

        lat = geo_data['results'][0]['latitude']
        lon = geo_data['results'][0]['longitude']
        timezone = geo_data['results'][0].get('timezone', 'auto')

        # Fetch daily weather forecast.
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&"
            f"timezone={timezone}&forecast_days={forecast_days}"
        )
        weather_data = requests.get(weather_url).json()

        if weather_data.get('error'):
            return {"error": True, "message": weather_data.get('reason', 'Weather tool: Unknown API error.')}

        daily_forecasts = []
        if 'daily' in weather_data:
            dates = weather_data['daily']['time']
            max_temps = weather_data['daily']['temperature_2m_max']
            min_temps = weather_data['daily']['temperature_2m_min']
            precipitation = weather_data['daily']['precipitation_sum']
            weather_codes = weather_data['daily']['weathercode']

            # Simple mapping for WMO weather codes.
            weather_descriptions = {
                0: "Clear sky", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Drizzle (light)", 53: "Drizzle (moderate)", 55: "Drizzle (dense)",
                61: "Rain (slight)", 63: "Rain (moderate)", 65: "Rain (heavy)",
                71: "Snow fall (slight)", 73: "Snow fall (moderate)", 75: "Snow fall (heavy)",
                80: "Rain showers (slight)", 81: "Rain showers (moderate)", 82: "Rain showers (violent)",
                95: "Thunderstorm"
            }

            for i in range(len(dates)):
                daily_forecasts.append({
                    "date": dates[i],
                    "max_temperature": f"{max_temps[i]}°C",
                    "min_temperature": f"{min_temps[i]}°C",
                    "precipitation_sum": f"{precipitation[i]} mm",
                    "weather_description": weather_descriptions.get(weather_codes[i], "Unknown"),
                })
        return {"location": location, "forecast": daily_forecasts}

    except requests.exceptions.RequestException as req_err:
        return {"error": True, "message": f"Weather tool: Network or API request error for {location}: {str(req_err)}"}
    except Exception as e:
        return {"error": True, "message": f"Weather tool: Unexpected processing error for {location}: {str(e)}"}
