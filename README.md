# Llaqta — centros poblados del Perú · Censo 2025

*Llaqta* es "pueblo" en quechua. App Streamlit para explorar los **93 676 centros poblados** del
Perú con **34 indicadores de vivienda y hogar** del Censo 2025 (agua, saneamiento, energía,
materiales, hacinamiento, conectividad, equipamiento y residuos).

- **Mapa:** cada CP es un punto, coloreado por el indicador elegido; el tamaño indica la población.
- **Resumen:** % del ámbito filtrado y comparación por departamento, provincia o distrito.
- **Centros poblados:** tabla con enlace a la ficha censal de cada CP. Descarga del ámbito en
  CSV, Excel o GeoJSON (Excel y GeoJSON hasta 15 000 CP).
- **Diccionario:** las 110 variables, con etiqueta, capa de origen y número de nulos.

Los porcentajes de un ámbito se recalculan como `suma(n) / suma(universo)`. Nunca se
promedian los porcentajes de los CP.

## Fuente

INEI, Censos Nacionales 2025. Son las capas de centros poblados publicadas como WFS en
[GEOPERÚ](https://visor.geoperu.gob.pe), descargadas el 21/10/2026 con la descarga oficial del visor:

| Capa GEOPERÚ | Contenido |
|---|---|
| `peru_ccpp_mayor_` | Nombre, ubigeo, ámbito, población, punto |
| `servicios_agua_red_publica_ccpp` | Agua, saneamiento, electricidad, materiales, precariedad |
| `hogar_bano_exclusivo_ccpp` | Internet, equipamiento, cocina, residuos, tenencia |
| `hacinamiento_critico_ccpp` | Personas por habitación, hacinamiento crítico |

Hay 9 901 CP que figuran con población 0 y sin datos de vivienda ni hogar. La app los oculta por defecto.

## Correr en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Actualizar los datos

`data/ccpp_censo2025.parquet` (9 MB) se genera a partir del GeoPackage nacional que arma
`geoperu_ccpp/unir.py`:

```bash
python preparar_datos.py ruta/a/ccpp_censo2025.gpkg
```
