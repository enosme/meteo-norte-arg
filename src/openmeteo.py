import time
import requests
import pandas as pd

URL = "https://api.open-meteo.com/v1/forecast"
HORARIAS = ("temperature_2m,dew_point_2m,precipitation,wind_speed_10m,"
            "wind_gusts_10m,cape,visibility,cloud_cover_low,freezing_level_height")

def pronostico(lat, lon, dias=2, intentos=4):
    """Consulta Open-Meteo con reintentos (a veces tarda o corta la conexión)."""
    params = {
        "latitude": lat, "longitude": lon, "hourly": HORARIAS,
        "forecast_days": dias, "timezone": "America/Argentina/Buenos_Aires",
        "wind_speed_unit": "kmh",
    }
    ultimo_error = None
    for i in range(intentos):
        try:
            r = requests.get(URL, params=params, timeout=20)
            r.raise_for_status()
            df = pd.DataFrame(r.json()["hourly"])
            df["time"] = pd.to_datetime(df["time"])
            return df
        except Exception as e:
            ultimo_error = e
            time.sleep(2 * (i + 1))   # espera 2, 4, 6 s entre intentos
    raise ultimo_error
