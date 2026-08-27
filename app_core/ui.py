from __future__ import annotations

import base64
from datetime import date
from html import escape
import mimetypes
from pathlib import Path

import pandas as pd
import streamlit as st

from .data import ProjectRecord, RegionDiagnostics, TeamMember


GLOBAL_CSS = """
<style>
:root {
    --ink: #172033;
    --muted: #66758C;
    --line: #E3E9F2;
    --surface: rgba(255,255,255,.94);
}
.stApp {
    background:
        radial-gradient(circle at 8% 4%, rgba(49,87,213,.09), transparent 28rem),
        radial-gradient(circle at 92% 12%, rgba(0,166,128,.08), transparent 30rem),
        #F5F7FB;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] {
    max-width: 1500px;
    padding-top: 1.8rem;
    padding-bottom: 3rem;
}
.hero {
    position: relative;
    overflow: hidden;
    padding: 2.1rem 2.25rem;
    border-radius: 24px;
    color: white;
    background: linear-gradient(120deg, #16264B 0%, #203B75 52%, #006D72 125%);
    box-shadow: 0 20px 48px rgba(23,38,75,.16);
    margin-bottom: 1.2rem;
}
.hero::after {
    content: "";
    position: absolute;
    width: 280px;
    height: 280px;
    border-radius: 50%;
    right: -65px;
    top: -115px;
    border: 38px solid rgba(255,255,255,.07);
}
.hero-topline {
    display: flex;
    align-items: center;
    gap: .65rem;
    font-size: .73rem;
    font-weight: 750;
    letter-spacing: .16em;
    text-transform: uppercase;
    color: #BFE9E7;
}
.live-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #62E6B7;
    box-shadow: 0 0 0 5px rgba(98,230,183,.12);
}
.hero h1 {
    margin: .65rem 0 .4rem;
    font-size: clamp(2rem, 4vw, 3.65rem);
    line-height: 1.02;
    letter-spacing: -.045em;
    max-width: 850px;
}
.hero-copy {
    max-width: 780px;
    margin: 0;
    color: #D8E4F7;
    font-size: 1.05rem;
    line-height: 1.6;
}
.hero-stats {
    display: flex;
    flex-wrap: wrap;
    gap: .65rem;
    margin-top: 1.45rem;
}
.hero-stat {
    padding: .58rem .82rem;
    border: 1px solid rgba(255,255,255,.16);
    border-radius: 11px;
    background: rgba(255,255,255,.08);
    backdrop-filter: blur(8px);
    color: #EEF5FF;
    font-size: .82rem;
}
.hero-stat strong { color: white; font-size: .95rem; margin-right: .22rem; }

.app-summary {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 1.4rem;
    align-items: center;
    padding: 1.25rem 1.35rem;
    border: 1px solid var(--line);
    border-left: 5px solid var(--accent);
    border-radius: 16px;
    background: var(--surface);
    box-shadow: 0 8px 22px rgba(30,41,59,.05);
    margin: .7rem 0 1rem;
}
.app-summary h2 { margin: 0 0 .25rem; color: var(--ink); font-size: 1.48rem; letter-spacing: -.02em; }
.app-summary p { margin: 0; color: var(--muted); line-height: 1.5; }
.app-summary-number { text-align: right; white-space: nowrap; }
.app-summary-number strong { display: block; color: var(--ink); font-size: 1.55rem; }
.app-summary-number span { color: var(--muted); font-size: .74rem; text-transform: uppercase; letter-spacing: .08em; }

.project-card {
    --accent: #3157D5;
    --accent-soft: #E9EEFF;
    position: relative;
    overflow: hidden;
    padding: 1.35rem;
    border: 1px solid var(--line);
    border-radius: 18px;
    background: var(--surface);
    box-shadow: 0 12px 30px rgba(30,41,59,.07);
}
.project-card::before {
    content: "";
    position: absolute;
    width: 150px;
    height: 150px;
    border-radius: 50%;
    right: -78px;
    top: -78px;
    background: var(--accent-soft);
}
.project-icon {
    display: grid;
    place-items: center;
    width: 50px;
    height: 50px;
    border-radius: 16px 16px 16px 5px;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: 1.45rem;
    margin-bottom: 1rem;
}
.eyebrow {
    display: block;
    color: var(--accent);
    font-size: .69rem;
    font-weight: 800;
    letter-spacing: .12em;
    text-transform: uppercase;
    margin-bottom: .4rem;
}
.project-card h3 { margin: 0 0 .7rem; color: var(--ink); font-size: 1.4rem; line-height: 1.18; letter-spacing: -.025em; }
.project-card .explanation { color: #56657A; font-size: .9rem; line-height: 1.6; margin-bottom: 1rem; }
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: .42rem;
    padding: .35rem .58rem;
    border-radius: 999px;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: .74rem;
    font-weight: 750;
    margin-bottom: 1.1rem;
}
.status-pill::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.detail-grid { display: grid; grid-template-columns: 1fr; gap: .7rem; }
.detail-row { padding-bottom: .68rem; border-bottom: 1px solid #EDF1F6; }
.detail-row:last-child { border-bottom: 0; padding-bottom: 0; }
.detail-label { display: block; color: #8390A3; font-size: .67rem; font-weight: 720; text-transform: uppercase; letter-spacing: .07em; margin-bottom: .18rem; }
.detail-value { color: #263449; font-size: .87rem; line-height: 1.4; font-weight: 600; }
.money-highlight { color: var(--accent); font-size: 1.2rem; font-weight: 800; }
.source-chip { margin-top: 1rem; padding: .65rem .75rem; border-radius: 10px; background: #F6F8FB; color: #718096; font-size: .72rem; word-break: break-word; }

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: .75rem;
    margin: .25rem 0 1rem;
}
.kpi {
    padding: .85rem 1rem;
    border: 1px solid var(--line);
    border-radius: 14px;
    background: rgba(255,255,255,.86);
}
.kpi-label { color: #718096; font-size: .7rem; text-transform: uppercase; letter-spacing: .07em; font-weight: 700; }
.kpi-value { display: block; color: var(--ink); font-size: 1.35rem; font-weight: 800; line-height: 1.25; margin-top: .2rem; letter-spacing: -.025em; }
.kpi-note { color: #91A0B3; font-size: .68rem; }

.map-shell {
    padding: .3rem .75rem .1rem;
    border: 1px solid var(--line);
    border-radius: 18px;
    background: rgba(255,255,255,.92);
    box-shadow: 0 12px 30px rgba(30,41,59,.06);
}
.map-heading h3 { margin: 0; color: var(--ink); font-size: 1.12rem; }
.map-heading p { margin: .22rem 0 .55rem; color: var(--muted); font-size: .8rem; }
.section-heading { margin: 1.7rem 0 .75rem; }
.section-heading span { color: #3157D5; font-size: .7rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
.section-heading h3 { color: var(--ink); margin: .25rem 0 0; font-size: 1.35rem; letter-spacing: -.025em; }
.method-note {
    padding: .9rem 1rem;
    border-radius: 13px;
    border: 1px solid #DDE6F1;
    background: #F8FAFD;
    color: #65748A;
    font-size: .79rem;
    line-height: 1.55;
}
.team-intro {
    position: relative;
    overflow: hidden;
    margin: .7rem 0 1.2rem;
    padding: 1.75rem 1.85rem;
    border: 1px solid #DDE5F1;
    border-radius: 20px;
    background: linear-gradient(125deg, rgba(255,255,255,.98), rgba(238,243,255,.94));
    box-shadow: 0 12px 30px rgba(30,41,59,.06);
}
.team-intro::after {
    content: "";
    position: absolute;
    width: 180px;
    height: 180px;
    border-radius: 50%;
    right: -75px;
    top: -90px;
    border: 28px solid rgba(49,87,213,.07);
}
.team-intro .eyebrow { margin-bottom: .5rem; }
.team-intro h2 { margin: 0 0 .55rem; color: var(--ink); font-size: 1.8rem; letter-spacing: -.035em; }
.team-intro p { margin: 0; max-width: 760px; color: var(--muted); line-height: 1.65; }
.team-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
}
.team-card {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-height: 100%;
    border: 1px solid var(--line);
    border-radius: 19px;
    background: rgba(255,255,255,.96);
    box-shadow: 0 12px 30px rgba(30,41,59,.07);
    transition: transform .18s ease, box-shadow .18s ease;
}
.team-card:hover { transform: translateY(-3px); box-shadow: 0 18px 38px rgba(30,41,59,.11); }
.team-photo-wrap { height: 270px; overflow: hidden; background: #EAF0F8; }
.team-photo {
    display: block;
    box-sizing: border-box;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
}
.team-photo-fallback {
    display: grid;
    place-items: center;
    width: 100%;
    height: 100%;
    color: #3157D5;
    background: linear-gradient(135deg, #E9EEFF, #DDF5F3);
    font-size: 2.2rem;
    font-weight: 800;
}
.team-card-body { display: flex; flex: 1; flex-direction: column; padding: 1.15rem 1.2rem 1.25rem; }
.team-card-body .team-label { color: #3157D5; font-size: .67rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
.team-card-body h3 { margin: .38rem 0 .55rem; color: var(--ink); font-size: 1.25rem; line-height: 1.2; letter-spacing: -.025em; }
.team-university { margin: 0 0 1rem; color: var(--muted); font-size: .86rem; line-height: 1.5; }
.linkedin-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: .4rem;
    min-height: 42px;
    margin-top: auto;
    border-radius: 11px;
    color: white !important;
    background: #0A66C2;
    font-size: .83rem;
    font-weight: 750;
    text-decoration: none !important;
}
.linkedin-button:hover { background: #084F96; }
.footer-note {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--line);
    color: #7C899B;
    font-size: .76rem;
    line-height: 1.55;
}

[data-baseweb="tab-list"] {
    gap: .55rem;
    background: rgba(255,255,255,.72);
    border: 1px solid var(--line);
    border-radius: 15px;
    padding: .35rem;
    box-shadow: 0 7px 18px rgba(30,41,59,.04);
}
button[data-baseweb="tab"] {
    border-radius: 11px;
    min-height: 44px;
    padding-left: 1rem;
    padding-right: 1rem;
}
button[data-baseweb="tab"][aria-selected="true"] { background: #EEF2FF; }
[data-testid="stMetric"] { background: white; border-color: var(--line); }
[data-testid="stPlotlyChart"] { border-radius: 14px; overflow: hidden; }
.stButton > button, .stLinkButton > a { border-radius: 11px; font-weight: 700; min-height: 43px; }
[data-testid="stSegmentedControl"] button { min-height: 40px; }

@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] { padding-left: 1rem; padding-right: 1rem; padding-top: 1rem; }
    .hero { padding: 1.6rem 1.3rem; border-radius: 18px; }
    .hero h1 { font-size: 2.15rem; }
    .hero-copy { font-size: .92rem; }
    .app-summary { grid-template-columns: 1fr; }
    .app-summary-number { text-align: left; }
    .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .team-grid { grid-template-columns: 1fr; }
    .team-photo-wrap { height: 340px; }
}
@media (max-width: 540px) {
    .kpi-grid { grid-template-columns: 1fr; }
    .hero-stat { width: 100%; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def format_integer(value: int | float) -> str:
    return f"{int(round(value)):,}"


def format_decimal(value: float, digits: int = 2) -> str:
    return f"{float(value):,.{digits}f}"


def format_soles(value: float, digits: int = 2) -> str:
    return f"S/ {format_decimal(float(value) / 1_000_000, digits)} MM"


MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def format_date(value: date | None) -> str:
    if value is None:
        return "No disponible"
    return f"{value.day} de {MONTHS[value.month - 1]} de {value.year}"


def render_hero(records: tuple[ProjectRecord, ...]) -> None:
    app_count = len({record.app_id for record in records})
    department_count = len({record.department for record in records})
    investment_total = sum(record.departmental_investment_usd_m for record in records)
    st.markdown(
        f"""
        <section class="hero">
            <div class="hero-topline"><span class="live-dot"></span> APP · Territorio · Inversión pública</div>
            <h1>APP Territorio Perú</h1>
            <p class="hero-copy">Una lectura interactiva de cada inversión vinculante y de los proyectos públicos que conforman su zona de influencia.</p>
            <div class="hero-stats">
                <div class="hero-stat"><strong>{format_integer(app_count)}</strong> APP</div>
                <div class="hero-stat"><strong>{format_integer(len(records))}</strong> inversiones vinculantes</div>
                <div class="hero-stat"><strong>US$ {format_decimal(investment_total, 1)} MM</strong> inversión territorial</div>
                <div class="hero-stat"><strong>{format_integer(department_count)}</strong> departamentos</div>
                <div class="hero-stat"><strong>100 % local</strong> sin descargas de datasets</div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_app_summary(records: tuple[ProjectRecord, ...]) -> None:
    first = records[0]
    total = sum(record.departmental_investment_usd_m for record in records)
    departments = " · ".join(record.department_display for record in records)
    st.markdown(
        f"""
        <section class="app-summary" style="--accent:{escape(first.color)}">
            <div>
                <h2>{escape(first.icon)} {escape(first.app_name)}</h2>
                <p>{escape(first.app_description)}<br><strong>{escape(departments)}</strong></p>
            </div>
            <div class="app-summary-number">
                <strong>US$ {format_decimal(total, 2)} MM</strong>
                <span>{format_integer(len(records))} inversión{'es' if len(records) != 1 else ''} vinculante{'s' if len(records) != 1 else ''}</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _project_explanation(project: ProjectRecord) -> str:
    return (
        f"Esta inversión de {project.sector.lower()} se desarrolla en "
        f"{project.department_display} mediante una {project.app_type} de "
        f"{project.initiative_type.lower()}, bajo modalidad {project.modality.lower()}. "
        f"Su titular es {project.owner} y actualmente figura como {project.status.lower()}."
    )


def render_project_card(project: ProjectRecord) -> None:
    explanation = _project_explanation(project)
    st.markdown(
        f"""
        <article class="project-card" style="--accent:{escape(project.color)};--accent-soft:{escape(project.soft_color)}">
            <div class="project-icon">{escape(project.icon)}</div>
            <span class="eyebrow">Inversión vinculante · {escape(project.department_display)}</span>
            <h3>{escape(project.section_name)}</h3>
            <p class="explanation">{escape(explanation)}</p>
            <div class="status-pill">{escape(project.status)}</div>
            <div class="detail-grid">
                <div class="detail-row">
                    <span class="detail-label">Proyecto</span>
                    <span class="detail-value">{escape(project.project_name)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Inversión en el departamento</span>
                    <span class="money-highlight">US$ {format_decimal(project.departmental_investment_usd_m, 2)} MM</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Fase contractual</span>
                    <span class="detail-value">{escape(project.phase)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Titular</span>
                    <span class="detail-value">{escape(project.owner)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Buena pro / adjudicación</span>
                    <span class="detail-value">{escape(format_date(project.award_date))}</span>
                </div>
            </div>
            <div class="source-chip">Base territorial: {escape(project.database_filename)} · hoja Sheet1</div>
        </article>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Concesionario y detalle contractual"):
        st.markdown(f"**Concesionario**  \n{project.concessionaire}")
        st.markdown(
            f"**Tipo de iniciativa:** {project.initiative_type}  \n"
            f"**Modalidad:** {project.modality}  \n"
            f"**Monto total estimado:** US$ {format_decimal(project.total_estimated_usd_m, 2)} MM"
        )
    if project.technical_sheet_url.startswith(("https://", "http://")):
        st.link_button(
            "Ver ficha técnica",
            project.technical_sheet_url,
            type="primary",
            icon=":material/open_in_new:",
            icon_position="right",
            width="stretch",
            help="Abre la ficha oficial de ProInversión en una nueva pestaña.",
        )
    else:
        st.warning("Esta inversión no tiene una URL válida de ficha técnica.")


def render_kpis(frame: pd.DataFrame) -> None:
    within_10 = int(frame["DIST_KM"].le(10).sum())
    within_50 = int(frame["DIST_KM"].le(50).sum())
    total_cost = float(frame["COSTO_ACTUALIZADO"].sum())
    functions = int(frame["FUNCION"].nunique())
    st.markdown(
        f"""
        <div class="kpi-grid">
            <div class="kpi"><span class="kpi-label">Base regional</span><span class="kpi-value">{format_integer(len(frame))}</span><span class="kpi-note">proyectos de inversión válidos</span></div>
            <div class="kpi"><span class="kpi-label">Entorno inmediato</span><span class="kpi-value">{format_integer(within_10)}</span><span class="kpi-note">proyectos de inversión a 10 km o menos</span></div>
            <div class="kpi"><span class="kpi-label">Zona ampliada</span><span class="kpi-value">{format_integer(within_50)}</span><span class="kpi-note">proyectos de inversión a 50 km o menos</span></div>
            <div class="kpi"><span class="kpi-label">Costo actualizado regional</span><span class="kpi-value">{escape(format_soles(total_cost))}</span><span class="kpi-note">{format_integer(functions)} funciones de proyectos de inversión</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_diagnostics(diagnostics: RegionDiagnostics) -> None:
    parts = [f"{format_integer(diagnostics.output_rows)} proyectos de inversión listos para analizar"]
    if diagnostics.swapped_coordinates:
        parts.append(
            f"{format_integer(diagnostics.swapped_coordinates)} coordenadas lat/lon corregidas"
        )
    if diagnostics.wrapped_longitudes:
        parts.append(
            f"{format_integer(diagnostics.wrapped_longitudes)} longitudes normalizadas"
        )
    excluded_quality = diagnostics.invalid_coordinates + diagnostics.out_of_region_coordinates
    if excluded_quality:
        parts.append(
            f"{format_integer(excluded_quality)} coordenadas anómalas excluidas"
        )
    st.caption("Calidad de datos · " + " · ".join(parts))


@st.cache_data(show_spinner=False)
def _image_data_uri(path: str, modified_ns: int) -> str:
    del modified_ns  # Forma parte de la clave de caché para invalidar cambios del archivo.
    mime_type = mimetypes.guess_type(path)[0] or "image/jpeg"
    encoded = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def render_team_section(members: tuple[TeamMember, ...]) -> None:
    st.markdown(
        """
        <section class="team-intro">
            <span class="eyebrow">Acerca del equipo</span>
            <h2>Las personas detrás de APP Territorio Perú</h2>
            <p>Conoce al equipo que integra análisis de inversión pública, lectura territorial y visualización de datos en una experiencia accesible para la toma de decisiones.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    cards: list[str] = []
    image_styles = {
        "Pierina_foto": "object-position:24% 70%;",
        "Lhorena_foto": "object-position:50% 50%;object-fit:contain;padding:28px;",
        "Shampier_foto": "object-position:28% 70%;",
    }
    for member in members:
        if member.image_path is not None and member.image_path.exists():
            image_uri = _image_data_uri(
                str(member.image_path), member.image_path.stat().st_mtime_ns
            )
            image = (
                f'<img class="team-photo" style="{image_styles.get(member.image_reference, "")}" src="{image_uri}" '
                f'alt="Fotografía de {escape(member.full_name, quote=True)}">'
            )
        else:
            initials = "".join(
                part[0].upper()
                for part in (member.first_names, member.last_names)
                if part
            )[:2]
            image = f'<div class="team-photo-fallback">{escape(initials)}</div>'

        if member.linkedin_url.startswith(("https://", "http://")):
            linkedin = (
                f'<a class="linkedin-button" href="{escape(member.linkedin_url, quote=True)}" '
                'target="_blank" rel="noopener noreferrer">LinkedIn <span aria-hidden="true">↗</span></a>'
            )
        else:
            linkedin = '<span class="team-university">Perfil de LinkedIn no disponible</span>'

        cards.append(
            f'<article class="team-card">'
            f'<div class="team-photo-wrap">{image}</div>'
            f'<div class="team-card-body">'
            f'<span class="team-label">Equipo</span>'
            f'<h3>{escape(member.full_name)}</h3>'
            f'<p class="team-university">{escape(member.university)}</p>'
            f'{linkedin}'
            f'</div>'
            f'</article>'
        )

    st.markdown(
        f'<section class="team-grid">{"".join(cards)}</section>',
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
        <div class="footer-note">
            <strong>Metodología.</strong> La app lee exclusivamente <code>data/APP_Peru.xlsx</code> y las bases incluidas en <code>data/Region/</code>, hoja <code>Sheet1</code>. La distancia se recalcula con Haversine desde cada inversión APP; los proyectos de inversión se acumulan por año y no se descarga ningún dataset de datos abiertos. El mapa base usa teselas cartográficas para dar contexto geográfico.
        </div>
        """,
        unsafe_allow_html=True,
    )
