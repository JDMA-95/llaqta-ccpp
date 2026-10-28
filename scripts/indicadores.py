# -*- coding: utf-8 -*-
"""
Catálogo de indicadores porcentuales y su agregación correcta.

Cada `pct_<x>` del censo es n_<x> / universo * 100, pero el universo no es
siempre el mismo (viviendas, hogares, hogares con baño, viviendas con red o
pilón...). Para un ámbito (distrito, provincia...) el porcentaje se recalcula
como suma(n) / suma(universo), nunca como promedio de porcentajes.
"""

from __future__ import annotations

import pandas as pd

VIV = "total_viviendas_universo"
HOG = "total_hogares_universo"

# clave: (etiqueta, grupo, universo, mas_es_mejor)
INDICADORES: dict[str, tuple[str, str, str, bool]] = {
    "agua_red_publica": ("Agua por red pública", "Agua y saneamiento", VIV, True),
    "agua_pilon_publico": ("Agua por pilón o pileta pública", "Agua y saneamiento", VIV, False),
    "agua_no_potable": ("Sin abastecimiento de agua potable", "Agua y saneamiento", VIV, False),
    "agua_continua": ("Agua todos los días (red o pilón)", "Agua y saneamiento", "n_universo_agua_red_pilon", True),
    "saneamiento_adecuado": ("Saneamiento adecuado", "Agua y saneamiento", VIV, True),
    "saneamiento_sin_conexion": ("Sin servicios higiénicos", "Agua y saneamiento", VIV, False),
    "bano_exclusivo": ("Baño de uso exclusivo del hogar", "Agua y saneamiento", "n_universo_bano", True),
    "electricidad_red_publica": ("Electricidad de red pública", "Energía", VIV, True),
    "sin_electricidad": ("Sin alumbrado eléctrico", "Energía", VIV, False),
    "electricidad_alternativa": ("Energía solar o eólica", "Energía", VIV, True),
    "cocina_energia_limpia": ("Cocina con energía limpia", "Energía", HOG, True),
    "cocina_energia_contaminante": ("Cocina con energía contaminante", "Energía", HOG, False),
    "cocina_lena": ("Cocina con leña", "Energía", HOG, False),
    "pared_noble": ("Pared de material noble", "Vivienda", VIV, True),
    "pared_precaria": ("Pared de material precario", "Vivienda", VIV, False),
    "techo_noble": ("Techo de material noble", "Vivienda", VIV, True),
    "techo_precario": ("Techo de material precario", "Vivienda", VIV, False),
    "piso_noble": ("Piso de material noble", "Vivienda", VIV, True),
    "piso_tierra": ("Piso de tierra", "Vivienda", VIV, False),
    "hacinamiento_critico": ("Hogares en hacinamiento crítico", "Vivienda", "hac_total_hogares_universo", False),
    "tenencia_propia": ("Vivienda propia", "Vivienda", HOG, True),
    "tenencia_alquilada": ("Vivienda alquilada", "Vivienda", HOG, True),
    "internet_fijo": ("Internet fijo", "Conectividad y equipamiento", HOG, True),
    "internet_movil": ("Internet móvil", "Conectividad y equipamiento", HOG, True),
    "sin_internet": ("Sin acceso a internet", "Conectividad y equipamiento", HOG, False),
    "telefono_celular": ("Teléfono celular", "Conectividad y equipamiento", HOG, True),
    "telefono_fijo": ("Teléfono fijo", "Conectividad y equipamiento", HOG, True),
    "tv_cable": ("TV por cable o satelital", "Conectividad y equipamiento", HOG, True),
    "con_computadora": ("Computadora, laptop o tablet", "Conectividad y equipamiento", HOG, True),
    "con_refrigeradora": ("Refrigeradora o congeladora", "Conectividad y equipamiento", HOG, True),
    "con_vehiculo_motorizado": ("Auto o moto", "Conectividad y equipamiento", HOG, True),
    "con_transporte_fluvial": ("Lancha, bote o canoa", "Conectividad y equipamiento", HOG, True),
    "residuos_manejo_formal": ("Manejo formal de residuos sólidos", "Residuos", HOG, True),
    "residuos_riesgo_ambiental": ("Manejo de residuos de riesgo ambiental", "Residuos", HOG, False),
}


def etiqueta(clave: str) -> str:
    return INDICADORES[clave][0]


def por_grupo() -> dict[str, list[str]]:
    grupos: dict[str, list[str]] = {}
    for clave, (_, grupo, _, _) in INDICADORES.items():
        grupos.setdefault(grupo, []).append(clave)
    return grupos


def agregado(df: pd.DataFrame, clave: str) -> float | None:
    """% del indicador para el conjunto de filas: suma(n) / suma(universo)."""
    universo = df[INDICADORES[clave][2]].sum()
    if not universo:
        return None
    return float(df[f"n_{clave}"].sum() / universo * 100)


def tabla_por(df: pd.DataFrame, nivel: str, claves: list[str]) -> pd.DataFrame:
    """Población, CP y % agregados de cada indicador por departamento/provincia/distrito."""
    filas = []
    for nombre, g in df.groupby(nivel, observed=True):
        fila = {nivel: nombre, "Centros poblados": len(g), "Población": int(g["poblacion_censada"].sum())}
        for clave in claves:
            fila[etiqueta(clave)] = agregado(g, clave)
        filas.append(fila)
    return pd.DataFrame(filas)
