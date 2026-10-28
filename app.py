# -*- coding: utf-8 -*-
"""
Llaqta -- centros poblados del Perú con los indicadores de vivienda y hogar
del Censo 2025 (INEI, publicados en GEOPERÚ).

Llaqta es "pueblo" en quechua. Explora los 93 676 centros poblados:

  1. Mapa        -- cada CP como punto, coloreado por el indicador elegido.
  2. Resumen     -- % agregados del ámbito filtrado y comparación por
                    departamento / provincia / distrito.
  3. Centros poblados -- tabla con enlace a la ficha censal y descargas
                    (CSV, Excel, GeoJSON) del ámbito filtrado.
  4. Diccionario -- las 110 variables.

Los datos vienen de geoperu_ccpp/unir.py -> preparar_datos.py.

Correr con:
    streamlit run app.py
"""

from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from scripts import indicadores as ind  # noqa: E402
from scripts import styles  # noqa: E402

APP_NAME = "Llaqta"
APP_TAGLINE = "Centros poblados · Censo 2025"
APP_VERSION = "0.1.0"
FUENTE = ("INEI, Censos Nacionales 2025, capas de centros poblados publicadas en GEOPERÚ "
          "(visor.geoperu.gob.pe), descargadas el 21/10/2026.")

st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🏘️")
styles.inject()

IDENTIDAD = ["codigo_ccpp", "nombccpp", "nombdist", "nombprov", "nombdep", "area_ambito_texto",
             "poblacion_censada", "lon", "lat"]
NOMBRES = {"codigo_ccpp": "Código CP", "nombccpp": "Centro poblado", "nombdist": "Distrito",
           "nombprov": "Provincia", "nombdep": "Departamento", "area_ambito_texto": "Ámbito",
           "poblacion_censada": "Población", "url_reporte": "Ficha censal", "lon": "Longitud", "lat": "Latitud"}
MAX_PESADOS = 15000  # tope de CP para Excel / GeoJSON (memoria de Streamlit Cloud)


# ------------------------------------------------------------ datos

@st.cache_data(show_spinner="Cargando centros poblados…")
def cargar() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_parquet(BASE_DIR / "data" / "ccpp_censo2025.parquet")
    dicc = pd.read_csv(BASE_DIR / "data" / "diccionario_variables.csv", encoding="utf-8-sig")
    return df, dicc


def opciones(serie: pd.Series) -> list[str]:
    return sorted(serie.dropna().astype(str).unique())


def formato_num(v: float | int | None, dec: int = 0) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{v:,.{dec}f}".replace(",", " ")


def formato_pct(v: float | None) -> str:
    return "—" if v is None or math.isnan(v) else f"{v:.1f} %"


# ------------------------------------------------------------ sidebar

