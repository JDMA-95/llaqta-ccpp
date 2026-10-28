# -*- coding: utf-8 -*-
"""
Paleta e inyección de estilos de Llaqta. Mismo lenguaje visual que Gea y
Ceque (navy #004764 + cyan #1AAFE2), con el prefijo de clases `ll-`.
"""

from __future__ import annotations

import html

import streamlit as st

CSS = """
<style>
:root {
    --bg: #f3f6f8; --surface: #ffffff; --surface-2: #eef3f6; --ink: #0f1b22; --muted: #66767f;
    --line: #dde5ea; --navy: #004764; --navy-deep: #002935; --cyan: #1AAFE2; --cyan-soft: #e3f6fd;
    --success: #12A66B; --success-soft: #e5f7ee; --danger: #E5484D; --danger-soft: #fdecec;
    --warning: #EE9D0E; --warning-soft: #fdf1dc;
}
.stApp { background: var(--bg); }
[data-testid="stSidebar"] { background: linear-gradient(175deg, var(--navy) 0%, var(--navy-deep) 100%); }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] small,
[data-testid="stSidebar"] .ll-brand, [data-testid="stSidebar"] h3 { color: #e7f1f5 !important; }
[data-testid="stSidebar"] .ll-brand {
    display: flex; gap: 10px; align-items: center; padding: 4px 2px 18px;
    border-bottom: 1px solid rgba(255,255,255,.12); margin-bottom: 14px;
}
[data-testid="stSidebar"] .ll-brand-mark {
    width: 38px; height: 38px; border-radius: 11px; display: grid; place-items: center; flex: none;
    background: linear-gradient(135deg, var(--cyan) 0%, #6fd4f5 100%);
    font-weight: 800; color: var(--navy-deep) !important; font-size: 18px;
}
[data-testid="stSidebar"] .ll-brand strong { display: block; font-size: 16px; font-weight: 800; }
[data-testid="stSidebar"] .ll-brand small { display: block; color: #a9c6d3 !important; font-size: 11.5px; }
[data-testid="stSidebar"] .ll-nota { font-size: 11.5px; color: #a9c6d3 !important; line-height: 1.45; }
[data-testid="stSidebar"] .ll-nota a { color: #6fd4f5 !important; }

.ll-kpi {
    background: var(--surface); border: 1px solid var(--line); border-radius: 16px;
    padding: 14px 16px; position: relative; overflow: hidden; box-shadow: 0 2px 8px rgba(9,30,40,.06);
    margin-bottom: 10px;
}
.ll-kpi::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--accent); }
.ll-kpi .label { display: block; color: var(--muted); font-weight: 600; font-size: 12.5px; }
.ll-kpi strong { display: block; margin: 4px 0 2px; font-size: 26px; font-weight: 800; color: var(--ink); }
.ll-kpi .caption { display: block; color: var(--muted); font-size: 12px; }
.ll-section-title { font-size: 13px; font-weight: 800; color: var(--navy); text-transform: uppercase;
    letter-spacing: .04em; margin: 10px 0 8px; }
.ll-header h1 { font-size: 26px; font-weight: 800; color: var(--ink); margin: 0; }
.ll-header p { color: var(--muted); margin: 2px 0 12px; }
.ll-leyenda { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--muted); margin: 4px 0 10px; }
.ll-leyenda .barra { height: 10px; width: 180px; border-radius: 999px;
    background: linear-gradient(90deg, #E5484D, #EE9D0E, #12A66B); }
</style>
"""

ACENTOS = {
    "navy": ("var(--navy)", "var(--cyan-soft)"),
    "cyan": ("var(--cyan)", "var(--cyan-soft)"),
    "success": ("var(--success)", "var(--success-soft)"),
    "danger": ("var(--danger)", "var(--danger-soft)"),
    "warning": ("var(--warning)", "var(--warning-soft)"),
}


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def kpi(label: str, valor: str, caption: str = "", tono: str = "navy") -> str:
    acento, suave = ACENTOS[tono]
    return (
        f'<div class="ll-kpi" style="--accent:{acento};--accent-soft:{suave}">'
        f'<span class="label">{html.escape(label)}</span><strong>{html.escape(valor)}</strong>'
        f'<span class="caption">{html.escape(caption)}</span></div>'
    )


def titulo(texto: str) -> None:
    st.markdown(f'<div class="ll-section-title">{html.escape(texto)}</div>', unsafe_allow_html=True)
