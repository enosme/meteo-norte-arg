"""Genera el informe diario por ciudad en Markdown."""
from datetime import datetime
from .openmeteo import pronostico
from .nubes import agregar_base_nubes
from . import metar as mt
from .smn_alertas import alertas_para_ciudad


def riesgo_granizo(df_dia):
    """INDICADOR simple, no es un pronóstico de granizo.
    Combina energía convectiva (CAPE), isoterma 0 °C baja-moderada y ráfagas."""
    cape = df_dia["cape"].max()
    iso0 = df_dia["freezing_level_height"].min()
    rafaga = df_dia["wind_gusts_10m"].max()
    puntos = 0
    puntos += 2 if cape >= 2500 else 1 if cape >= 1500 else 0
    puntos += 1 if 2500 <= iso0 <= 4500 else 0
    puntos += 1 if rafaga >= 60 else 0
    return ["Bajo", "Bajo", "Moderado", "Alto", "Alto"][puntos], cape, iso0


def riesgo_niebla(df_dia):
    """Niebla probable: aire casi saturado, viento débil y horas de madrugada."""
    noche = df_dia[(df_dia["time"].dt.hour <= 9)]
    if noche.empty:
        return "Bajo"
    cond = ((noche["temperature_2m"] - noche["dew_point_2m"]) <= 1.5) & (noche["wind_speed_10m"] < 10)
    return "Alto" if cond.sum() >= 3 else "Moderado" if cond.sum() >= 1 else "Bajo"


def informe_ciudad(ciudad, alertas_smn):
    hoy = datetime.now().date()
    df = agregar_base_nubes(pronostico(ciudad["lat"], ciudad["lon"], dias=2))
    d = df[df["time"].dt.date == hoy]
    if d.empty:
        d = df.head(24)

    granizo, cape, iso0 = riesgo_granizo(d)
    visib_min = d["visibility"].min() / 1000

    dia = d[(d["time"].dt.hour.between(8, 19))]
    base_med = dia["base_nubes_m"].median() if not dia.empty else d["base_nubes_m"].median()

    lineas = [
        f"## {ciudad['nombre']} ({ciudad['provincia']})",
        "",
        f"- **Temperatura:** mín {d['temperature_2m'].min():.0f} °C / máx {d['temperature_2m'].max():.0f} °C",
        f"- **Precipitación total prevista:** {d['precipitation'].sum():.1f} mm "
        f"(máx {d['precipitation'].max():.1f} mm/h)",
        f"- **Viento máx:** {d['wind_speed_10m'].max():.0f} km/h — **ráfaga máx:** {d['wind_gusts_10m'].max():.0f} km/h",
        f"- **CAPE máx:** {cape:.0f} J/kg (tormentas más probables con valores altos)",
        f"- **Indicador de riesgo de granizo:** {granizo} (isoterma 0 °C mín {iso0:.0f} m)",
        f"- **Visibilidad mínima:** {visib_min:.1f} km — **riesgo de niebla/neblina:** {riesgo_niebla(d)}",
        f"- **Base de nubes estimada (diurna):** ~{base_med:.0f} m sobre el suelo "
        f"(~{base_med*3.28:.0f} ft)",
    ]

    if ciudad["icao"]:
        m = mt.ultimo_metar(ciudad["icao"])
        if m:
            obs = mt.base_nubes_observada_ft(m)
            lineas.append(f"- **Observado ahora ({ciudad['icao']}):** "
                          f"{mt.fenomeno_visibilidad(m) or 'sin datos de visibilidad'}"
                          + (f", base de nubes observada {obs} ft" if obs else ", sin nubes bajas reportadas"))
        else:
            lineas.append(f"- *Sin METAR disponible para {ciudad['icao']}.*")

    av = alertas_para_ciudad(alertas_smn, ciudad)
    if av:
        lineas.append("- **Alertas SMN vigentes:**")
        for a in av:
            lineas.append(f"  - ⚠️ {a['titulo'] or a['evento']} (nivel: {a['severidad'] or 's/d'})")
    else:
        lineas.append("- **Alertas SMN:** ninguna vigente para esta zona en el feed oficial.")

    return "\n".join(lineas) + "\n"
