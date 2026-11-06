import requests
import pandas as pd

URL = "https://api.open-meteo.com/v1/forecast"
HORARIAS = ("temperature_2m,dew_point_2m,precipitation,wind_speed_10m,"
            "wind_gusts_10m,cape,visibility,cloud_cover_low,freezing_level_height")

def pronostico(lat, lon, dias=2):
    params = {
        "latitude": lat, "longitude": lon, "hourly": HORARIAS,
        "forecast_days": dias, "timezone": "America/Argentina/Buenos_Aires",
        "wind_speed_unit": "kmh",
    }
    r = requests.get(URL, params=params, timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df
