"""Cubo semántico -- Stand de Ingeniería Estadística, ConexIA 2026.

Flujo: el visitante elige su deporte, responde 3 preguntas de opinión, y
cada respuesta se convierte en un punto del Diagrama de Opiniones.
Las posiciones y clústeres quedan congelados desde build_seed_space/
fit_projection.py -- esta app nunca reentrena nada, solo consulta el
pipeline y guarda respuestas nuevas en data/visitantes.sqlite.

Los elementos decorativos (tarjetas de estadísticas, leyenda de colores)
se construyen con HTML/CSS propio en vez de depender del theming nativo
de Streamlit, para tener control total sobre cómo se ven. Los widgets
interactivos (botones, pills, texto, el gráfico) sí son nativos.

Para el siguiente aspirante en el stand: no hay botón de reinicio a
propósito -- el anfitrión solo refresca el navegador (F5), eso le da a
Streamlit una sesión nueva desde cero.

Corre con: streamlit run app.py
"""
from __future__ import annotations

import textwrap
import uuid
from collections import defaultdict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pipeline import storage
from pipeline.clustering import assign_cluster
from pipeline.embeddings import encode
from pipeline.projection import get_variance_explained, transform_to_3d
from pipeline.questions import QUESTIONS
from pipeline.sports import MAX_CUSTOM_SPORT_LENGTH, OTHER_SPORT_LABEL, SPORTS, normalize_sport_name
from pipeline.visual_encoding import CATEGORICAL_PALETTE, OTHER_COLOR, PREGUNTA_TO_SHAPE, get_color_for_cluster

MIN_ANSWER_LENGTH = 10
MAX_HOVER_CHARS = 140


