"""Uso:  python main.py
Genera informes/AAAA-MM-DD.md con el informe de todas las ciudades."""
import time
from datetime import datetime
from pathlib import Path
from src.ciudades import CIUDADES
from src.smn_alertas import descargar_alertas
from src.informe import informe_ciudad


def main():
    alertas = descargar_alertas()
    print(f"Alertas SMN leídas: {len(alertas)}")
    hoy = datetime.now().strftime("%Y-%m-%d")
    partes = [f"# Informe meteorológico — {hoy}\n",
              "> Datos: Open-Meteo, METAR (aviationweather.gov) y alertas CAP del SMN. "
              "Son estimaciones; ante riesgo, seguí siempre los avisos oficiales del SMN "
              "(smn.gob.ar/alertas).\n"]
    for c in CIUDADES:
        time.sleep(1)
        try:
            partes.append(informe_ciudad(c, alertas))
        except Exception as e:
            partes.append(f"## {c['nombre']}\n\n*No se pudo generar el informe: {e}*\n")
    Path("informes").mkdir(exist_ok=True)
    salida = Path("informes") / f"{hoy}.md"
    salida.write_text("\n".join(partes), encoding="utf-8")
    print(f"Informe guardado en {salida}")


if __name__ == "__main__":
    main()
