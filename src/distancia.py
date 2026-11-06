from math import radians, sin, cos, asin, sqrt, atan2, degrees

def distancia_km(lat1, lon1, lat2, lon2):
    """Distancia entre dos puntos (fórmula de Haversine)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))

def rumbo_grados(lat1, lon1, lat2, lon2):
    """Dirección desde el punto 1 hacia el punto 2 (0° = Norte)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    y = sin(lon2 - lon1) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1)
    return (degrees(atan2(y, x)) + 360) % 360

def punto_cardinal(grados):
    puntos = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    return puntos[int((grados + 22.5) // 45) % 8]