def inject_style() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800&family=Inter:wght@400;600&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        h1, h2, h3, h4 { font-family: 'Montserrat', sans-serif; }
        #MainMenu, footer, header { visibility: hidden; }
        .info-box-icon {
            font-family: 'Material Symbols Outlined';
            font-size: 22px;
            line-height: 1;
            vertical-align: middle;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#1976d2,#0d47a1);
                    padding:1.5rem 1.75rem;border-radius:14px;margin-bottom:1.5rem;">
            <div style="font-family:'Montserrat',sans-serif;font-weight:800;
                        font-size:1.8rem;color:#ffffff;letter-spacing:-0.01em;">
                DATA SPORT
            </div>
            <div style="font-family:'Montserrat',sans-serif;font-weight:700;
                        font-size:0.72rem;letter-spacing:0.18em;text-transform:uppercase;
                        color:#fec330;margin-top:2px;">
                ConexIA · Ingeniería Estadística · IA en acción
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_card(label: str, value: str, gradient: str, text_color: str, label_color: str) -> None:
    st.markdown(
        f"""
        <div style="background:{gradient};border-radius:12px;padding:1rem 1.25rem;text-align:center;">
            <div style="color:{label_color};font-size:0.72rem;font-weight:700;
                        letter-spacing:0.08em;text-transform:uppercase;">{label}</div>
            <div style="color:{text_color};font-size:2rem;font-weight:800;
                        font-family:'Montserrat',sans-serif;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_box(title: str, body: str, bg: str, title_color: str, icon: str) -> None:
    st.markdown(
        f"""
        <div style="background:{bg};border-radius:10px;padding:1rem 1.1rem;min-height:190px;
                    box-sizing:border-box;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.5rem;">
                <span class="info-box-icon" style="color:{title_color};">{icon}</span>
                <span style="font-weight:800;color:{title_color};
                            font-family:'Montserrat',sans-serif;">{title}</span>
            </div>
            <div style="font-size:0.85rem;color:#40493d;line-height:1.4;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_interpretation() -> None:
    st.subheader("Cómo leer el diagrama", divider="blue")
    col_forma, col_color, col_cercania = st.columns(3)
    with col_forma:
        render_info_box(
            "Forma",
            '<span style="display:inline-block;width:11px;height:11px;background:#1976d2;'
            'border-radius:50%;margin-right:6px;"></span>Pregunta 1<br>'
            '<span style="display:inline-block;width:11px;height:11px;background:#1976d2;'
            'margin-right:6px;"></span>Pregunta 2<br>'
            '<span style="display:inline-block;width:11px;height:11px;background:#1976d2;'
            'transform:rotate(45deg);margin-right:6px;"></span>Pregunta 3',
            bg="#eaf2fb",
            title_color="#1976d2",
            icon="interests",
        )
    with col_color:
        swatches = "".join(
            f'<span style="display:inline-block;width:16px;height:16px;border-radius:50%;'
            f'background:{c["light"]};margin-right:4px;"></span>'
            for c in CATEGORICAL_PALETTE[:5]
        )
        render_info_box(
            "Color",
            f'<div style="margin-bottom:0.5rem;">{swatches}</div>'
            "Cada color agrupa opiniones que el modelo encontró parecidas entre sí. "
            "Nadie le dio esas reglas, las descubrió solo.",
            bg="#fff4de",
            title_color="#795900",
            icon="palette",
        )
    with col_cercania:
        render_info_box(
            "Cercanía",
            "Los puntos que quedan cerca en el espacio son opiniones parecidas en significado, "
            "sin importar de qué deporte hablen.",
            bg="#e9f7ef",
            title_color="#0f6b3f",
            icon="hub",
        )


def init_session_state() -> None:
    if "visita_id" not in st.session_state:
        st.session_state.visita_id = str(uuid.uuid4())
    if "pregunta_actual" not in st.session_state:
        st.session_state.pregunta_actual = 1
    if "enviado" not in st.session_state:
        st.session_state.enviado = False
    if "balloons_shown" not in st.session_state:
        st.session_state.balloons_shown = False
    if "respuestas" not in st.session_state:
        # Guardadas aparte, en un dict plano -- no en el session_state de
        # cada widget. Streamlit borra el valor de un widget con key cuando
        # ese widget deja de dibujarse en una corrida (ej. la caja de la
        # pregunta 1 mientras se ve la 3), así que si dependemos solo de eso,
        # las respuestas anteriores "desaparecen" al llegar al final.
        st.session_state.respuestas = {1: "", 2: "", 3: ""}


def render_sport_selector() -> tuple[str | None, bool]:
    """Devuelve (deporte_elegido_o_None, cuestionario_bloqueado)."""
    with st.container(border=True):
        st.subheader("Antes de empezar", divider="blue")
        st.caption("¿Cuál es tu deporte favorito?")

        options = SPORTS + [OTHER_SPORT_LABEL]
        chosen = st.pills(
            "Deporte favorito",
            options,
            key="sport_pill",
            label_visibility="collapsed",
        )

        deporte: str | None = None
        if chosen:
            if chosen == OTHER_SPORT_LABEL:
                custom = st.text_input(
                    "Escribe tu deporte",
                    key="otro_deporte_input",
                    max_chars=MAX_CUSTOM_SPORT_LENGTH,
                    placeholder="Escribe tu deporte",
                    label_visibility="collapsed",
                )
                deporte = normalize_sport_name(custom) if custom.strip() else None
            else:
                deporte = chosen

    locked = deporte is None
    if locked:
        st.info("Elige tu deporte para continuar", icon=":material/arrow_downward:")
    return deporte, locked


def render_quiz(deporte: str | None, locked: bool) -> None:
    q_num = st.session_state.pregunta_actual

    with st.container(border=True):
        st.subheader("Cuéntanos", divider="blue")
        st.progress(q_num / 3)
        st.caption(f"Pregunta {q_num} de 3")

        st.markdown(f"#### {QUESTIONS[q_num]}")
        st.caption("Cuéntanos con tus palabras. No hay una respuesta correcta o incorrecta.")

        respuesta_actual = st.text_area(
            "Tu respuesta",
            value=st.session_state.respuestas[q_num],
            key=f"respuesta_widget_{q_num}",
            height=140,
            disabled=locked,
            placeholder="Escribe tu respuesta aquí...",
            label_visibility="collapsed",
        )
        st.session_state.respuestas[q_num] = respuesta_actual

        col_atras, col_siguiente = st.columns(2)
        with col_atras:
            atras = st.button(
                "Atrás",
                icon=":material/arrow_back:",
                disabled=locked or q_num == 1,
                use_container_width=True,
            )
        with col_siguiente:
            if q_num == 3:
                etiqueta, icono = "Terminar", ":material/check_circle:"
            else:
                etiqueta, icono = "Siguiente", ":material/arrow_forward:"
            siguiente = st.button(
                etiqueta,
                icon=icono,
                disabled=locked,
                use_container_width=True,
                type="primary",
            )

    if atras:
        st.session_state.pregunta_actual -= 1
        st.rerun()

    if siguiente:
        if len(respuesta_actual.strip()) < MIN_ANSWER_LENGTH:
            st.warning("Cuéntanos un poco más antes de continuar.", icon=":material/edit_note:")
        elif q_num < 3:
            st.session_state.pregunta_actual += 1
            st.rerun()
        else:
            # Revalida las 3 antes de enviar -- no solo la actual. Si alguien
            # volvió con "Atrás" y dejó una pregunta anterior vacía, esto la
            # atrapa antes de que llegue a guardarse (antes no pasaba nada).
            faltantes = [
                n for n in (1, 2, 3) if len(st.session_state.respuestas[n].strip()) < MIN_ANSWER_LENGTH
            ]
            if faltantes:
                st.session_state.pregunta_actual = faltantes[0]
                st.warning(
                    f"Falta completar la pregunta {faltantes[0]} antes de terminar.",
                    icon=":material/edit_note:",
                )
                st.rerun()
            else:
                procesar_respuestas(deporte)


def procesar_respuestas(deporte: str) -> None:
    with st.spinner("Ubicando tus opiniones en el diagrama..."):
        for pregunta_id in (1, 2, 3):
            texto = st.session_state.respuestas[pregunta_id].strip()
            vector = encode(texto)
            x, y, z = transform_to_3d(vector)
            # assign_cluster recibe las coordenadas ya proyectadas, no el
            # embedding crudo -- así "mismo color" siempre implica "cerca
            # en el diagrama" (ver pipeline/clustering.py).
            cluster_id = assign_cluster([x, y, z])
            storage.save_answer(
                visita_id=st.session_state.visita_id,
                pregunta_id=pregunta_id,
                deporte=deporte,
                texto=texto,
                cluster_id=cluster_id,
                x=x,
                y=y,
                z=z,
            )
    st.session_state.enviado = True
    st.rerun()


def render_resultado() -> None:
    if not st.session_state.balloons_shown:
        st.balloons()
        st.session_state.balloons_shown = True

    with st.container(border=True):
        st.subheader("¡Listo!", divider="blue")
        st.success(
            "Tus 3 respuestas ya son parte del diagrama, resaltadas más abajo. "
            "Más abajo también te explicamos cómo leerlo.",
            icon=":material/celebration:",
        )


def wrap_for_hover(texto: str, width: int = 42) -> str:
    """Inserta saltos de línea cada `width` caracteres.

    Sin esto, Plotly dibuja el texto como una sola línea que puede
    extenderse más allá del ancho de la caja de hover y verse cortada,
    en vez de acomodarse en varias líneas legibles.
    """
    return "<br>".join(textwrap.wrap(texto, width=width))


def hover_text(point: dict) -> str:
    texto = point["texto"]
    if len(texto) > MAX_HOVER_CHARS:
        texto = texto[:MAX_HOVER_CHARS].rstrip() + "…"
    pregunta_texto = QUESTIONS.get(point["pregunta_id"], "")
    return (
        f"{point['deporte']}<br>"
        f"{wrap_for_hover(pregunta_texto)}<br>"
        f"“{wrap_for_hover(texto)}”"
    )


NEUTRAL_LEGEND_COLOR = "#52514e"  # ink secundario -- no es color de ningún clúster


def build_cube_figure(points: list[dict], highlight_visita_id: str | None) -> go.Figure:
    fig = go.Figure()

    axis_style = dict(
        backgroundcolor="#fcfcfb",
        gridcolor="#e1e0d9",
        showspikes=False,
        zerolinecolor="#c3c2b7",
    )

    for pregunta_id, shape in PREGUNTA_TO_SHAPE.items():
        subset = [p for p in points if p["pregunta_id"] == pregunta_id]
        if not subset:
            continue
        fig.add_trace(
            go.Scatter3d(
                x=[p["x"] for p in subset],
                y=[p["y"] for p in subset],
                z=[p["z"] for p in subset],
                mode="markers",
                name=f"Pregunta {pregunta_id}",
                showlegend=False,  # la leyenda real es la traza fantasma de abajo
                marker=dict(
                    size=6,
                    color=[get_color_for_cluster(p["cluster_id"], mode="light") for p in subset],
                    symbol=shape,
                    line=dict(width=0.5, color="rgba(0,0,0,0.35)"),
                ),
                hovertext=[hover_text(p) for p in subset],
                hoverinfo="text",
            )
        )

    hay_resaltados = False
    if highlight_visita_id:
        mine = [p for p in points if p["visita_id"] == highlight_visita_id]
        if mine:
            hay_resaltados = True
            fig.add_trace(
                go.Scatter3d(
                    x=[p["x"] for p in mine],
                    y=[p["y"] for p in mine],
                    z=[p["z"] for p in mine],
                    mode="markers",
                    name="Tus respuestas",
                    showlegend=False,
                    marker=dict(
                        size=11,
                        color=[get_color_for_cluster(p["cluster_id"], mode="light") for p in mine],
                        symbol=[PREGUNTA_TO_SHAPE[p["pregunta_id"]] for p in mine],
                        line=dict(width=2, color="#1c1b1b"),
                    ),
                    hovertext=[hover_text(p) for p in mine],
                    hoverinfo="text",
                )
            )

    # Trazas fantasma, sin datos reales: existen solo para que la leyenda
    # muestre un color neutro y consistente. El color real de cada punto ya
    # se ve en el gráfico -- la leyenda aquí explica la FORMA (pregunta),
    # no debe repetir ni mezclarse con el color de clúster.
    for pregunta_id, shape in PREGUNTA_TO_SHAPE.items():
        fig.add_trace(
            go.Scatter3d(
                x=[None],
                y=[None],
                z=[None],
                mode="markers",
                name=f"Pregunta {pregunta_id}",
                marker=dict(size=6, color=NEUTRAL_LEGEND_COLOR, symbol=shape),
                hoverinfo="skip",
            )
        )
    if hay_resaltados:
        fig.add_trace(
            go.Scatter3d(
                x=[None],
                y=[None],
                z=[None],
                mode="markers",
                name="Tus respuestas",
                marker=dict(size=9, color=NEUTRAL_LEGEND_COLOR, line=dict(width=2, color="#1c1b1b")),
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            xaxis=dict(title="Componente 1", **axis_style),
            yaxis=dict(title="Componente 2", **axis_style),
            zaxis=dict(title="Componente 3", **axis_style),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0,
            xanchor="center",
            x=0.5,
            font=dict(color="#40493d"),
        ),
        margin=dict(l=0, r=0, t=10, b=70),
        height=560,
    )
    return fig


def render_cube_section(points: list[dict]) -> None:
    with st.container(border=True):
        st.subheader("Diagrama de Opiniones", divider="blue")
        st.caption("Cada punto es una opinión real. Las que se parecen en significado, quedan cerca.")

        highlight = st.session_state.visita_id if st.session_state.enviado else None

        col_aspirantes, col_opiniones = st.columns(2)
        with col_aspirantes:
            render_stat_card(
                "Aspirantes participando",
                str(len(points) // 3),
                gradient="linear-gradient(135deg,#1976d2,#0d47a1)",
                text_color="#ffffff",
                label_color="rgba(255,255,255,0.85)",
            )
        with col_opiniones:
            render_stat_card(
                "Opiniones en el diagrama",
                str(len(points)),
                gradient="linear-gradient(135deg,#fec330,#f8bd2a)",
                text_color="#6f5100",
                label_color="rgba(111,81,0,0.75)",
            )

        st.write("")
        if not points:
            st.caption("Todavía no hay opiniones. Sé el primero en aparecer aquí.")

        fig = build_cube_figure(points, highlight)
        st.plotly_chart(fig, use_container_width=True)

        variance = get_variance_explained()
        if variance is not None:
            st.caption(
                f"Estos 3 ejes resumen el {variance:.0%} de la variación real entre las opiniones. "
                "El resto no se puede dibujar en 3 dimensiones, por eso la posición es aproximada. "
                "La cercanía entre puntos sigue siendo una buena pista, solo que no perfecta."
            )

        st.write("")
        render_interpretation()
        st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)


def build_sports_treemap(points: list[dict]) -> go.Figure | None:
    """Cuenta ASPIRANTES (visita_id únicos) por deporte, no filas -- cada
    visitante aporta 3 filas (una por pregunta) y contarlas tal cual
    triplicaría el número sin cambiar las proporciones entre deportes."""
    visitors_by_sport: dict[str, set[str]] = defaultdict(set)
    for p in points:
        visitors_by_sport[p["deporte"]].add(p["visita_id"])

    counts = {sport: len(ids) for sport, ids in visitors_by_sport.items()}
    if not counts:
        return None

    # Un color distinto por deporte (paleta categórica validada), no un
    # degradado de un solo tono -- son identidades distintas, no una
    # magnitud continua. Se ordenan por tamaño para que los primeros
    # deportes (los slots más seguros de la paleta) sean los más mencionados.
    ordered_sports = sorted(counts, key=lambda s: -counts[s])
    color_map = {
        sport: (CATEGORICAL_PALETTE[i]["light"] if i < len(CATEGORICAL_PALETTE) else OTHER_COLOR["light"])
        for i, sport in enumerate(ordered_sports)
    }

    df = pd.DataFrame({"deporte": ordered_sports, "aspirantes": [counts[s] for s in ordered_sports]})
    fig = px.treemap(
        df,
        path=["deporte"],
        values="aspirantes",
        color="deporte",
        color_discrete_map=color_map,
    )
    fig.update_traces(
        texttemplate="%{label}<br>%{value}",
        textfont=dict(family="Montserrat, sans-serif", size=14, color="#ffffff"),
        marker=dict(line=dict(width=2, color="#ffffff")),
        hovertemplate="<b>%{label}</b><br>%{value} aspirante(s)<extra></extra>",
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_showscale=False,
        height=340,
    )
    return fig


def render_sports_section(points: list[dict]) -> None:
    with st.container(border=True):
        st.subheader("Deportes más mencionados", divider="blue")
        st.caption("Cuántos aspirantes eligieron cada deporte hasta ahora.")

        fig = build_sports_treemap(points)
        if fig is None:
            st.caption("Todavía no hay datos. Aparecerán aquí en cuanto alguien complete el cuestionario.")
        else:
            st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="DATA SPORT · ConexIA 2026", layout="centered")
    inject_style()
    init_session_state()
    render_header()

    if st.session_state.enviado:
        render_resultado()
    else:
        deporte, locked = render_sport_selector()
        render_quiz(deporte, locked)

    points = storage.load_all_points()

    st.divider()
    render_sports_section(points)
    st.divider()
    render_cube_section(points)


if __name__ == "__main__":
    main()
