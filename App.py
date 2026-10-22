"""
Tablero Scrum interactivo
Proyecto: Sistema inteligente para la gestión de turnos y predicción de tiempos
de espera en establecimientos de salud públicos mediante Machine Learning.
Curso: Tecnologías Emergentes

Ejecutar con:  streamlit run app.py
"""

import html
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------
# Configuración general
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Tablero Scrum · Gestión de turnos en salud",
    page_icon="🏥",
    layout="wide",
)

ESTADOS = ["Por hacer", "En curso", "Hecho"]
MIEMBROS = [
    "Castilla Quiroz, Jahir Daniel",
    "Llanos Castillo, Diego Alonso",
    "Medina Torres, Ryan Patrick",
    "Silvera Alegría, Andrea Lucia",
    "Quispe Bartolo, Carlos Martin",
    "Villar Rosado, Maylor Mark",
]
ARCHIVO_DATOS = Path("datos_tablero.json")  # guarda el avance entre recargas
ZONA = ZoneInfo("America/Lima")

# Colores por estado (fondo, texto)
COLORES = {
    "Por hacer": ("#E8EDF2", "#3B4B5C"),
    "En curso": ("#FFF1D6", "#8A5A00"),
    "Hecho": ("#D9F2E6", "#14633F"),
}

HISTORIAS = [
    ("HU-01", "Como paciente, quiero registrar mi llegada y especialidad en el sistema, para iniciar el control de mi turno.", 1, 5),
    ("HU-02", "Como administrador del hospital, quiero que el sistema genere datos sintéticos calibrados con ENSUSALUD, para simular escenarios reales de atención.", 1, 8),
    ("HU-03", "Como sistema, quiero predecir el tiempo de espera estimado mediante Random Forest, para informar al paciente y al personal.", 2, 8),
    ("HU-04", "Como gestor de salud, quiero visualizar los turnos y métricas en un dashboard en la nube, para observar el flujo en tiempo real.", 2, 8),
    ("HU-05", "Como desarrollador, quiero evaluar el modelo predictivo con métricas de rendimiento, para asegurar la calidad de la predicción.", 3, 5),
    ("HU-06", "Como investigador, quiero comparar el rendimiento de Random Forest frente a un modelo base de promedio móvil, para medir la mejora obtenida.", 3, 3),
    ("HU-07", "Como operador del sistema, quiero almacenar los datos de turnos en Amazon RDS y los archivos en Amazon S3, para una gestión escalable.", 4, 5),
    ("HU-08", "Como analista, quiero simular escenarios de alta demanda (1,5 y 2 veces el flujo habitual), para comprobar la robustez del sistema.", 4, 5),
    ("HU-09", "Como usuario del sistema, quiero ver el desglose de los consultorios activos y la cantidad de personas en cola, para entender la situación actual del servicio.", 5, 3),
    ("HU-10", "Como administrador, quiero verificar que la disponibilidad del dashboard en la nube supere el 95% durante las pruebas, para garantizar su fiabilidad operativa.", 5, 3),
]
CATALOGO = {
    codigo: {"descripcion": desc, "prioridad": prio, "sp": sp}
    for codigo, desc, prio, sp in HISTORIAS
}
CODIGOS = list(CATALOGO.keys())


# ----------------------------------------------------------------------------
# Estado y persistencia
# ----------------------------------------------------------------------------
def estado_inicial():
    return {
        "estados": {c: 0 for c in CODIGOS},
        "responsables": {c: None for c in CODIGOS},
        "bitacora": [],
        "siguiente_id": 1,
    }


def cargar():
    if ARCHIVO_DATOS.exists():
        try:
            datos = json.loads(ARCHIVO_DATOS.read_text(encoding="utf-8"))
            if set(datos["estados"]) == set(CODIGOS):
                # compatibilidad con archivos guardados antes de existir el responsable
                datos.setdefault("responsables", {c: None for c in CODIGOS})
                return datos
        except (json.JSONDecodeError, KeyError, OSError):
            pass
    return estado_inicial()


def guardar():
    datos = {
        "estados": st.session_state.estados,
        "responsables": st.session_state.responsables,
        "bitacora": st.session_state.bitacora,
        "siguiente_id": st.session_state.siguiente_id,
    }
    try:
        ARCHIVO_DATOS.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        pass  # si el servidor no permite escribir, la app sigue en memoria


if "estados" not in st.session_state:
    datos = cargar()
    st.session_state.estados = datos["estados"]
    st.session_state.responsables = datos["responsables"]
    st.session_state.bitacora = datos["bitacora"]
    st.session_state.siguiente_id = datos["siguiente_id"]
