from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .data import BUFFER_ORDER, ProjectRecord, normalize_name


FUNCTION_COLORS = {
    "EDUCACION": "#3157D5",
    "SALUD": "#D63864",
    "TRANSPORTE": "#007C83",
    "SANEAMIENTO": "#00A680",
    "AGROPECUARIA": "#5D8F24",
    "ORDEN_PUBLICO_Y_SEGURIDAD": "#7B4FC9",
    "VIVIENDA_Y_DESARROLLO_URBANO": "#D87924",
    "CULTURA_Y_DEPORTE": "#B63A8F",
    "PROTECCION_SOCIAL": "#8A5A44",
    "AMBIENTE": "#3B8E5A",
    "ENERGIA": "#D99A00",
    "TURISMO": "#2C79B8",
    "PLANEAMIENTO_GESTION_Y_RESERVA_DE_CONTINGENCIA": "#64748B",
}

FALLBACK_PALETTE = (
    "#3157D5",
    "#00A680",
    "#D63864",
    "#8B5CF6",
    "#D87924",
    "#0781A7",
    "#A64D79",
    "#5D8F24",
    "#B46A18",
    "#475569",
    "#C2415B",
    "#0F766E",
)

BUFFER_COLORS = {
    "0–5 km": "#3157D5",
    "5–10 km": "#00A680",
    "10–20 km": "#D99A00",
    "20–50 km": "#E25555",
    "> 50 km": "#94A3B8",
}

def function_color(function_name: str) -> str:
    normalized = normalize_name(function_name)
    if normalized in FUNCTION_COLORS:
        return FUNCTION_COLORS[normalized]
    digest = hashlib.md5(normalized.encode("utf-8")).digest()
    return FALLBACK_PALETTE[digest[0] % len(FALLBACK_PALETTE)]


def geographic_circle(
    latitude: float,
    longitude: float,
    radius_km: float,
    points: int = 96,
) -> tuple[np.ndarray, np.ndarray]:
    earth_radius_km = 6_371.0
    bearings = np.linspace(0, 2 * np.pi, points)
    lat_1 = np.radians(latitude)
    lon_1 = np.radians(longitude)
    angular_distance = radius_km / earth_radius_km
    lat_2 = np.arcsin(
        np.sin(lat_1) * np.cos(angular_distance)
        + np.cos(lat_1) * np.sin(angular_distance) * np.cos(bearings)
    )
    lon_2 = lon_1 + np.arctan2(
        np.sin(bearings) * np.sin(angular_distance) * np.cos(lat_1),
        np.cos(angular_distance) - np.sin(lat_1) * np.sin(lat_2),
    )
    return np.degrees(lat_2), np.degrees(lon_2)


def _custom_data(frame: pd.DataFrame) -> np.ndarray:
    district = (
        frame["DISTRITO"]
        if "DISTRITO" in frame.columns
        else pd.Series(["No disponible"] * len(frame), index=frame.index)
    )
    return np.column_stack(
        [
            frame["NOMBRE_INVERSION"].to_numpy(),
            frame["ANO"].to_numpy(),
            frame["BUFFER"].astype(str).to_numpy(),
            frame["DIST_KM"].to_numpy(),
            (frame["COSTO_ACTUALIZADO"] / 1_000_000).to_numpy(),
            frame["CODIGO_UNICO"].astype(str).to_numpy(),
            district.to_numpy(),
        ]
    )


