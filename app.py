"""Panel gráfico del proyecto. Ejecutar local:  streamlit run app.py"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.ciudades import CIUDADES
from src.distancia import distancia_km, rumbo_grados, punto_cardinal
from src.openmeteo import pronostico
from src.nubes import agregar_base_nubes
from src.smn_alertas import descargar_alertas, alertas_para_ciudad
from src.informe import riesgo_granizo, riesgo_niebla
from src import metar as mt

st.set_page_config(page_title="Meteo Norte Argentino", page_icon="⛈️", layout="wide")


@st.cache_data(ttl=1800)
def datos_ciudad(lat, lon):
    return agregar_base_nubes(pronostico(lat, lon, dias=3))


@st.cache_data(ttl=600)
def alertas_smn():
    return descargar_alertas()


@st.cache_data(ttl=600)
def metar_ciudad(icao):
    return mt.ultimo_metar(icao)


st.title("⛈️ Meteo Norte Argentino")
st.caption("Datos: Open-Meteo, METAR y alertas CAP del SMN. Son estimaciones: "
           "ante riesgo, seguí los avisos oficiales en smn.gob.ar/alertas.")

nombres = [c["nombre"] for c in CIUDADES]
elegida = st.sidebar.selectbox("Ciudad", nombres)
ciudad = next(c for c in CIUDADES if c["nombre"] == elegida)
alertas = alertas_smn()

# ---------- Mapa general ----------
st.subheader("Mapa de localidades")
filas = []
for c in CIUDADES:
    n = len(alertas_para_ciudad(alertas, c))
    filas.append({"Ciudad": c["nombre"], "lat": c["lat"], "lon": c["lon"],
                  "Estado": f"{n} alerta(s) SMN" if n else "Sin alertas",
                  "Distancia a la ciudad elegida (km)":
                      round(distancia_km(ciudad["lat"], ciudad["lon"], c["lat"], c["lon"]))})
dfm = pd.DataFrame(filas)
fig_mapa = px.scatter_mapbox(
    dfm, lat="lat", lon="lon", hover_name="Ciudad", color="Estado",
    color_discrete_map={"Sin alertas": "green"},
    hover_data={"lat": False, "lon": False}, zoom=5, height=450)
fig_mapa.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
fig_mapa.update_traces(marker=dict(size=14))
st.plotly_chart(fig_mapa, use_container_width=True)

# ---------- Ciudad elegida ----------
st.header(f"{ciudad['nombre']} ({ciudad['provincia']})")
df = datos_ciudad(ciudad["lat"], ciudad["lon"])
hoy = df["time"].dt.date.min()
d = df[df["time"].dt.date == hoy]

granizo, cape, iso0 = riesgo_granizo(d)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Lluvia prevista hoy", f"{d['precipitation'].sum():.1f} mm")
c2.metric("Ráfaga máxima hoy", f"{d['wind_gusts_10m'].max():.0f} km/h")
c3.metric("Riesgo de granizo (indicador)", granizo)
c4.metric("Riesgo de niebla", riesgo_niebla(d))

# Alertas
st.subheader("Alertas del SMN")
av = alertas_para_ciudad(alertas, ciudad)
if av:
    for a in av:
        st.warning(f"**{a['titulo'] or a['evento']}** — nivel: {a['severidad'] or 's/d'}\n\n"
                   f"{a['descripcion'][:400]}")
else:
    st.success("Ninguna alerta vigente para esta zona en el feed oficial.")

# Observación real
if ciudad["icao"]:
    m = metar_ciudad(ciudad["icao"])
    if m:
        obs = mt.base_nubes_observada_ft(m)
        st.info(f"**Observado ahora ({ciudad['icao']}):** "
                f"{mt.fenomeno_visibilidad(m) or 'sin datos de visibilidad'}"
                + (f" · base de nubes observada: {obs} ft ({obs*0.3048:.0f} m)" if obs else " · sin nubes bajas reportadas"))

# Gráficos
st.subheader("Pronóstico a 72 horas")
g1, g2 = st.columns(2)

with g1:
    f = px.bar(df, x="time", y="precipitation", title="Precipitación (mm/h)")
    f.update_layout(xaxis_title="", yaxis_title="mm/h")
    st.plotly_chart(f, use_container_width=True)

    f = go.Figure()
    f.add_scatter(x=df["time"], y=df["wind_speed_10m"], name="Viento")
    f.add_scatter(x=df["time"], y=df["wind_gusts_10m"], name="Ráfagas")
    f.update_layout(title="Viento y ráfagas (km/h)", yaxis_title="km/h")
    st.plotly_chart(f, use_container_width=True)

with g2:
    f = px.line(df, x="time", y="base_nubes_m",
                title="Altura estimada de la base de nubes (m sobre el suelo)")
    f.update_layout(xaxis_title="", yaxis_title="metros")
    st.plotly_chart(f, use_container_width=True)
    st.caption("Estimación por nivel de condensación (125 × (T − Td)). "
               "Más confiable con nubes convectivas diurnas.")

    f = px.area(df, x="time", y="cape", title="CAPE (J/kg): potencial de tormentas")
    f.update_layout(xaxis_title="", yaxis_title="J/kg")
    st.plotly_chart(f, use_container_width=True)

f = px.line(df, x="time", y=df["visibility"] / 1000, title="Visibilidad (km)")
f.update_layout(xaxis_title="", yaxis_title="km")
st.plotly_chart(f, use_container_width=True)

# Distancias
st.subheader("Distancia a las otras localidades")
tabla = []
for c in CIUDADES:
    if c["nombre"] == ciudad["nombre"]:
        continue
    km = distancia_km(ciudad["lat"], ciudad["lon"], c["lat"], c["lon"])
    rb = punto_cardinal(rumbo_grados(ciudad["lat"], ciudad["lon"], c["lat"], c["lon"]))
    tabla.append({"Localidad": c["nombre"], "Distancia (km)": round(km), "Dirección": rb})
st.dataframe(pd.DataFrame(tabla).sort_values("Distancia (km)"), hide_index=True)

# Informes guardados
with st.expander("Último informe diario (generado por GitHub Actions)"):
    from pathlib import Path
    archivos = sorted(Path("informes").glob("*.md")) if Path("informes").exists() else []
    if archivos:
        st.markdown(archivos[-1].read_text(encoding="utf-8"))
    else:
        st.write("Todavía no hay informes guardados.")
