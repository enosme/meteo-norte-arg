import time
import requests
import pandas as pd

URL = "https://api.open-meteo.com/v1/forecast"
TZ = "America/Argentina/Buenos_Aires"
HORARIAS = ("temperature_2m,dew_point_2m,precipitation,precipitation_probability,"
            "wind_speed_10m,wind_gusts_10m,cape,visibility,cloud_cover_low,"
            "freezing_level_height")

# Modelos numéricos globales distintos (nombres de Open-Meteo)
MODELOS = {"ECMWF": "ecmwf_ifs025", "GFS": "gfs_seamless", "ICON": "icon_seamless"}
VARS_MODELOS = ["temperature_2m", "precipitation", "wind_speed_10m", "wind_gusts_10m"]


def _get(params, intentos=4):
    """GET con reintentos (a veces Open-Meteo tarda o corta la conexión)."""
    ultimo = None
    for i in range(intentos):
        try:
            r = requests.get(URL, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            ultimo = e
            time.sleep(2 * (i + 1))
    raise ultimo


def _a_df(hourly):
    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"])
    return df


def pronostico(lat, lon, dias=2, past_days=0):
    """Pronóstico del modelo 'best match' de Open-Meteo."""
    params = {"latitude": lat, "longitude": lon, "hourly": HORARIAS,
              "forecast_days": dias, "past_days": past_days,
              "timezone": TZ, "wind_speed_unit": "kmh"}
    return _a_df(_get(params)["hourly"])


def pronostico_modelos(lat, lon, dias=3, past_days=0):
    """Mismo punto, varios modelos. Devuelve columnas '<variable>_<modelo>' y,
    para cada variable, la media del conjunto y el rango (mín/máx) entre modelos."""
    params = {"latitude": lat, "longitude": lon,
              "hourly": ",".join(VARS_MODELOS), "models": ",".join(MODELOS.values()),
              "forecast_days": dias, "past_days": past_days,
              "timezone": TZ, "wind_speed_unit": "kmh"}
    df = _a_df(_get(params)["hourly"])
    for v in VARS_MODELOS:
        cols = [f"{v}_{m}" for m in MODELOS.values() if f"{v}_{m}" in df.columns]
        if cols:
            df[f"{v}_media"] = df[cols].mean(axis=1)
            df[f"{v}_min"] = df[cols].min(axis=1)
            df[f"{v}_max"] = df[cols].max(axis=1)
    return df


def pronostico_varias(ciudades, dias=3):
    """Una sola consulta para todas las ciudades. Devuelve {nombre: DataFrame}."""
    params = {"latitude": ",".join(str(c["lat"]) for c in ciudades),
              "longitude": ",".join(str(c["lon"]) for c in ciudades),
              "hourly": "temperature_2m,precipitation,wind_gusts_10m,cape",
              "forecast_days": dias, "timezone": TZ, "wind_speed_unit": "kmh"}
    datos = _get(params)
    if isinstance(datos, dict):      # una sola ciudad
        datos = [datos]
    return {c["nombre"]: _a_df(d["hourly"]) for c, d in zip(ciudades, datos)}
