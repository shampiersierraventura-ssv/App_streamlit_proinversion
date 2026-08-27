from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"
PORTFOLIO_PATH = DATA_DIR / "APP_Peru.xlsx"
TEAM_PATH = DATA_DIR / "EQUIPO.xlsx"
REGION_DIR = DATA_DIR / "Region"
TEAM_IMAGES_DIR = APP_DIR / "assets" / "Imagenes"

BUFFER_ORDER = (
    "0–5 km",
    "5–10 km",
    "10–20 km",
    "20–50 km",
    "> 50 km",
)


APP_METADATA: dict[int, dict[str, str]] = {
    1: {
        "name": "COAR Centro",
        "tab": "🏫 COAR Centro · 3",
        "icon": "🏫",
        "map_symbol": "school",
        "color": "#3157D5",
        "soft_color": "#E9EEFF",
        "description": (
            "Infraestructura educativa de alto rendimiento articulada en tres "
            "departamentos del centro y sur del país."
        ),
    },
    2: {
        "name": "Puerto de Salaverry",
        "tab": "⚓ Puerto de Salaverry · 1",
        "icon": "⚓",
        "map_symbol": "harbor",
        "color": "#007C83",
        "soft_color": "#DDF5F3",
        "description": (
            "Modernización portuaria para ampliar la capacidad logística y "
            "multipropósito de La Libertad."
        ),
    },
    3: {
        "name": "ESSALUD",
        "tab": "🏥 ESSALUD · 2",
        "icon": "✚",
        "map_symbol": "hospital",
        "color": "#D63864",
        "soft_color": "#FCE6ED",
        "description": (
            "Dos hospitales especializados para fortalecer la atención de "
            "ESSALUD en Piura y Chimbote."
        ),
    },
}


DEPARTMENT_NAMES = {
    "ANCASH": "Áncash",
    "CUSCO": "Cusco",
    "HUANCAVELICA": "Huancavelica",
    "LA LIBERTAD": "La Libertad",
    "PASCO": "Pasco",
    "PIURA": "Piura",
}


SECTION_NAMES = {
    (1, "PASCO"): "COAR Pasco",
    (1, "HUANCAVELICA"): "COAR Huancavelica",
    (1, "CUSCO"): "COAR Cusco",
    (2, "LA LIBERTAD"): "Terminal Portuario de Salaverry",
    (3, "PIURA"): "Hospital Especializado de Piura",
    (3, "ANCASH"): "Hospital Especializado de Chimbote",
}


@dataclass(frozen=True)
class ProjectRecord:
    app_id: int
    app_name: str
    tab_label: str
    icon: str
    map_symbol: str
    color: str
    soft_color: str
    app_description: str
    section_name: str
    project_name: str
    department: str
    department_display: str
    app_type: str
    sector: str
    initiative_type: str
    modality: str
    phase: str
    owner: str
    status: str
    departmental_investment_usd_m: float
    total_estimated_usd_m: float
    concessionaire: str
    latitude: float
    longitude: float
    award_date: date | None
    technical_sheet_url: str
    database_name: str

    @property
    def key(self) -> str:
        return f"app{self.app_id}-{slugify(self.department)}"

    @property
    def database_filename(self) -> str:
        name = Path(self.database_name).name
        return name if name.lower().endswith(".xlsx") else f"{name}.xlsx"


@dataclass(frozen=True)
class RegionDiagnostics:
    source_rows: int
    output_rows: int
    swapped_coordinates: int
    wrapped_longitudes: int
    invalid_coordinates: int
    out_of_region_coordinates: int
    excluded_non_projects: int
    excluded_app_rows: int

    @property
    def excluded_rows(self) -> int:
        return self.source_rows - self.output_rows


@dataclass(frozen=True)
class TeamMember:
    first_names: str
    last_names: str
    university: str
    linkedin_url: str
    image_reference: str
    image_path: Path | None

    @property
    def full_name(self) -> str:
        return f"{self.first_names} {self.last_names}".strip()


def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]+", "_", text.upper()).strip("_")


def slugify(value: object) -> str:
    return normalize_name(value).lower().replace("_", "-")


def clean_text(value: object, default: str = "No disponible") -> str:
    if value is None or pd.isna(value):
        return default
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    return cleaned or default


def _number(value: object) -> float:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(parsed) else float(parsed)


def _date(value: object) -> date | None:
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    return None if pd.isna(parsed) else parsed.date()