if "aviso" not in st.session_state:
    st.session_state.aviso = None


def avanzar(codigo: str, nota: str, responsable: str | None = None):
    """Pasa la historia al estado siguiente y registra la nota.
    Si sale de «Por hacer», también fija el responsable (no se puede cambiar después)."""
    actual = st.session_state.estados[codigo]
    st.session_state.estados[codigo] = actual + 1
    if actual == 0 and responsable:
        st.session_state.responsables[codigo] = responsable
    st.session_state.bitacora.append(
        {
            "id": st.session_state.siguiente_id,
            "historia": codigo,
            "desde": ESTADOS[actual],
            "hacia": ESTADOS[actual + 1],
            "nota": nota.strip(),
            "responsable": responsable if actual == 0 else None,
            "fecha": datetime.now(ZONA).strftime("%d/%m/%Y %H:%M"),
        }
    )
    st.session_state.siguiente_id += 1
    guardar()


def retroceder(codigo: str):
    """Revierte el último avance de la historia y borra su nota de la bitácora.
    Al volver a «Por hacer» también se libera el responsable para poder reasignarlo."""
    actual = st.session_state.estados[codigo]
    st.session_state.estados[codigo] = actual - 1
    if actual - 1 == 0:
        st.session_state.responsables[codigo] = None
    for i in range(len(st.session_state.bitacora) - 1, -1, -1):
        if st.session_state.bitacora[i]["historia"] == codigo:
            del st.session_state.bitacora[i]
            break
    guardar()


def notas_de(codigo: str):
    return [n for n in st.session_state.bitacora if n["historia"] == codigo]


