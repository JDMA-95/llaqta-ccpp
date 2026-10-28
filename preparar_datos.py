# -*- coding: utf-8 -*-
"""
Convierte la salida de geoperu_ccpp/unir.py en el parquet liviano que usa la app.

El GeoJSON nacional pesa ~310 MB (no entra en GitHub ni conviene en Streamlit
Cloud); la app solo necesita lon/lat, así que se descarta la geometría y se
guarda en parquet comprimido con tipos compactos.

Correr con:
    python preparar_datos.py [ruta_gpkg]
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent
ORIGEN = BASE_DIR.parent / "geoperu_ccpp" / "salida"
DESTINO = BASE_DIR / "data"

TEXTO = ["codigo_ccpp", "ubigeo", "codccpp", "nombccpp", "url_reporte"]
CATEGORIAS = ["nombdist", "nombprov", "nombdep", "area_ambito_texto", "rango_poblacional_texto"]


def main() -> None:
    gpkg = Path(sys.argv[1]) if len(sys.argv) > 1 else ORIGEN / "ccpp_censo2025.gpkg"
    df = gpd.read_file(gpkg).drop(columns="geometry")
    for col in CATEGORIAS:
        df[col] = df[col].astype("category")
    for col in df.columns.difference(TEXTO + CATEGORIAS + ["lon", "lat"]):
        df[col] = df[col].astype("float32")
    DESTINO.mkdir(exist_ok=True)
    salida = DESTINO / "ccpp_censo2025.parquet"
    df.to_parquet(salida, compression="zstd", compression_level=19, index=False)
    shutil.copy(gpkg.parent / "diccionario_variables.csv", DESTINO / "diccionario_variables.csv")
    print(f"{len(df):,} CP x {df.shape[1]} columnas -> {salida} ({salida.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
