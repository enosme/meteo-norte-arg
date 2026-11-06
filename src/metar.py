"""Observaciones reales de aeropuertos (METAR) vía aviationweather.gov."""
import requests

URL = "https://aviationweather.gov/api/data/metar"

def ultimo_metar(icao):
    try:
        r = requests.get(URL, params={"ids": icao, "format": "json"}, timeout=20)
        r.raise_for_status()
        datos = r.json()
        return datos[0] if datos else None
    except Exception:
        return None

def base_nubes_observada_ft(metar):
    """Base de la capa más baja BKN/OVC (techo) o la más baja cualquiera."""
    if not metar:
        return None
    capas = [c for c in (metar.get("clouds") or []) if c.get("base") is not None]
    if not capas:
        return None
    techos = [c["base"] for c in capas if c.get("cover") in ("BKN", "OVC")]
    return min(techos) if techos else min(c["base"] for c in capas)

def fenomeno_visibilidad(metar):
    """Texto con visibilidad y fenómenos (FG = niebla, BR = neblina, FU = humo)."""
    if not metar:
        return None
    wx = metar.get("wxString") or ""
    vis = metar.get("visib")
    partes = []
    if vis is not None:
        partes.append(f"visibilidad {vis} SM")
    if wx:
        partes.append(f"fenómeno: {wx}")
    return ", ".join(partes) or None