def sidebar(df: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    with st.sidebar:
        st.markdown(
            f'<div class="ll-brand"><div class="ll-brand-mark">L</div>'
            f'<div><strong>{APP_NAME}</strong><small>{APP_TAGLINE}</small></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("### Ámbito")
        deps = st.multiselect("Departamento", opciones(df["nombdep"]), placeholder="Todo el Perú")
        sub = df[df["nombdep"].isin(deps)] if deps else df
        provs = st.multiselect("Provincia", opciones(sub["nombprov"]), placeholder="Todas")
        sub = sub[sub["nombprov"].isin(provs)] if provs else sub
        dists = st.multiselect("Distrito", opciones(sub["nombdist"]), placeholder="Todos")
        sub = sub[sub["nombdist"].isin(dists)] if dists else sub

        ambito = st.radio("Ámbito censal", ["Todos", "Urbano", "Rural"], horizontal=True)
        if ambito != "Todos":
            sub = sub[sub["area_ambito_texto"] == ambito]
        con_poblacion = st.checkbox("Solo CP con población censada", value=True,
                                    help="9 901 CP figuran con 0 habitantes y sin datos de vivienda u hogar.")
        if con_poblacion:
            sub = sub[sub["poblacion_censada"] > 0]
        pob_min = st.number_input("Población mínima", min_value=0, value=0, step=50)
        if pob_min:
            sub = sub[sub["poblacion_censada"] >= pob_min]
        buscar = st.text_input("Buscar centro poblado", placeholder="Nombre o parte del nombre")
        if buscar.strip():
            sub = sub[sub["nombccpp"].str.contains(buscar.strip(), case=False, na=False, regex=False)]

        st.markdown("### Indicador")
        grupos = ind.por_grupo()
        grupo = st.selectbox("Tema", list(grupos))
        clave = st.selectbox("Indicador", grupos[grupo], format_func=ind.etiqueta)

        nivel = "nombdist" if (provs or dists) else "nombprov" if deps else "nombdep"
        st.markdown(f'<p class="ll-nota">Fuente: {FUENTE}<br>Llaqta v{APP_VERSION}</p>', unsafe_allow_html=True)
    return sub, clave, nivel


# ------------------------------------------------------------ vistas

def color_por_valor(valores: pd.Series, mas_es_mejor: bool) -> np.ndarray:
    """Rojo -> ámbar -> verde según el %; gris si no hay dato."""
    v = valores.to_numpy(dtype="float64") / 100
    v = v if mas_es_mejor else 1 - v
    rojo, ambar, verde = np.array([229, 72, 77]), np.array([238, 157, 14]), np.array([18, 166, 107])
    t = np.clip(np.nan_to_num(v, nan=0), 0, 1)[:, None]
    rgb = np.where(t < .5, rojo + (ambar - rojo) * (t / .5), ambar + (verde - ambar) * ((t - .5) / .5))
    rgb[np.isnan(v)] = [150, 160, 168]
    return np.c_[rgb, np.full(len(v), 200)].astype(int)


def vista_mapa(df: pd.DataFrame, clave: str) -> None:
    etiqueta, _, _, mas_es_mejor = ind.INDICADORES[clave]
    if df.empty:
        st.info("No hay centros poblados con esos filtros.")
        return
    puntos = df[["nombccpp", "nombdist", "nombprov", "nombdep", "poblacion_censada", "lon", "lat",
                 f"pct_{clave}"]].copy()
    puntos["color"] = color_por_valor(puntos[f"pct_{clave}"], mas_es_mejor).tolist()
    puntos["radio"] = np.sqrt(puntos["poblacion_censada"].clip(lower=1)) * 12
    puntos["valor"] = puntos[f"pct_{clave}"].map(formato_pct)
    puntos["pob"] = puntos["poblacion_censada"].map(formato_num)

    lon_min, lat_min, lon_max, lat_max = (puntos["lon"].min(), puntos["lat"].min(),
                                          puntos["lon"].max(), puntos["lat"].max())
    extension = max(lon_max - lon_min, (lat_max - lat_min) * 1.3, 0.02)
    zoom = float(np.clip(math.log2(360 / extension) - 1.2, 3.8, 13))
    vista = pdk.ViewState(longitude=(lon_min + lon_max) / 2, latitude=(lat_min + lat_max) / 2, zoom=zoom)
    capa = pdk.Layer("ScatterplotLayer", data=puntos, get_position=["lon", "lat"], get_fill_color="color",
                     get_radius="radio", radius_min_pixels=2, radius_max_pixels=28, pickable=True,
                     stroked=True, get_line_color=[255, 255, 255, 120], line_width_min_pixels=0.5)
    tooltip = {"html": "<b>{nombccpp}</b><br>{nombdist}, {nombprov}, {nombdep}<br>"
                       f"Población: {{pob}}<br>{etiqueta}: <b>{{valor}}</b>",
               "style": {"backgroundColor": "#002935", "color": "white", "fontSize": "12px"}}
    st.pydeck_chart(pdk.Deck(layers=[capa], initial_view_state=vista, tooltip=tooltip, map_style="light"),
                    height=620)
    extremos = ("peor", "mejor") if mas_es_mejor else ("mejor", "peor")
    st.markdown(
        f'<div class="ll-leyenda"><span>0 % ({extremos[0]})</span><div class="barra"></div>'
        f'<span>100 % ({extremos[1]})</span><span>· tamaño = población · gris = sin dato</span></div>',
        unsafe_allow_html=True,
    )


def vista_resumen(df: pd.DataFrame, clave: str, nivel: str) -> None:
    etiqueta, _, _, mas_es_mejor = ind.INDICADORES[clave]
    c = st.columns(5)
    c[0].markdown(styles.kpi("Centros poblados", formato_num(len(df))), unsafe_allow_html=True)
    c[1].markdown(styles.kpi("Población censada", formato_num(df["poblacion_censada"].sum())), unsafe_allow_html=True)
    c[2].markdown(styles.kpi("Viviendas", formato_num(df[ind.VIV].sum()), tono="cyan"), unsafe_allow_html=True)
    c[3].markdown(styles.kpi("Hogares", formato_num(df[ind.HOG].sum()), tono="cyan"), unsafe_allow_html=True)
    valor = ind.agregado(df, clave) if len(df) else None
    c[4].markdown(styles.kpi(etiqueta, formato_pct(valor), "del ámbito filtrado",
                             tono="success" if mas_es_mejor else "warning"), unsafe_allow_html=True)
    if df.empty:
        return

    nombre_nivel = {"nombdep": "departamento", "nombprov": "provincia", "nombdist": "distrito"}[nivel]
    styles.titulo(f"{etiqueta} por {nombre_nivel}")
    tabla = ind.tabla_por(df, nivel, [clave]).dropna(subset=[etiqueta])
    tabla = tabla.sort_values(etiqueta, ascending=not mas_es_mejor)
    alto = min(30 + 18 * len(tabla), 900)
    grafico = alt.Chart(tabla).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X(f"{etiqueta}:Q", title="%", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y(f"{nivel}:N", sort=None, title=None),
        color=alt.Color(f"{etiqueta}:Q", legend=None, scale=alt.Scale(
            domain=[0, 50, 100], range=["#E5484D", "#EE9D0E", "#12A66B"] if mas_es_mejor
            else ["#12A66B", "#EE9D0E", "#E5484D"])),
        tooltip=[nivel, alt.Tooltip(f"{etiqueta}:Q", format=".1f"), "Centros poblados", "Población"],
    ).properties(height=alto)
    st.altair_chart(grafico, width="stretch")

    styles.titulo("Todos los indicadores del ámbito")
    filas = []
    for grupo, claves in ind.por_grupo().items():
        for k in claves:
            filas.append({"Tema": grupo, "Indicador": ind.etiqueta(k), "Ámbito filtrado (%)": ind.agregado(df, k)})
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch", height=560,
                 column_config={"Ámbito filtrado (%)": st.column_config.ProgressColumn(
                     format="%.1f", min_value=0, max_value=100)})


def geojson_bytes(df: pd.DataFrame) -> bytes:
    props = df.drop(columns=["lon", "lat"]).astype(object).where(df.drop(columns=["lon", "lat"]).notna(), None)
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(x, 6), round(y, 6)]},
              "properties": p} for x, y, p in zip(df["lon"], df["lat"], props.to_dict("records"))]
    return json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False).encode("utf-8")