def _project_icon_vectors(
    project: ProjectRecord,
    within_50_km: bool,
) -> tuple[list[float | None], list[float | None]]:
    """Construye un pictograma vectorial local, independiente de sprites web."""
    size_km = 5.8 if within_50_km else 12.0
    lat_scale = size_km / 111.0
    lon_scale = size_km / (111.0 * np.cos(np.radians(project.latitude)))

    if project.app_id == 1:  # colegio: techo, edificio y puerta
        strokes = (
            ((-0.46, 0.04), (0.0, 0.42), (0.46, 0.04)),
            ((-0.34, 0.04), (-0.34, -0.40), (0.34, -0.40), (0.34, 0.04)),
            ((-0.09, -0.40), (-0.09, -0.10), (0.09, -0.10), (0.09, -0.40)),
        )
    elif project.app_id == 2:  # puerto: ancla simplificada
        strokes = (
            ((0.0, 0.42), (0.0, -0.30)),
            ((-0.16, 0.24), (0.16, 0.24)),
            ((-0.39, 0.02), (-0.34, -0.22), (-0.17, -0.39), (0.0, -0.43), (0.17, -0.39), (0.34, -0.22), (0.39, 0.02)),
            ((-0.39, 0.02), (-0.23, -0.02)),
            ((0.39, 0.02), (0.23, -0.02)),
        )
    else:  # salud: cruz médica
        strokes = (
            ((-0.38, 0.0), (0.38, 0.0)),
            ((0.0, -0.38), (0.0, 0.38)),
        )

    latitudes: list[float | None] = []
    longitudes: list[float | None] = []
    for stroke in strokes:
        for x_value, y_value in stroke:
            latitudes.append(project.latitude + y_value * lat_scale)
            longitudes.append(project.longitude + x_value * lon_scale)
        latitudes.append(None)
        longitudes.append(None)
    return latitudes, longitudes


