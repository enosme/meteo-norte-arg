"""Altura estimada de la base de las nubes.

Método: nivel de condensación por ascenso (LCL), aproximación de Espy:
    base (m sobre el suelo) ≈ 125 * (T - Td)
Es una ESTIMACIÓN para nubes convectivas/cúmulos de capa límite. Para capas
estratiformes o nubes altas puede errar bastante. Se compara contra el METAR
(base observada) para ver qué tan bien funciona.
"""

def base_nubes_m(temp_c, rocio_c):
    return max(0.0, 125.0 * (temp_c - rocio_c))

def m_a_ft(m):
    return m * 3.28084

def agregar_base_nubes(df):
    df = df.copy()
    df["base_nubes_m"] = [base_nubes_m(t, td) for t, td in zip(df["temperature_2m"], df["dew_point_2m"])]
    df["base_nubes_ft"] = df["base_nubes_m"].apply(m_a_ft)
    return df
