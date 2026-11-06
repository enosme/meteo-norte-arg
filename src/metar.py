"""Observaciones reales de aeropuertos (METAR) vía aviationweather.gov."""
import re
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

def visibilidad_desde_raw(raw):
    """Lee la visibilidad del texto original del METAR (en metros, formato internacional:
    'SARE 061200Z 36010KT 9999 FEW030 ...'). Devuelve (km, tope). 'CAVOK' o 9999 = 10 km o más."""
    if not raw:
        return None, False
    if re.search(r"\bCAVOK\b", raw):
        return 10.0, True
    g = re.search(r"(?:\b\d{3}|VRB)\d{2}(?:G\d{2,3})?KT(?:\s+\d{3}V\d{3})?\s+(\d{4})\b", raw)
    if g:
        metros = int(g.group(1))
        return (10.0, True) if metros >= 9999 else (metros / 1000, False)
    return None, False


def visibilidad_metar(metar):
    """Mejor estimación en km: primero el texto original, si no, el campo 'visib' de la API."""
    km, tope = visibilidad_desde_raw(metar.get("rawOb"))
    if km is not None:
        return km, tope
    return visibilidad_km(metar.get("visib"))


def visibilidad_km(valor):
    """Convierte la visibilidad del METAR (millas terrestres, ej. 3, 0.5, '6+') a km.
    Devuelve (km, tope). tope=True significa 'más de' (el METAR no informa más allá de ~10 km)."""
    if valor is None:
        return None, False
    s = str(valor).strip()
    tope = s.endswith("+")
    try:
        return float(s.rstrip("+")) * 1.609, tope
    except ValueError:
        return None, False


def fenomeno_visibilidad(metar):
    """Texto con visibilidad (km) y fenómenos (FG = niebla, BR = neblina, HZ = bruma, FU = humo)."""
    if not metar:
        return None
    wx = metar.get("wxString") or ""
    km, tope = visibilidad_metar(metar)
    partes = []
    if km is not None:
        partes.append(f"visibilidad {'más de ' if tope else ''}{km:.1f} km")
    if wx:
        partes.append(f"fenómeno: {wx}")
    return ", ".join(partes) or None


def historial_metar(icao, horas=48):
    """Observaciones de las últimas horas como DataFrame (hora local Argentina).
    Columnas: time, temp, viento_kmh, rafaga_kmh, visib_km."""
    import pandas as pd
    try:
        r = requests.get(URL, params={"ids": icao, "format": "json", "hours": horas}, timeout=20)
        r.raise_for_status()
        filas = []
        for m in r.json():
            if m.get("obsTime") is None:
                continue
            t = pd.to_datetime(m["obsTime"], unit="s", utc=True)
            t = t.tz_convert("America/Argentina/Buenos_Aires").tz_localize(None)
            wspd, wgst = m.get("wspd"), m.get("wgst")
            vkm, _ = visibilidad_metar(m)
            filas.append({"time": t, "temp": m.get("temp"),
                          "viento_kmh": wspd * 1.852 if wspd is not None else None,
                          "rafaga_kmh": wgst * 1.852 if wgst is not None else None,
                          "visib_km": vkm, "raw": m.get("rawOb")})
        return pd.DataFrame(filas).sort_values("time") if filas else pd.DataFrame()
    except Exception:
        return pd.DataFrame()