def _required(row: pd.Series, column: str) -> object:
    if column not in row.index:
        raise ValueError(f"APP_Peru.xlsx no contiene la columna requerida: {column}")
    return row[column]


def ensure_app_local_path(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(APP_DIR.resolve()):
        raise ValueError(f"{label} debe permanecer dentro de la carpeta de la aplicación: {resolved}")
    return resolved


@st.cache_data(show_spinner=False)
def load_portfolio(path: Path = PORTFOLIO_PATH) -> tuple[ProjectRecord, ...]:
    path = ensure_app_local_path(path, "El catálogo de APP")
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el catálogo de APP: {path}")

    frame = pd.read_excel(path, sheet_name="APP")
    frame.columns = [normalize_name(column) for column in frame.columns]
    records: list[ProjectRecord] = []

    for _, row in frame.iterrows():
        app_id = int(_number(_required(row, "ID")))
        department = clean_text(_required(row, "DEPARTAMENTO")).upper()
        meta = APP_METADATA.get(
            app_id,
            {
                "name": clean_text(_required(row, "NOMBRE_CORTO")),
                "tab": clean_text(_required(row, "NOMBRE_CORTO")),
                "icon": "●",
                "map_symbol": "marker",
                "color": "#3157D5",
                "soft_color": "#E9EEFF",
                "description": "Inversión mediante asociación público-privada.",
            },
        )
        records.append(
            ProjectRecord(
                app_id=app_id,
                app_name=meta["name"],
                tab_label=meta["tab"],
                icon=meta["icon"],
                map_symbol=meta["map_symbol"],
                color=meta["color"],
                soft_color=meta["soft_color"],
                app_description=meta["description"],
                section_name=SECTION_NAMES.get(
                    (app_id, department),
                    f"{clean_text(_required(row, 'NOMBRE_CORTO'))} · {DEPARTMENT_NAMES.get(department, department.title())}",
                ),
                project_name=clean_text(_required(row, "PROYECTO")),
                department=department,
                department_display=DEPARTMENT_NAMES.get(department, department.title()),
                app_type=clean_text(_required(row, "TIPO")),
                sector=clean_text(_required(row, "SECTOR")),
                initiative_type=clean_text(_required(row, "TIPO_DE_INICIATIVA")),
                modality=clean_text(_required(row, "MODALIDAD")),
                phase=clean_text(_required(row, "FASE")),
                owner=clean_text(_required(row, "TITULAR")),
                status=clean_text(_required(row, "SITUACION_ACTUAL")),
                departmental_investment_usd_m=_number(
                    _required(row, "MONTO_INVERSION_DEPARTAMENTAL_US_MILLONES")
                ),
                total_estimated_usd_m=_number(
                    _required(row, "MONTO_TOTAL_ESTIMADA_US_MILLONES")
                ),
                concessionaire=clean_text(_required(row, "CONCESIONARIO")),
                latitude=_number(_required(row, "LATITUD")),
                longitude=_number(_required(row, "LONGITUD")),
                award_date=_date(_required(row, "FECHA_BUENA_PRO_ADJUDICACION")),
                technical_sheet_url=clean_text(_required(row, "FICHA_TECNICA"), default=""),
                database_name=clean_text(_required(row, "BASE_DE_DATOS"), default=""),
            )
        )

    return tuple(records)


def group_portfolio(records: tuple[ProjectRecord, ...]) -> dict[int, tuple[ProjectRecord, ...]]:
    grouped: dict[int, list[ProjectRecord]] = {}
    for record in records:
        grouped.setdefault(record.app_id, []).append(record)
    return {app_id: tuple(items) for app_id, items in sorted(grouped.items())}


def resolve_team_image(image_reference: str) -> Path | None:
    reference = Path(clean_text(image_reference, default="")).name
    if not reference or not TEAM_IMAGES_DIR.exists():
        return None

    allowed_extensions = (".png", ".jpg", ".jpeg", ".webp")
    requested = Path(reference)
    candidate_names = (
        [requested.name]
        if requested.suffix.lower() in allowed_extensions
        else [f"{requested.name}{extension}" for extension in allowed_extensions]
    )
    available = {
        path.name.casefold(): path.resolve()
        for path in TEAM_IMAGES_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in allowed_extensions
    }
    image_root = TEAM_IMAGES_DIR.resolve()
    for candidate_name in candidate_names:
        candidate = available.get(candidate_name.casefold())
        if candidate is not None and candidate.parent == image_root:
            return candidate
    return None


@st.cache_data(show_spinner=False)
def load_team(path: Path = TEAM_PATH) -> tuple[TeamMember, ...]:
    path = ensure_app_local_path(path, "El catálogo del equipo")
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el catálogo del equipo: {path}")

    frame = pd.read_excel(path, sheet_name="Hoja1")
    frame.columns = [normalize_name(column) for column in frame.columns]
    linkedin_column = "LINKEDLN" if "LINKEDLN" in frame.columns else "LINKEDIN"
    required = {"NOMBRES", "APELLIDOS", "UNIVERSIDAD", linkedin_column, "IMAGEN_VINCULANTE"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(
            f"EQUIPO.xlsx no contiene columnas requeridas: {', '.join(sorted(missing))}"
        )

    members: list[TeamMember] = []
    for _, row in frame.iterrows():
        image_reference = clean_text(row["IMAGEN_VINCULANTE"], default="")
        members.append(
            TeamMember(
                first_names=clean_text(row["NOMBRES"]),
                last_names=clean_text(row["APELLIDOS"]),
                university=clean_text(row["UNIVERSIDAD"]),
                linkedin_url=clean_text(row[linkedin_column], default=""),
                image_reference=image_reference,
                image_path=resolve_team_image(image_reference),
            )
        )
    return tuple(members)


def resolve_region_path(database_name: str) -> Path:
    filename = Path(clean_text(database_name, default="")).name
    if not filename:
        raise ValueError("La fila del proyecto no especifica BASE DE DATOS.")
    if not filename.lower().endswith(".xlsx"):
        filename = f"{filename}.xlsx"

    region_root = REGION_DIR.resolve()
    candidate = (REGION_DIR / filename).resolve()
    if candidate.parent != region_root:
        raise ValueError(f"Nombre de base regional no permitido: {database_name}")
    if not candidate.exists():
        raise FileNotFoundError(f"No se encontró la base regional: {candidate}")
    return candidate


def haversine_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: np.ndarray | pd.Series,
    longitude_2: np.ndarray | pd.Series,
) -> np.ndarray:
    radius_km = 6_371.0
    lat_1 = np.radians(latitude_1)
    lon_1 = np.radians(longitude_1)
    lat_2 = np.radians(pd.to_numeric(latitude_2, errors="coerce").to_numpy())
    lon_2 = np.radians(pd.to_numeric(longitude_2, errors="coerce").to_numpy())
    delta_lat = lat_2 - lat_1
    delta_lon = lon_2 - lon_1
    value = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(lat_1) * np.cos(lat_2) * np.sin(delta_lon / 2) ** 2
    )
    return radius_km * 2 * np.arcsin(np.sqrt(value))


