# Meteo Norte Argentino

Informe diario de condiciones meteorológicas para 10 localidades del norte argentino:
Resistencia, Corrientes (Aeropuerto), Pirané, Las Lomitas, Ing. Guillermo N. Juárez,
Tartagal, Posadas, San Pedro (Misiones), Mercedes (Corrientes) y Tostado (Santa Fe).

## Qué incluye
- Precipitación, viento, ráfagas, CAPE (potencial de tormentas) y visibilidad (Open-Meteo)
- Indicador de riesgo de granizo y de niebla/neblina
- **Altura estimada de la base de las nubes** (método LCL: 125 × (T − Td)), con el METAR como observación real cuando hay aeropuerto
- **Alertas del Sistema de Alerta Temprana del SMN** (feed CAP oficial), cruzadas con la ubicación de cada ciudad
- Informe diario en `informes/AAAA-MM-DD.md`, generado automáticamente con GitHub Actions

## Uso
```bash
pip install -r requirements.txt
python main.py
```

## Limitaciones (importante)
- No es un pronóstico oficial. Para decisiones de seguridad usá los avisos del SMN.
- La base de nubes por LCL funciona mejor con nubes convectivas diurnas.
- Los avisos a muy corto plazo del SMN dependen de lo que publique el feed CAP; verificá en smn.gob.ar/alertas.
- Verificá los códigos ICAO de `src/ciudades.py`; las ciudades sin aeropuerto no tienen METAR.

## Próximos pasos
Rayos (GOES GLM) con distancia al más cercano, focos de calor (NASA FIRMS) para humo,
reflectividad de radar y un mapa con Streamlit + Folium.
