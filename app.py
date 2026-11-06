"""Panel gráfico del proyecto. Ejecutar local:  streamlit run app.py"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from plotly.subplots import make_subplots

from src.ciudades import CIUDADES
from src.distancia import distancia_km, rumbo_grados, punto_cardinal
from src.openmeteo import pronostico, pronostico_modelos, pronostico_varias, MODELOS
from src.nubes import agregar_base_nubes
from src.smn_alertas import descargar_alertas, alertas_para_ciudad
from src.informe import riesgo_granizo, riesgo_niebla
from src.verificacion import comparar
from src import metar as mt

st.set_page_config(page_title="Meteo Norte Argentino", page_icon="⛈️", layout="wide")
TZ = "America/Argentina/Buenos_Aires"
COLORES = {"ecmwf_ifs025": "#1f77b4", "gfs_seamless": "#d62728", "icon_seamless": "#2ca02c"}


# ------------------------- datos (con caché) -------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def datos_ciudad(lat, lon):
    return agregar_base_nubes(pronostico(lat, lon, dias=3))


@st.cache_data(ttl=1800, show_spinner=False)
def datos_modelos(lat, lon, past_days):
    return pronostico_modelos(lat, lon, dias=3, past_days=past_days)


@st.cache_data(ttl=1800, show_spinner=False)
def datos_todas():
    return pronostico_varias(CIUDADES, dias=3)


@st.cache_data(ttl=900, show_spinner=False)
def historial(icao):
    return mt.historial_metar(icao, horas=48)


@st.cache_data(ttl=600, show_spinner=False)
def _alertas_cache():
    res = descargar_alertas()
    if not res:
        raise RuntimeError("sin alertas leídas")   # no se guarda un resultado vacío
    return res


def alertas_smn():
    try:
        return _alertas_cache()
    except Exception:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def metar_ciudad(icao):
    return mt.ultimo_metar(icao)


def ahora():
    return pd.Timestamp.now(tz=TZ).tz_localize(None)


def marca_ahora(fig):
    t = ahora()
    fig.add_shape(type="line", x0=t, x1=t, y0=0, y1=1, yref="paper",
                  line=dict(color="gray", dash="dot", width=1))
    return fig


def estilo(fig, titulo, y):
    fig.update_layout(title=titulo, yaxis_title=y, hovermode="x unified",
                      margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h"))
    return marca_ahora(fig)


# ------------------------- encabezado -------------------------
st.title("⛈️ Meteo Norte Argentino")
st.caption("Datos: Open-Meteo (3 modelos), METAR y alertas CAP del SMN. Son estimaciones: "
           "ante riesgo, seguí los avisos oficiales en smn.gob.ar/alertas.")

nombres = [c["nombre"] for c in CIUDADES]
elegida = st.sidebar.selectbox("Ciudad", nombres)
ciudad = next(c for c in CIUDADES if c["nombre"] == elegida)
with st.spinner("Leyendo alertas del SMN..."):
    alertas = alertas_smn()
st.sidebar.caption(f"Alertas leídas del SMN: {len(alertas)}")
if st.sidebar.button("🔄 Actualizar datos"):
    st.cache_data.clear()
    st.rerun()

# ------------------------- mapa de localidades -------------------------
filas = []
for c in CIUDADES:
    n = len(alertas_para_ciudad(alertas, c))
    filas.append({"Ciudad": c["nombre"], "lat": c["lat"], "lon": c["lon"],
                  "Estado": f"{n} alerta(s) SMN" if n else "Sin alertas"})
dfm = pd.DataFrame(filas)
usa_nuevo = hasattr(px, "scatter_map")
funcion_mapa = px.scatter_map if usa_nuevo else px.scatter_mapbox
fig_mapa = funcion_mapa(dfm, lat="lat", lon="lon", hover_name="Ciudad", color="Estado",
                        color_discrete_map={"Sin alertas": "green"},
                        hover_data={"lat": False, "lon": False}, zoom=5, height=380)
estilo_mapa = "map_style" if usa_nuevo else "mapbox_style"
fig_mapa.update_layout(**{estilo_mapa: "open-street-map"}, margin=dict(l=0, r=0, t=0, b=0))
fig_mapa.update_traces(marker=dict(size=14))
st.plotly_chart(fig_mapa, use_container_width=True)

# ------------------------- datos de la ciudad -------------------------
st.header(f"{ciudad['nombre']} ({ciudad['provincia']})")
try:
    with st.spinner("Descargando pronóstico..."):
        df = datos_ciudad(ciudad["lat"], ciudad["lon"])
except Exception as e:
    st.error(f"No se pudo descargar el pronóstico de Open-Meteo: {e}")
    st.stop()

hoy = df["time"].dt.date.min()
d = df[df["time"].dt.date == hoy]
granizo, cape, iso0 = riesgo_granizo(d)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Lluvia prevista hoy", f"{d['precipitation'].sum():.1f} mm")
c2.metric("Ráfaga máxima hoy", f"{d['wind_gusts_10m'].max():.0f} km/h")
c3.metric("Riesgo de granizo (indicador)", granizo)
c4.metric("Riesgo de niebla", riesgo_niebla(d))

tab_res, tab_mod, tab_prec, tab_todas, tab_windy = st.tabs(
    ["📊 Resumen", "🔀 Comparar modelos", "🎯 Precisión (observado vs pronóstico)",
     "🌡️ Todas las ciudades", "🛰️ Mapa con capas (Windy)"])

# ======================= RESUMEN =======================
with tab_res:
    st.subheader("Alertas del SMN")
    av = alertas_para_ciudad(alertas, ciudad)
    if av:
        for a in av:
            st.warning(f"**{a['titulo'] or a['evento']}** — nivel: {a['severidad'] or 's/d'}\n\n"
                       f"{a['descripcion'][:400]}")
    else:
        st.success("Ninguna alerta vigente para esta zona en el feed oficial.")

    if ciudad["icao"]:
        m = metar_ciudad(ciudad["icao"])
        if m:
            obs = mt.base_nubes_observada_ft(m)
            st.info(f"**Observado ahora ({ciudad['icao']}):** "
                    f"{mt.fenomeno_visibilidad(m) or 'sin datos de visibilidad'}"
                    + (f" · base de nubes observada: {obs} ft ({obs*0.3048:.0f} m)"
                       if obs else " · sin nubes bajas reportadas"))

    # Lluvia + probabilidad
    f = make_subplots(specs=[[{"secondary_y": True}]])
    f.add_bar(x=df["time"], y=df["precipitation"], name="Lluvia (mm/h)", marker_color="#1f77b4")
    if "precipitation_probability" in df:
        f.add_scatter(x=df["time"], y=df["precipitation_probability"], name="Probabilidad (%)",
                      line=dict(color="orange"), secondary_y=True)
        f.update_yaxes(title_text="%", range=[0, 100], secondary_y=True)
    f.update_yaxes(title_text="mm/h", secondary_y=False)
    estilo(f, "Precipitación y probabilidad de lluvia", "mm/h")
    f.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(f, use_container_width=True)

    g1, g2 = st.columns(2)
    with g1:
        f = go.Figure()
        f.add_scatter(x=df["time"], y=df["wind_speed_10m"], name="Viento", fill="tozeroy")
        f.add_scatter(x=df["time"], y=df["wind_gusts_10m"], name="Ráfagas")
        st.plotly_chart(estilo(f, "Viento y ráfagas (km/h)", "km/h"), use_container_width=True)

        f = px.area(df, x="time", y="cape")
        st.plotly_chart(estilo(f, "CAPE (J/kg): potencial de tormentas", "J/kg"),
                        use_container_width=True)
    with g2:
        f = go.Figure()
        f.add_scatter(x=df["time"], y=df["base_nubes_m"], name="Base de nubes", fill="tozeroy")
        st.plotly_chart(estilo(f, "Base de nubes estimada (m sobre el suelo)", "metros"),
                        use_container_width=True)

        f = go.Figure()
        f.add_scatter(x=df["time"], y=(df["visibility"] / 1000).clip(upper=10),
                      name="Modelo (limitado a 10 km)")
        if ciudad["icao"]:
            ob = historial(ciudad["icao"])
            if not ob.empty and "visib_km" in ob:
                f.add_scatter(x=ob["time"], y=ob["visib_km"].clip(upper=10),
                              mode="markers+lines", name="Observado (METAR)",
                              line=dict(color="black", width=2))
        st.plotly_chart(estilo(f, "Visibilidad (km)", "km"), use_container_width=True)
        st.caption("El METAR informa como máximo ~10 km, por eso el modelo se limita a 10 km para "
                   "poder compararlos. Los modelos no detectan bien las nieblas locales: ante "
                   "diferencias, guiate por el METAR (observación real).")

    st.subheader("Distancia a las otras localidades")
    tabla = []
    for c in CIUDADES:
        if c["nombre"] == ciudad["nombre"]:
            continue
        km = distancia_km(ciudad["lat"], ciudad["lon"], c["lat"], c["lon"])
        rb = punto_cardinal(rumbo_grados(ciudad["lat"], ciudad["lon"], c["lat"], c["lon"]))
        tabla.append({"Localidad": c["nombre"], "Distancia (km)": round(km), "Dirección": rb})
    st.dataframe(pd.DataFrame(tabla).sort_values("Distancia (km)"), hide_index=True)

# ======================= COMPARAR MODELOS =======================
with tab_mod:
    st.markdown("Tres modelos meteorológicos distintos para el mismo punto. **Cuando coinciden, "
                "el pronóstico es más confiable; cuando se separan, hay más incertidumbre.**")
    try:
        dm = datos_modelos(ciudad["lat"], ciudad["lon"], 0)
    except Exception as e:
        st.error(f"No se pudieron obtener los modelos: {e}")
        dm = None
    if dm is not None:
        variables = {"Temperatura (°C)": "temperature_2m", "Precipitación (mm/h)": "precipitation",
                     "Ráfagas (km/h)": "wind_gusts_10m", "Viento (km/h)": "wind_speed_10m"}
        sel = st.radio("Variable", list(variables), horizontal=True)
        v = variables[sel]
        f = go.Figure()
        f.add_scatter(x=dm["time"], y=dm[f"{v}_max"], line=dict(width=0), showlegend=False,
                      hoverinfo="skip")
        f.add_scatter(x=dm["time"], y=dm[f"{v}_min"], fill="tonexty", line=dict(width=0),
                      fillcolor="rgba(150,150,150,0.25)", name="Rango entre modelos",
                      hoverinfo="skip")
        for nombre, m in MODELOS.items():
            if f"{v}_{m}" in dm:
                f.add_scatter(x=dm["time"], y=dm[f"{v}_{m}"], name=nombre,
                              line=dict(color=COLORES[m], width=1.5))
        f.add_scatter(x=dm["time"], y=dm[f"{v}_media"], name="Promedio",
                      line=dict(color="black", width=3, dash="dot"))
        estilo(f, f"{sel}: comparación de modelos", sel)
        f.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(f, use_container_width=True)

        # Acuerdo entre modelos sobre la lluvia
        cols = [f"precipitation_{m}" for m in MODELOS.values() if f"precipitation_{m}" in dm]
        acuerdo = (dm[cols].fillna(0) >= 0.1).mean(axis=1) * 100
        f = px.bar(x=dm["time"], y=acuerdo)
        f.update_traces(marker_color="#1f77b4")
        estilo(f, "Acuerdo entre modelos: % que prevé lluvia (≥ 0,1 mm/h)", "% de modelos")
        f.update_yaxes(range=[0, 100])
        st.plotly_chart(f, use_container_width=True)
        st.caption("100 % = los tres modelos prevén lluvia esa hora. 33 % o 67 % = hay desacuerdo.")

# ======================= PRECISIÓN =======================
with tab_prec:
    st.markdown("Compara lo que **pronosticó cada modelo** con lo que **se observó** en el aeropuerto "
                "(METAR) en las últimas 48 horas, y mide el error. Así sabés qué modelo conviene "
                "usar en tu zona.")
    if not ciudad["icao"]:
        st.info(f"{ciudad['nombre']} no tiene aeropuerto con METAR. Elegí una ciudad como "
                "Resistencia, Corrientes (Aeropuerto), Las Lomitas, Tartagal, Posadas o Mercedes.")
    else:
        obs = historial(ciudad["icao"])
        if obs.empty:
            st.warning(f"No se pudieron obtener observaciones de {ciudad['icao']} "
                       "(el código de estación puede ser incorrecto o no haber datos recientes).")
        else:
            try:
                dmp = datos_modelos(ciudad["lat"], ciudad["lon"], 2)
                tabla_err, par = comparar(obs, dmp)
                f = go.Figure()
                for nombre, m in MODELOS.items():
                    f.add_scatter(x=dmp["time"], y=dmp[f"temperature_2m_{m}"], name=nombre,
                                  line=dict(color=COLORES[m], width=1.2))
                f.add_scatter(x=obs["time"], y=obs["temp"], name="Observado (METAR)",
                              mode="markers+lines", line=dict(color="black", width=2))
                estilo(f, f"Temperatura: observada en {ciudad['icao']} vs modelos", "°C")
                f.update_xaxes(range=[obs["time"].min(), ahora() + pd.Timedelta(hours=12)])
                st.plotly_chart(f, use_container_width=True)

                f = go.Figure()
                for nombre, m in MODELOS.items():
                    f.add_scatter(x=dmp["time"], y=dmp[f"wind_speed_10m_{m}"], name=nombre,
                                  line=dict(color=COLORES[m], width=1.2))
                f.add_scatter(x=obs["time"], y=obs["viento_kmh"], name="Observado (METAR)",
                              mode="markers+lines", line=dict(color="black", width=2))
                estilo(f, "Viento: observado vs modelos", "km/h")
                f.update_xaxes(range=[obs["time"].min(), ahora() + pd.Timedelta(hours=12)])
                st.plotly_chart(f, use_container_width=True)

                if not tabla_err.empty:
                    st.subheader("Error de cada modelo (menor es mejor)")
                    st.dataframe(tabla_err, hide_index=True)
            except Exception as e:
                st.error(f"No se pudo hacer la comparación: {e}")

# ======================= TODAS LAS CIUDADES =======================
with tab_todas:
    st.markdown("Vista conjunta de las 10 localidades: cada fila es una ciudad y cada columna una hora.")
    try:
        todas = datos_todas()
        opciones = {"Precipitación (mm/h)": ("precipitation", "Blues"),
                    "Ráfagas (km/h)": ("wind_gusts_10m", "YlOrRd"),
                    "CAPE (J/kg)": ("cape", "Purples"),
                    "Temperatura (°C)": ("temperature_2m", "RdYlBu_r")}
        sel = st.radio("Variable", list(opciones), horizontal=True, key="var_todas")
        var, escala = opciones[sel]
        nombres_c = list(todas)
        t0 = todas[nombres_c[0]]["time"]
        z = [todas[n][var].tolist() for n in nombres_c]
        f = go.Figure(go.Heatmap(z=z, x=t0, y=nombres_c, colorscale=escala,
                                 colorbar=dict(title=sel)))
        f.update_layout(title=f"{sel} por ciudad y hora", height=450,
                        margin=dict(l=10, r=10, t=50, b=10))
        marca_ahora(f)
        st.plotly_chart(f, use_container_width=True)

        resumen = pd.DataFrame({
            "Ciudad": nombres_c,
            "Lluvia 72 h (mm)": [round(todas[n]["precipitation"].sum(), 1) for n in nombres_c],
            "Ráfaga máx (km/h)": [round(todas[n]["wind_gusts_10m"].max()) for n in nombres_c],
            "CAPE máx (J/kg)": [round(todas[n]["cape"].max()) for n in nombres_c],
        })
        st.dataframe(resumen, hide_index=True)
    except Exception as e:
        st.error(f"No se pudieron descargar los datos de todas las ciudades: {e}")

# ======================= WINDY =======================
with tab_windy:
    CAPAS = {"Viento": "wind", "Ráfagas": "gust", "Lluvia": "rain", "Tormentas": "thunder",
             "Nubes": "clouds", "CAPE": "cape", "Temperatura": "temp", "Radar": "radar",
             "Satélite": "satellite", "Presión": "pressure"}
    cw1, cw2 = st.columns([2, 1])
    capa = cw1.radio("Capa", list(CAPAS), horizontal=True)
    zoom_w = cw2.slider("Zoom", 5, 10, 7)
    lat_c, lon_c = ciudad["lat"], ciudad["lon"]
    url_windy = (
        "https://embed.windy.com/embed2.html"
        f"?lat={lat_c}&lon={lon_c}&detailLat={lat_c}&detailLon={lon_c}"
        f"&zoom={zoom_w}&level=surface&overlay={CAPAS[capa]}&product=ecmwf"
        "&menu=true&message=true&marker=true&calendar=now&type=map"
        "&location=coordinates&detail=true&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1")
    components.iframe(url_windy, height=620)
    st.caption("Mapa de Windy (windy.com). Dentro del mapa podés abrir el menú para más capas "
               "y mover la línea de tiempo.")

# ------------------------- último informe -------------------------
with st.expander("Último informe diario (generado por GitHub Actions)"):
    from pathlib import Path
    archivos = sorted(Path("informes").glob("*.md")) if Path("informes").exists() else []
    if archivos:
        st.markdown(archivos[-1].read_text(encoding="utf-8"))
    else:
        st.write("Todavía no hay informes guardados.")