def build_influence_map(
    frame: pd.DataFrame,
    project: ProjectRecord,
    selected_functions: list[str] | tuple[str, ...] | None = None,
    within_50_km: bool = True,
    map_background: str = "Cartográfico",
) -> go.Figure:
    visible = frame.loc[frame["DIST_KM"].le(50)].copy() if within_50_km else frame.copy()
    available_functions = sorted(visible["FUNCION"].dropna().unique().tolist())
    functions = (
        [function for function in selected_functions if function in available_functions]
        if selected_functions is not None
        else available_functions
    )
    visible = visible.loc[visible["FUNCION"].isin(functions)].copy()

    figure = go.Figure()

    fill_latitudes, fill_longitudes = geographic_circle(
        project.latitude, project.longitude, 50
    )
    figure.add_trace(
        go.Scattermap(
            lat=fill_latitudes,
            lon=fill_longitudes,
            mode="lines",
            line={"color": "rgba(49,87,213,0)", "width": 0},
            fill="toself",
            fillcolor="rgba(49,87,213,0.035)",
            hoverinfo="skip",
            showlegend=False,
        )
    )

    for index, (radius, color) in enumerate(
        zip((5, 10, 20, 50), ("#3157D5", "#00A680", "#D99A00", "#E25555"))
    ):
        latitudes, longitudes = geographic_circle(
            project.latitude, project.longitude, radius
        )
        figure.add_trace(
            go.Scattermap(
                lat=latitudes,
                lon=longitudes,
                mode="lines",
                line={"color": color, "width": 2.2 if radius == 50 else 1.6},
                opacity=0.78,
                name="Radios 5 · 10 · 20 · 50 km" if index == 0 else f"Radio {radius} km",
                showlegend=index == 0,
                hovertemplate=f"Límite de {radius} km<extra></extra>",
                legendgroup="radios",
            )
        )

    # Halo + globo + pictograma: un marcador temático permanente en lugar de la estrella.
    figure.add_trace(
        go.Scattermap(
            lat=[project.latitude],
            lon=[project.longitude],
            mode="markers",
            marker={"size": 52, "color": project.color, "opacity": 0.20, "symbol": "circle"},
            hoverinfo="skip",
            showlegend=False,
        )
    )
    figure.add_trace(
        go.Scattermap(
            lat=[project.latitude],
            lon=[project.longitude],
            mode="markers",
            marker={
                "size": 38,
                "color": project.color,
                "opacity": 0.98,
                "symbol": "circle",
                "allowoverlap": True,
            },
            name=f"{project.icon} Proyecto APP",
            customdata=[[project.project_name, project.department_display]],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Proyecto eje · %{customdata[1]}<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scattermap(
            lat=[project.latitude],
            lon=[project.longitude],
            mode="markers",
            marker={
                "size": 29,
                "color": "white",
                "opacity": 0.98,
                "symbol": "circle",
                "allowoverlap": True,
            },
            hoverinfo="skip",
            showlegend=False,
        )
    )
    icon_latitudes, icon_longitudes = _project_icon_vectors(project, within_50_km)
    figure.add_trace(
        go.Scattermap(
            lat=icon_latitudes,
            lon=icon_longitudes,
            mode="lines",
            line={"color": project.color, "width": 3.4},
            name=f"Logo {project.app_name}",
            hoverinfo="skip",
            showlegend=False,
        )
    )

    static_trace_count = len(figure.data)
    years = sorted(visible["ANO"].dropna().astype(int).unique().tolist())

    if functions and years:
        first_year = years[0]
        initial = visible.loc[visible["ANO"].le(first_year)]
        for function in functions:
            subset = initial.loc[initial["FUNCION"].eq(function)]
            figure.add_trace(
                go.Scattermap(
                    lat=subset["LATITUD"],
                    lon=subset["LONGITUD"],
                    mode="markers",
                    marker={
                        "size": 10,
                        "color": function_color(function),
                        "opacity": 0.78,
                        "symbol": "circle",
                    },
                    name=function.title(),
                    customdata=_custom_data(subset),
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        f"Función: {function.title()}<br>"
                        "Año: %{customdata[1]} · CUI: %{customdata[5]}<br>"
                        "Distrito: %{customdata[6]}<br>"
                        "Distancia: %{customdata[3]:.1f} km · %{customdata[2]}<br>"
                        "Costo actualizado: S/ %{customdata[4]:,.2f} MM<extra></extra>"
                    ),
                    legendgroup="functions",
                )
            )

        frames: list[go.Frame] = []
        for year in years:
            cumulative = visible.loc[visible["ANO"].le(year)]
            frame_traces: list[go.Scattermap] = []
            trace_indexes: list[int] = []
            for function_index, function in enumerate(functions):
                subset = cumulative.loc[cumulative["FUNCION"].eq(function)]
                frame_traces.append(
                    go.Scattermap(
                        lat=subset["LATITUD"],
                        lon=subset["LONGITUD"],
                        mode="markers",
                        marker={
                            "size": 10,
                            "color": function_color(function),
                            "opacity": 0.78,
                            "symbol": "circle",
                        },
                        customdata=_custom_data(subset),
                    )
                )
                trace_indexes.append(static_trace_count + function_index)
            frames.append(
                go.Frame(data=frame_traces, traces=trace_indexes, name=str(year))
            )
        figure.frames = frames

    slider_steps = [
        {
            "method": "animate",
            "args": [
                [str(year)],
                {
                    "frame": {"duration": 0, "redraw": True},
                    "mode": "immediate",
                    "transition": {"duration": 0},
                },
            ],
            "label": str(year),
        }
        for year in years
    ]

    figure.update_layout(
        map={
            "style": "white-bg" if map_background == "Sin conexión" else "carto-positron",
            "center": {"lat": project.latitude, "lon": project.longitude},
            "zoom": 8.05 if within_50_km else 6.65,
        },
        height=680,
        margin={"l": 0, "r": 0, "t": 10, "b": 76},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Segoe UI, Inter, sans-serif", "color": "#273449"},
        hoverlabel={"bgcolor": "white", "font_size": 12, "font_family": "Segoe UI"},
        legend={
            "title": {"text": "Capas y funciones"},
            "orientation": "v",
            "yanchor": "top",
            "y": 0.98,
            "xanchor": "right",
            "x": 0.99,
            "font": {"size": 9.5},
            "bgcolor": "rgba(255,255,255,0.90)",
            "bordercolor": "rgba(203,213,225,0.80)",
            "borderwidth": 1,
            "maxheight": 0.60,
            "groupclick": "toggleitem",
        },
        sliders=(
            [
                {
                    "steps": slider_steps,
                    "active": 0,
                    "x": 0.18,
                    "y": 0.01,
                    "len": 0.80,
                    "pad": {"t": 18, "b": 0},
                    "currentvalue": {
                        "prefix": "Acumulado hasta ",
                        "font": {"size": 12, "color": "#475569"},
                    },
                    "tickcolor": "#CBD5E1",
                }
            ]
            if slider_steps
            else []
        ),
        updatemenus=(
            [
                {
                    "type": "buttons",
                    "direction": "left",
                    "showactive": False,
                    "x": 0,
                    "y": 0.01,
                    "xanchor": "left",
                    "yanchor": "top",
                    "pad": {"t": 18, "r": 8},
                    "buttons": [
                        {
                            "label": "▶",
                            "method": "animate",
                            "args": [
                                None,
                                {
                                    "frame": {"duration": 650, "redraw": True},
                                    "transition": {"duration": 120},
                                    "fromcurrent": True,
                                    "mode": "immediate",
                                },
                            ],
                        },
                        {
                            "label": "Ⅱ",
                            "method": "animate",
                            "args": [
                                [None],
                                {
                                    "frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate",
                                },
                            ],
                        },
                    ],
                }
            ]
            if slider_steps
            else []
        ),
        uirevision=f"{project.key}-{'50' if within_50_km else 'region'}-{map_background}",
    )
    return figure


