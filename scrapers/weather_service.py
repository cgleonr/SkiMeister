import requests
from datetime import datetime, timedelta
import config

class WeatherService:
    """Service to fetch weather forecasts from Open-Meteo API"""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    def get_forecast(self, lat, lng):
        """
        Fetch 7-day forecast for given coordinates
        """
        try:
            params = {
                "latitude": lat,
                "longitude": lng,
                "daily": "temperature_2m_max,temperature_2m_min,snowfall_sum,weathercode",
                "timezone": "auto"
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "daily" not in data:
                return []
            
            daily = data["daily"]
            forecasts = []
            
            for i in range(len(daily["time"])):
                forecast = {
                    "date": datetime.fromisoformat(daily["time"][i]),
                    "temp_max": daily["temperature_2m_max"][i],
                    "temp_min": daily["temperature_2m_min"][i],
                    "snow_forecast_cm": int(daily["snowfall_sum"][i]),
                    "symbol": self._map_weather_code(daily["weathercode"][i])
                }
                forecasts.append(forecast)
                
            return forecasts
            
        except Exception as e:
            print(f"Error fetching Open-Meteo forecast: {e}")
            return []
            
    def _map_weather_code(self, code):
        """Map WMO Weather Interpretation Codes to symbols"""
        # https://open-meteo.com/en/docs
        mapping = {
            0: "sunny",
            1: "mostly_sunny",
            2: "partly_cloudy",
            3: "cloudy",
            45: "fog",
            48: "fog",
            51: "drizzle",
            53: "drizzle",
            55: "drizzle",
            61: "rain",
            63: "rain",
            65: "rain",
            71: "snow",
            73: "snow",
            75: "snow",
            77: "snow_grains",
            80: "rain_showers",
            81: "rain_showers",
            82: "rain_showers",
            85: "snow_showers",
            86: "snow_showers",
            95: "thunderstorm",
        }
        return mapping.get(code, "unknown")