REGION_COLUMNS = {
    "CODIGO_UNICO",
    "NOMBRE_INVERSION",
    "FUNCION",
    "AÑO",
    "LATITUD",
    "LONGITUD",
    "COSTO_ACTUALIZADO",
    "TIPO_INVERSION",
    "DES_MODALIDAD",
    "ESTADO",
    "SITUACION",
    "ENTIDAD",
    "DEPARTAMENTO",
    "PROVINCIA",
    "DISTRITO",
}


@st.cache_data(show_spinner=False, max_entries=12)
def load_region_data(
    database_name: str,
    anchor_latitude: float,
    anchor_longitude: float,
) -> tuple[pd.DataFrame, RegionDiagnostics]:
    path = resolve_region_path(database_name)
    frame = pd.read_excel(
        path,
        sheet_name="Sheet1",
        usecols=lambda column: str(column) in REGION_COLUMNS,
    )
    frame.columns = [normalize_name(column) for column in frame.columns]

    required = {
        "CODIGO_UNICO",
        "NOMBRE_INVERSION",
        "FUNCION",
        "ANO",
        "LATITUD",
        "LONGITUD",
        "COSTO_ACTUALIZADO",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(
            f"{path.name} / Sheet1 no contiene columnas requeridas: {', '.join(sorted(missing))}"
        )

    source_rows = len(frame)
    excluded_non_projects = 0
    if "TIPO_INVERSION" in frame.columns:
        project_mask = (
            frame["TIPO_INVERSION"].fillna("").map(normalize_name)
            == "PROYECTO_DE_INVERSION"
        )
        excluded_non_projects = int((~project_mask).sum())
        frame = frame.loc[project_mask].copy()

    excluded_app_rows = 0
    if "DES_MODALIDAD" in frame.columns:
        app_mask = frame["DES_MODALIDAD"].fillna("").str.contains(
            "APP", case=False, na=False
        )
        excluded_app_rows = int(app_mask.sum())
        frame = frame.loc[~app_mask].copy()

    frame["LATITUD"] = pd.to_numeric(frame["LATITUD"], errors="coerce")
    frame["LONGITUD"] = pd.to_numeric(frame["LONGITUD"], errors="coerce")
    frame["ANO"] = pd.to_numeric(frame["ANO"], errors="coerce")
    frame["COSTO_ACTUALIZADO"] = pd.to_numeric(
        frame["COSTO_ACTUALIZADO"], errors="coerce"
    ).fillna(0.0)

    # Corrige exclusivamente longitudes desplazadas una vuelta completa
    # (por ejemplo, -438° -> -78°) cuando el resultado cae en Perú.
    wrap_candidate = frame["LONGITUD"].abs().between(180.0, 540.0)
    wrapped_values = ((frame.loc[wrap_candidate, "LONGITUD"] + 180.0) % 360.0) - 180.0
    wrap_valid = wrapped_values.between(-82.5, -67.0)
    wrapped_indexes = wrapped_values.index[wrap_valid]
    frame.loc[wrapped_indexes, "LONGITUD"] = wrapped_values.loc[wrapped_indexes]
    wrapped_longitudes = int(len(wrapped_indexes))

    # Algunas bases contienen pares latitud/longitud intercambiados. Solo se
    # corrigen cuando el intercambio produce inequívocamente un punto en Perú.
    valid_peru = frame["LATITUD"].between(-20.0, 0.5) & frame["LONGITUD"].between(
        -82.5, -67.0
    )
    swapped = (
        ~valid_peru
        & frame["LATITUD"].between(-82.5, -67.0)
        & frame["LONGITUD"].between(-20.0, 0.5)
    )
    swapped_coordinates = int(swapped.sum())
    original_latitude = frame.loc[swapped, "LATITUD"].copy()
    frame.loc[swapped, "LATITUD"] = frame.loc[swapped, "LONGITUD"].to_numpy()
    frame.loc[swapped, "LONGITUD"] = original_latitude.to_numpy()

    valid_peru = (
        frame["LATITUD"].between(-20.0, 0.5)
        & frame["LONGITUD"].between(-82.5, -67.0)
        & frame["ANO"].between(1900, 2100)
    )
    invalid_coordinates = int((~valid_peru).sum())
    frame = frame.loc[valid_peru].copy()
    frame["ANO"] = frame["ANO"].astype(int)

    frame["DIST_KM"] = haversine_km(
        anchor_latitude,
        anchor_longitude,
        frame["LATITUD"],
        frame["LONGITUD"],
    )

    # Los archivos están prefiltrados por departamento. Una distancia superior
    # a 350 km frente a su APP eje señala coordenadas asignadas a otra región.
    in_region = frame["DIST_KM"].le(350.0)
    out_of_region_coordinates = int((~in_region).sum())
    frame = frame.loc[in_region].copy()

    frame["FUNCION"] = frame["FUNCION"].map(lambda value: clean_text(value, "Sin clasificar"))
    frame["NOMBRE_INVERSION"] = frame["NOMBRE_INVERSION"].map(clean_text)
    for column in ("ENTIDAD", "ESTADO", "SITUACION", "DEPARTAMENTO", "PROVINCIA", "DISTRITO"):
        if column in frame.columns:
            frame[column] = frame[column].map(clean_text)

    frame["BUFFER"] = pd.Categorical(
        np.select(
            [
                frame["DIST_KM"].le(5),
                frame["DIST_KM"].le(10),
                frame["DIST_KM"].le(20),
                frame["DIST_KM"].le(50),
            ],
            list(BUFFER_ORDER[:4]),
            default=BUFFER_ORDER[4],
        ),
        categories=BUFFER_ORDER,
        ordered=True,
    )
    frame = frame.sort_values(["ANO", "FUNCION", "CODIGO_UNICO"]).reset_index(drop=True)

    diagnostics = RegionDiagnostics(
        source_rows=source_rows,
        output_rows=len(frame),
        swapped_coordinates=swapped_coordinates,
        wrapped_longitudes=wrapped_longitudes,
        invalid_coordinates=invalid_coordinates,
        out_of_region_coordinates=out_of_region_coordinates,
        excluded_non_projects=excluded_non_projects,
        excluded_app_rows=excluded_app_rows,
    )
    return frame, diagnostics
