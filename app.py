from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from app_core.data import (
    ProjectRecord,
    group_portfolio,
    load_portfolio,
    load_region_data,
    load_team,
)
from app_core.ui import (
    format_decimal,
    inject_css,
    render_app_summary,
    render_diagnostics,
    render_footer,
    render_hero,
    render_kpis,
    render_project_card,
    render_team_section,
)
from app_core.visuals import (
    build_buffer_chart,
    build_influence_map,
    build_timeline_chart,
)


st.set_page_config(
    page_title="APP Territorio Perú",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()


def render_project(project: ProjectRecord) -> None:
    with st.spinner(f"Preparando el entorno territorial de {project.section_name}…"):
        region, diagnostics = load_region_data(
            project.database_name,
            project.latitude,
            project.longitude,
        )

    render_kpis(region)
    information_column, map_column = st.columns([0.30, 0.70], gap="large")

    with information_column:
        render_project_card(project)

    with map_column:
        st.markdown(
            """
            <div class="map-heading">
                <h3>Zona de influencia y línea de tiempo</h3>
                <p>El globo temático identifica la APP. Usa ▶ para reproducir y la leyenda para aislar funciones de los proyectos de inversión.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        control_left, control_middle, control_right = st.columns(
            [0.48, 0.25, 0.27], vertical_alignment="bottom"
        )
        with control_left:
            coverage = st.segmented_control(
                "Cobertura del mapa",
                options=("Hasta 50 km", "Región completa"),
                default="Hasta 50 km",
                key=f"coverage-{project.key}",
                help="La vista de 50 km enfatiza los cuatro anillos del notebook; la vista regional muestra toda la base.",
            )
        within_50_km = coverage != "Región completa"
        with control_middle:
            map_background = st.selectbox(
                "Fondo",
                options=("Cartográfico", "Sin conexión"),
                key=f"background-{project.key}",
                help="Usa ‘Sin conexión’ si las teselas cartográficas no están disponibles.",
            )
        coverage_frame = (
            region.loc[region["DIST_KM"].le(50)].copy() if within_50_km else region
        )
        available_functions = sorted(coverage_frame["FUNCION"].dropna().unique().tolist())
        with control_right:
            with st.popover(
                "Filtrar funciones",
                icon=":material/filter_alt:",
                width="stretch",
            ):
                selected_functions = st.multiselect(
                    "Funciones visibles",
                    options=available_functions,
                    default=available_functions,
                    key=f"functions-{project.key}-{coverage}",
                    help="También puedes ocultar o aislar una función haciendo clic en la leyenda del mapa.",
                )

        if not selected_functions:
            st.info("Selecciona al menos una función para mostrar sus proyectos de inversión en el mapa.")

        figure = build_influence_map(
            region,
            project,
            selected_functions=selected_functions,
            within_50_km=within_50_km,
            map_background=map_background,
        )
        st.plotly_chart(
            figure,
            key=f"map-{project.key}-{coverage}-{map_background}",
            width="stretch",
            theme=None,
            config={
                "displaylogo": False,
                "scrollZoom": False,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": f"mapa_{project.key}",
                    "scale": 2,
                },
            },
        )
        render_diagnostics(diagnostics)

    st.markdown(
        """
        <div class="section-heading">
            <span>Lectura complementaria</span>
            <h3>Cómo evoluciona el entorno territorial</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_view = coverage_frame.loc[
        coverage_frame["FUNCION"].isin(selected_functions)
    ].copy()
    if selected_view.empty:
        st.info("No hay registros para resumir con los filtros actuales.")
    else:
        timeline_column, buffer_column = st.columns([0.58, 0.42], gap="large")
        with timeline_column:
            st.plotly_chart(
                build_timeline_chart(selected_view, project.color),
                key=f"timeline-{project.key}-{coverage}",
                width="stretch",
                theme=None,
                config={"displayModeBar": False},
            )
        with buffer_column:
            st.plotly_chart(
                build_buffer_chart(selected_view),
                key=f"buffers-{project.key}-{coverage}",
                width="stretch",
                theme=None,
                config={"displayModeBar": False},
            )

    with st.expander("Ver datos del mapa"):
        table = selected_view[
            [
                "CODIGO_UNICO",
                "NOMBRE_INVERSION",
                "FUNCION",
                "ANO",
                "DIST_KM",
                "BUFFER",
                "COSTO_ACTUALIZADO",
                "PROVINCIA",
                "DISTRITO",
            ]
        ].copy()
        table["CODIGO_UNICO"] = table["CODIGO_UNICO"].astype(str)
        table["DIST_KM"] = table["DIST_KM"].map(
            lambda value: f"{format_decimal(value, 1)} km"
        )
        table["COSTO_ACTUALIZADO"] = table["COSTO_ACTUALIZADO"].map(
            lambda value: f"S/ {format_decimal(value / 1_000_000, 2)} MM"
        )
        table.columns = [
            "CUI",
            "Inversión",
            "Función",
            "Año",
            "Distancia (km)",
            "Rango",
            "Costo actualizado (S/ MM)",
            "Provincia",
            "Distrito",
        ]
        st.dataframe(
            table,
            width="stretch",
            height=420,
            hide_index=True,
            column_config={
                "CUI": st.column_config.TextColumn("CUI"),
                "Distancia (km)": st.column_config.TextColumn("Distancia (km)"),
                "Costo actualizado (S/ MM)": st.column_config.TextColumn(
                    "Costo actualizado (S/ MM)"
                ),
            },
        )


def render_app(records: tuple[ProjectRecord, ...]) -> None:
    render_app_summary(records)
    if len(records) == 1:
        selected = records[0]
        st.caption(f"Sección única · {selected.section_name}")
    else:
        options = [record.key for record in records]
        labels = {record.key: record.section_name for record in records}
        selected_key = st.segmented_control(
            "Inversiones vinculantes",
            options=options,
            default=options[0],
            format_func=labels.get,
            key=f"section-app-{records[0].app_id}",
            required=True,
            width="stretch",
        )
        selected = next(record for record in records if record.key == selected_key)
    render_project(selected)


def main() -> None:
    try:
        portfolio = load_portfolio()
        grouped = group_portfolio(portfolio)
    except (FileNotFoundError, ValueError) as error:
        st.error("No fue posible iniciar la aplicación.")
        st.exception(error)
        st.stop()

    render_hero(portfolio)
    ordered_groups = [grouped[app_id] for app_id in sorted(grouped)]
    tab_labels = [records[0].tab_label for records in ordered_groups]
    tab_labels.append("👥 Acerca del Equipo")
    tabs = st.tabs(
        tab_labels,
        key="principal-app-tabs",
        on_change="rerun",
        width="stretch",
    )
    for tab, records in zip(tabs[:-1], ordered_groups):
        if tab.open:
            with tab:
                try:
                    render_app(records)
                except (FileNotFoundError, ValueError) as error:
                    st.error(f"No se pudo cargar la sección {records[0].app_name}.")
                    st.exception(error)

    team_tab = tabs[-1]
    if team_tab.open:
        with team_tab:
            try:
                render_team_section(load_team())
            except (FileNotFoundError, ValueError) as error:
                st.error("No se pudo cargar la sección Acerca del Equipo.")
                st.exception(error)

    render_footer()


if __name__ == "__main__":
    main()
