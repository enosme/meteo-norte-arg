"""Compara lo pronosticado contra lo observado (METAR) y mide el error."""
import pandas as pd
from .openmeteo import MODELOS


def comparar(obs, fc):
    """obs: DataFrame de historial_metar. fc: DataFrame de pronostico_modelos.
    Devuelve (tabla de errores por modelo, DataFrame emparejado por hora)."""
    if obs is None or obs.empty:
        return pd.DataFrame(), pd.DataFrame()
    o = obs.copy()
    o["hora"] = o["time"].dt.round("h")
    o = o.groupby("hora", as_index=False).mean(numeric_only=True)
    f = fc.copy()
    f["hora"] = f["time"]
    par = o.merge(f, on="hora", how="inner")
    filas = []
    for nombre, m in MODELOS.items():
        fila = {"Modelo": nombre}
        ct, cv = f"temperature_2m_{m}", f"wind_speed_10m_{m}"
        if ct in par and par["temp"].notna().any():
            fila["Error medio temperatura (°C)"] = (par[ct] - par["temp"]).abs().mean()
        if cv in par and par["viento_kmh"].notna().any():
            fila["Error medio viento (km/h)"] = (par[cv] - par["viento_kmh"]).abs().mean()
        fila["Horas comparadas"] = int(par["temp"].notna().sum())
        filas.append(fila)
    if "temperature_2m_media" in par:
        fila = {"Modelo": "Promedio de modelos",
                "Error medio temperatura (°C)": (par["temperature_2m_media"] - par["temp"]).abs().mean(),
                "Error medio viento (km/h)": (par["wind_speed_10m_media"] - par["viento_kmh"]).abs().mean(),
                "Horas comparadas": int(par["temp"].notna().sum())}
        filas.append(fila)
    tabla = pd.DataFrame(filas).round(2)
    return tabla, par