def build_timeline_chart(frame: pd.DataFrame, color: str) -> go.Figure:
    yearly = frame.groupby("ANO", observed=True).size().rename("NUEVAS").reset_index()
    yearly["ACUMULADAS"] = yearly["NUEVAS"].cumsum()
    yearly["ANO_TEXTO"] = yearly["ANO"].astype(int).astype(str)
    year_labels = yearly["ANO_TEXTO"].tolist()
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=yearly["ANO_TEXTO"],
            y=yearly["NUEVAS"],
            name="Registradas en el año",
            marker={"color": color, "opacity": 0.30, "cornerradius": 5},
            hovertemplate="%{x}: %{y:,.0f} nuevas<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=yearly["ANO_TEXTO"],
            y=yearly["ACUMULADAS"],
            name="Acumuladas",
            mode="lines+markers",
            line={"color": color, "width": 3},
            marker={"size": 7, "color": "white", "line": {"color": color, "width": 2}},
            hovertemplate="%{x}: %{y:,.0f} acumuladas<extra></extra>",
        )
    )
    figure.update_layout(
        height=320,
        margin={"l": 42, "r": 10, "t": 54, "b": 48},
        title={"text": "Evolución de registros", "x": 0, "font": {"size": 16}},
        xaxis={
            "title": None,
            "type": "category",
            "categoryorder": "array",
            "categoryarray": year_labels,
            "tickmode": "array",
            "tickvals": year_labels,
            "ticktext": year_labels,
            "tickangle": 0,
            "tickfont": {"size": 10},
            "showgrid": False,
            "automargin": True,
        },
        yaxis={
            "title": None,
            "gridcolor": "#E9EEF5",
            "zeroline": False,
            "tickformat": ",d",
            "separatethousands": True,
            "automargin": True,
        },
        legend={"orientation": "h", "y": 1.18, "x": 1, "xanchor": "right", "font": {"size": 10}},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Segoe UI, Inter, sans-serif", "color": "#334155"},
        hovermode="x unified",
    )
    return figure


def build_buffer_chart(frame: pd.DataFrame) -> go.Figure:
    counts = (
        frame.groupby("BUFFER", observed=False)
        .size()
        .reindex(BUFFER_ORDER, fill_value=0)
        .rename("PROYECTOS")
        .reset_index()
    )
    distance_labels = [str(label) for label in counts["BUFFER"]]
    display_counts = [f"{int(value):,}" for value in counts["PROYECTOS"]]
    figure = go.Figure(
        go.Bar(
            y=distance_labels,
            x=counts["PROYECTOS"],
            orientation="h",
            marker={"color": [BUFFER_COLORS[str(label)] for label in counts["BUFFER"]], "cornerradius": 6},
            text=display_counts,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x:,.0f} proyectos de inversión<extra></extra>",
        )
    )
    figure.update_layout(
        height=320,
        margin={"l": 88, "r": 62, "t": 48, "b": 28},
        title={"text": "Distribución por distancia", "x": 0, "font": {"size": 16}},
        xaxis={"visible": False},
        yaxis={
            "title": None,
            "autorange": "reversed",
            "showgrid": False,
            "tickmode": "array",
            "tickvals": distance_labels,
            "ticktext": distance_labels,
            "automargin": True,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Segoe UI, Inter, sans-serif", "color": "#334155"},
        showlegend=False,
    )
    return figure