def vista_tabla(df: pd.DataFrame, clave: str) -> None:
    if df.empty:
        st.info("No hay centros poblados con esos filtros.")
        return
    todos = list(ind.INDICADORES)
    elegidos = st.multiselect("Indicadores a mostrar (%)", todos, default=[clave], format_func=ind.etiqueta)
    orden = st.radio("Ordenar por el primer indicador", ["Mayor población", "Peor valor", "Mejor valor"],
                     horizontal=True)
    vista = df[IDENTIDAD[:-2] + ["url_reporte"] + [f"pct_{k}" for k in elegidos]].copy()
    if elegidos and orden != "Mayor población":
        mas_es_mejor = ind.INDICADORES[elegidos[0]][3]
        ascendente = (orden == "Peor valor") == mas_es_mejor
        vista = vista.sort_values(f"pct_{elegidos[0]}", ascending=ascendente, na_position="last")
    else:
        vista = vista.sort_values("poblacion_censada", ascending=False)
    config = {f"pct_{k}": st.column_config.NumberColumn(ind.etiqueta(k), format="%.1f %%") for k in elegidos}
    config["url_reporte"] = st.column_config.LinkColumn("Ficha censal", display_text="Ver ficha")
    config["poblacion_censada"] = st.column_config.NumberColumn("Población", format="%d")
    st.caption(f"{len(vista):,} centros poblados".replace(",", " "))
    st.dataframe(vista.rename(columns={k: v for k, v in NOMBRES.items() if k not in config}),
                 hide_index=True, width="stretch", height=520, column_config=config)

    styles.titulo("Descargar el ámbito filtrado (todas las variables)")
    formato = st.radio("Formato", ["CSV", "Excel", "GeoJSON"], horizontal=True)
    firma = (formato, len(df), int(df["poblacion_censada"].sum()), df["codigo_ccpp"].iloc[0])
    if formato != "CSV" and len(df) > MAX_PESADOS:
        st.info(f"Excel y GeoJSON están disponibles hasta {MAX_PESADOS:,} centros poblados".replace(",", " ")
                + " (el nacional en GeoJSON pesa ~290 MB). Filtra por departamento o provincia, o descarga en CSV.")
        return
    if st.button("Preparar archivo", type="primary"):
        with st.spinner("Generando archivo…"):
            if formato == "CSV":
                datos, mime, ext = df.to_csv(index=False).encode("utf-8-sig"), "text/csv", "csv"
            elif formato == "Excel":
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as xl:
                    df.to_excel(xl, sheet_name="ccpp", index=False)
                    cargar()[1].to_excel(xl, sheet_name="diccionario", index=False)
                datos, ext = buf.getvalue(), "xlsx"
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                datos, mime, ext = geojson_bytes(df), "application/geo+json", "geojson"
        st.session_state["descarga"] = (firma, datos, mime, ext)
    descarga = st.session_state.get("descarga")
    if descarga and descarga[0] == firma:
        _, datos, mime, ext = descarga
        st.download_button(f"Descargar {formato} ({len(datos) / 1e6:.1f} MB)", datos,
                           file_name=f"ccpp_censo2025.{ext}", mime=mime)


def vista_diccionario(dicc: pd.DataFrame) -> None:
    st.dataframe(dicc[["variable", "etiqueta", "capa_origen", "tipo", "nulos"]], hide_index=True,
                 width="stretch", height=640)
    st.caption("Los porcentajes de un ámbito se recalculan como suma(n) / suma(universo); "
               "no se promedian los % de cada centro poblado.")


# ------------------------------------------------------------ main

def main() -> None:
    df, dicc = cargar()
    sub, clave, nivel = sidebar(df)
    st.markdown(
        f'<div class="ll-header"><h1>{APP_NAME}</h1>'
        f'<p>Indicadores de vivienda y hogar de los centros poblados del Perú · Censo 2025</p></div>',
        unsafe_allow_html=True,
    )
    mapa, resumen, tabla, diccionario = st.tabs(["Mapa", "Resumen", "Centros poblados", "Diccionario"])
    with mapa:
        vista_mapa(sub, clave)
    with resumen:
        vista_resumen(sub, clave, nivel)
    with tabla:
        vista_tabla(sub, clave)
    with diccionario:
        vista_diccionario(dicc)


main()
