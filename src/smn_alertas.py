"""Alertas del Sistema de Alerta Temprana (SAT) del SMN en formato CAP.

Feed oficial (listado en el Alert Hub de la OMM): https://ssl.smn.gob.ar/CAP/AR.php
El formato exacto puede cambiar: el parser es tolerante y si algo falla
devuelve lista vacía y avisa, sin romper el informe.

Los "avisos a muy corto plazo" (nowcasting) del SMN se publican en
https://www.smn.gob.ar/alertas ; si el feed CAP los incluye, aparecen acá.
"""
import requests
import xml.etree.ElementTree as ET

FEED = "https://ssl.smn.gob.ar/CAP/AR.php"

def _limpiar(tag):
    return tag.split("}")[-1]

def _hijos(elem, nombre):
    return [c for c in elem.iter() if _limpiar(c.tag) == nombre]

def _texto(elem, nombre):
    for c in elem.iter():
        if _limpiar(c.tag) == nombre and c.text:
            return c.text.strip()
    return ""

def _punto_en_poligono(lat, lon, pol):
    """Ray casting. pol = lista de (lat, lon)."""
    dentro = False
    n = len(pol)
    for i in range(n):
        y1, x1 = pol[i]
        y2, x2 = pol[(i + 1) % n]
        if (x1 > lon) != (x2 > lon):
            y_cruce = (y2 - y1) * (lon - x1) / (x2 - x1) + y1
            if lat < y_cruce:
                dentro = not dentro
    return dentro

def _parsear_cap(xml_texto):
    alertas = []
    raiz = ET.fromstring(xml_texto)
    for info in _hijos(raiz, "info"):
        poligonos = []
        for p in _hijos(info, "polygon"):
            if p.text:
                pts = [tuple(map(float, par.split(","))) for par in p.text.split()]
                poligonos.append(pts)
        alertas.append({
            "evento": _texto(info, "event"),
            "severidad": _texto(info, "severity"),
            "titulo": _texto(info, "headline"),
            "descripcion": _texto(info, "description"),
            "area": _texto(info, "areaDesc"),
            "desde": _texto(info, "onset") or _texto(info, "effective"),
            "hasta": _texto(info, "expires"),
            "poligonos": poligonos,
        })
    return alertas

def descargar_alertas():
    """Devuelve la lista de alertas vigentes (o [] si no se pudo leer)."""
    try:
        r = requests.get(FEED, timeout=30)
        r.raise_for_status()
        raiz = ET.fromstring(r.content)
        # El feed puede ser un CAP directo o un índice (RSS/Atom) con links a CAPs
        if _hijos(raiz, "info"):
            return _parsear_cap(r.text)
        alertas = []
        enlaces = set()
        for e in raiz.iter():
            if _limpiar(e.tag) == "link":
                url = e.attrib.get("href") or (e.text or "").strip()
                if url.startswith("http"):
                    enlaces.add(url)
        for url in enlaces:
            try:
                rc = requests.get(url, timeout=30)
                if rc.ok and "<info" in rc.text:
                    alertas += _parsear_cap(rc.text)
            except Exception:
                continue
        return alertas
    except Exception as e:
        print(f"[aviso] No se pudo leer el feed de alertas del SMN: {e}")
        return []

def alertas_para_ciudad(alertas, ciudad):
    """Alertas que cubren el punto (polígono) o mencionan la provincia."""
    resultado = []
    prov = ciudad["provincia"].lower()
    for a in alertas:
        en_poligono = any(_punto_en_poligono(ciudad["lat"], ciudad["lon"], p) for p in a["poligonos"])
        menciona = prov in a["area"].lower() or prov in a["descripcion"].lower()
        if en_poligono or (not a["poligonos"] and menciona):
            resultado.append(a)
    return resultado
