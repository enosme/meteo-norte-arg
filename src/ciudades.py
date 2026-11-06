"""Ciudades monitoreadas. 'icao' = aeropuerto con METAR (None si no tiene).
Verificá los códigos ICAO en aviationweather.gov: si una estación no
reporta, el programa la saltea sin fallar."""

CIUDADES = [
    {"nombre": "Resistencia",                 "provincia": "Chaco",      "lat": -27.46, "lon": -58.98, "icao": "SARE"},
    {"nombre": "Corrientes (Aeropuerto)",     "provincia": "Corrientes", "lat": -27.45, "lon": -58.76, "icao": "SARC"},
    {"nombre": "Pirané",                      "provincia": "Formosa",    "lat": -25.73, "lon": -59.11, "icao": None},
    {"nombre": "Las Lomitas",                 "provincia": "Formosa",    "lat": -24.71, "lon": -60.59, "icao": "SARL"},
    {"nombre": "Ing. Guillermo N. Juárez",    "provincia": "Formosa",    "lat": -23.90, "lon": -61.85, "icao": None},
    {"nombre": "Tartagal",                    "provincia": "Salta",      "lat": -22.52, "lon": -63.80, "icao": "SAST"},
    {"nombre": "Posadas",                     "provincia": "Misiones",   "lat": -27.37, "lon": -55.90, "icao": "SARP"},
    {"nombre": "San Pedro",                   "provincia": "Misiones",   "lat": -26.62, "lon": -54.12, "icao": None},
    {"nombre": "Mercedes",                    "provincia": "Corrientes", "lat": -29.18, "lon": -58.08, "icao": "SARM"},
    {"nombre": "Tostado",                     "provincia": "Santa Fe",   "lat": -29.23, "lon": -61.77, "icao": None},
]