# ----------------------------------------------------------------------------
# Estilos
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=Source+Serif+4:wght@600;700&display=swap');

    html, body, [class*="css"], .stMarkdown, .stButton button, .stTextArea textarea {
        font-family: 'Source Sans 3', sans-serif;
    }
    .block-container { padding-top: 5rem; max-width: 1200px; }

    .titulo {
        font-family: 'Source Serif 4', serif;
        font-size: 2rem; font-weight: 700; color: inherit;
        margin: 0; line-height: 1.3; padding-top: .25rem;
    }
    .subtitulo { color: inherit; opacity: .75; margin: .35rem 0 1.25rem 0; font-size: 1.02rem; }

    .kanban { width: 100%; border-collapse: collapse; background: #fff;
              border: 1px solid #D5DEE4; border-radius: 10px; overflow: hidden; }
    .kanban th { background: #0F3D4C; color: #fff; padding: .7rem .9rem;
                 font-weight: 600; text-align: center; }
    .kanban th:first-child { text-align: left; }
    .kanban td { padding: .6rem .9rem; border-top: 1px solid #E4EAEE;
                 text-align: center; color: #1D2B33; }
    .kanban td.hu { text-align: left; font-weight: 600; white-space: nowrap; }
    .kanban td.resumen { text-align: left; color: #4A6572; font-size: .92rem; }
    .kanban td.resp { text-align: left; font-size: .9rem; white-space: nowrap; }
    .responsable { color: inherit; font-weight: 700; }
    .kanban td.marca { font-weight: 700; font-size: 1.15rem; }
    .kanban td.m-0 { background: #E8EDF2; color: #3B4B5C; }
    .kanban td.m-1 { background: #FFF1D6; color: #8A5A00; }
    .kanban td.m-2 { background: #D9F2E6; color: #14633F; }

    .badge { display: inline-block; padding: .15rem .65rem; border-radius: 999px;
             font-size: .82rem; font-weight: 600; }
    .historia { border: 1px solid #D5DEE4; border-left: 5px solid #0F3D4C;
                background: #fff; border-radius: 8px; padding: 1rem 1.2rem;
                margin-bottom: .4rem; }
    .historia .cab { display: flex; justify-content: space-between;
                     align-items: center; gap: .5rem; flex-wrap: wrap; }
    .historia .cod { font-family: 'Source Serif 4', serif; font-weight: 700;
                     font-size: 1.15rem; color: #0F3D4C; }
    .historia .meta { color: #4A6572; font-size: .88rem; margin: .2rem 0 .5rem 0; }
    .historia .desc { color: #1D2B33; line-height: 1.5; }
    .nota { border-left: 3px solid #9DB4C0; margin: .35rem 0 .35rem 1rem;
            padding: .3rem .8rem; background: #F5F8FA; border-radius: 0 6px 6px 0;
            color: #1D2B33; font-size: .94rem; }
    .nota .fecha { color: #6A8290; font-size: .82rem; }
    .vacio { color: #6A8290; font-style: italic; margin: .3rem 0 .8rem 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Encabezado y métricas
# ----------------------------------------------------------------------------
st.markdown(
    '<p class="titulo">Tablero Scrum · Gestión de turnos en salud</p>'
    '<p class="subtitulo">Sistema inteligente para la gestión de turnos y predicción de '
    "tiempos de espera en establecimientos de salud públicos mediante Machine Learning</p>",
    unsafe_allow_html=True,
)

total_sp = sum(h["sp"] for h in CATALOGO.values())
sp_hechos = sum(CATALOGO[c]["sp"] for c in CODIGOS if st.session_state.estados[c] == 2)
n_por_hacer = sum(1 for c in CODIGOS if st.session_state.estados[c] == 0)
n_en_curso = sum(1 for c in CODIGOS if st.session_state.estados[c] == 1)
n_hechas = sum(1 for c in CODIGOS if st.session_state.estados[c] == 2)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Por hacer", n_por_hacer)
m2.metric("En curso", n_en_curso)
m3.metric("Hechas", n_hechas)
m4.metric("Story Points completados", f"{sp_hechos} / {total_sp}")
st.progress(sp_hechos / total_sp, text=f"Avance del proyecto: {sp_hechos / total_sp:.0%}")

tab_tablero, tab_detalle = st.tabs(["📋 Tablero de control", "📖 Detalle y bitácora"])

# ----------------------------------------------------------------------------
# Pestaña 1: Tablero de control
# ----------------------------------------------------------------------------
with tab_tablero:
    filas = ""
    for c in CODIGOS:
        idx = st.session_state.estados[c]
        celdas = ""
        for i in range(3):
            if i == idx:
                celdas += f'<td class="marca m-{i}">X</td>'
            else:
                celdas += "<td></td>"
        resumen = html.escape(CATALOGO[c]["descripcion"].split(", quiero ")[-1].split(", para")[0])
        resp = st.session_state.responsables.get(c)
        resp_html = html.escape(resp) if resp else '<span style="opacity:.5">Sin asignar</span>'
        filas += (
            f'<tr><td class="hu">{c}</td>'
            f'<td class="resumen">Quiero {resumen}</td>'
            f'<td class="resp">{resp_html}</td>{celdas}</tr>'
        )
    st.markdown(
        f"""
        <table class="kanban">
          <thead><tr><th>Historia</th><th style="text-align:left">Objetivo</th>
          <th style="text-align:left">Responsable</th>
          <th>Por hacer</th><th>En curso</th><th>Hecho</th></tr></thead>
          <tbody>{filas}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Actualizar una historia")

    if st.session_state.aviso:
        tipo, texto = st.session_state.aviso
        (st.success if tipo == "ok" else st.warning)(texto)
        st.session_state.aviso = None

    col_sel, col_info = st.columns([1, 2])
    with col_sel:
        codigo = st.selectbox(
            "Historia de usuario",
            CODIGOS,
            format_func=lambda c: f"{c} · Prioridad {CATALOGO[c]['prioridad']} · {CATALOGO[c]['sp']} SP",
        )
    idx_actual = st.session_state.estados[codigo]
    fondo, texto_color = COLORES[ESTADOS[idx_actual]]
    with col_info:
        st.markdown(
            f"<div style='padding-top:1.9rem'>Estado actual: "
            f"<span class='badge' style='background:{fondo};color:{texto_color}'>"
            f"{ESTADOS[idx_actual]}</span></div>",
            unsafe_allow_html=True,
        )
    st.caption(CATALOGO[codigo]["descripcion"])

    responsable_actual = st.session_state.responsables.get(codigo)
    if responsable_actual:
        st.markdown(
            f"Responsable: <span class='responsable'>{html.escape(responsable_actual)}</span>",
            unsafe_allow_html=True,
        )
        st.caption(
            "El responsable queda fijo mientras la historia esté en curso o hecha. "
            "Para cambiarlo, deshaz hasta «Por hacer» y asígnalo de nuevo."
        )

    col_avanzar, col_deshacer = st.columns([3, 1], gap="large")

    # --- Avanzar (con responsable al salir de «Por hacer» y nota obligatoria) ---
    with col_avanzar:
        if idx_actual < 2:
            siguiente = ESTADOS[idx_actual + 1]
            with st.form(f"form_avanzar_{codigo}_{idx_actual}", clear_on_submit=True):
                elegido = None
                if idx_actual == 0:
                    elegido = st.selectbox(
                        "Responsable de la historia",
                        MIEMBROS,
                        index=None,
                        placeholder="Selecciona un integrante del grupo…",
                    )
                etiqueta = (
                    "¿Qué se va a hacer para resolver esta historia?"
                    if siguiente == "En curso"
                    else "¿Qué se hizo para resolver esta historia?"
                )
                nota = st.text_area(etiqueta, placeholder="Escribe una nota breve del avance…", height=100)
                enviar = st.form_submit_button(
                    f"Mover a «{siguiente}»", type="primary", use_container_width=True
                )
            if enviar:
                if idx_actual == 0 and not elegido:
                    st.warning("Selecciona un responsable antes de pasar a «En curso».")
                elif not nota.strip():
                    st.warning("Escribe una nota antes de cambiar el estado.")
                else:
                    avanzar(codigo, nota, elegido)
                    st.session_state.aviso = ("ok", f"{codigo} pasó a «{siguiente}».")
                    st.rerun()
        else:
            st.success(f"{codigo} ya está en «Hecho». No hay más estados por avanzar.")

    # --- Deshacer ---
    with col_deshacer:
        st.markdown("<div style='height:.2rem'></div>", unsafe_allow_html=True)
        st.write("¿Te equivocaste al avanzar?")
        if idx_actual > 0:
            anterior = ESTADOS[idx_actual - 1]
            if st.button(f"Deshacer y volver a «{anterior}»", use_container_width=True):
                retroceder(codigo)
                extra = " El responsable quedó libre para asignarlo de nuevo." if anterior == "Por hacer" else ""
                st.session_state.aviso = (
                    "warn",
                    f"{codigo} volvió a «{anterior}» y su nota fue eliminada de la bitácora.{extra}",
                )
                st.rerun()
        else:
            st.button("Nada que deshacer", disabled=True, use_container_width=True)

    with st.expander("Reiniciar todo el tablero"):
        st.write("Esto devuelve las 10 historias a «Por hacer» y borra toda la bitácora.")
        confirmar = st.checkbox("Entiendo que esta acción no se puede deshacer")
        if st.button("Reiniciar tablero", disabled=not confirmar):
            base = estado_inicial()
            st.session_state.estados = base["estados"]
            st.session_state.responsables = base["responsables"]
            st.session_state.bitacora = base["bitacora"]
            st.session_state.siguiente_id = base["siguiente_id"]
            guardar()
            st.rerun()

# ----------------------------------------------------------------------------
# Pestaña 2: Detalle de historias y bitácora
# ----------------------------------------------------------------------------
with tab_detalle:
    filtro = st.radio(
        "Mostrar historias en estado",
        ["Todas"] + ESTADOS,
        horizontal=True,
    )

    mostradas = 0
    for c in CODIGOS:
        idx = st.session_state.estados[c]
        if filtro != "Todas" and ESTADOS[idx] != filtro:
            continue
        mostradas += 1
        fondo, texto_color = COLORES[ESTADOS[idx]]
        h = CATALOGO[c]
        resp = st.session_state.responsables.get(c)
        resp_txt = html.escape(resp) if resp else "Sin asignar"
        st.markdown(
            f"""
            <div class="historia">
              <div class="cab">
                <span class="cod">{c}</span>
                <span class="badge" style="background:{fondo};color:{texto_color}">{ESTADOS[idx]}</span>
              </div>
              <div class="meta">Prioridad {h['prioridad']} &nbsp;|&nbsp; {h['sp']} Story Points
                &nbsp;|&nbsp; Responsable: <b>{resp_txt}</b></div>
              <div class="desc">{html.escape(h['descripcion'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        notas = notas_de(c)
        if notas:
            for n in notas:
                st.markdown(
                    f"<div class='nota'><span class='fecha'>{n['fecha']} · "
                    f"{n['desde']} ➔ {n['hacia']}</span><br>{html.escape(n['nota'])}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<div class='vacio'>Aún no hay notas de avance para esta historia.</div>",
                unsafe_allow_html=True,
            )
        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    if mostradas == 0:
        st.info(f"No hay historias en «{filtro}» por ahora.")

    if st.session_state.bitacora:
        st.markdown("### Bitácora completa")
        df = pd.DataFrame(st.session_state.bitacora).reindex(
            columns=["fecha", "historia", "responsable", "desde", "hacia", "nota"]
        ).rename(
            columns={
                "fecha": "Fecha",
                "historia": "Historia",
                "responsable": "Responsable asignado",
                "desde": "Desde",
                "hacia": "Hacia",
                "nota": "Nota",
            }
        )
        st.dataframe(df.iloc[::-1], hide_index=True, use_container_width=True)
