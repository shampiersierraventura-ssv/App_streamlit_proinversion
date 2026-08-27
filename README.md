# APP Territorio Perú

Aplicación Streamlit construida a partir de la lógica cartográfica de `01_ProInversion_lineatiempo.ipynb`.

## Qué incluye

- Tres pestañas APP: COAR Centro, Puerto de Salaverry y ESSALUD.
- Secciones vinculantes: 3 para COAR, 1 para Salaverry y 2 para ESSALUD.
- Sección independiente `Acerca del Equipo`, alimentada por `EQUIPO.xlsx` y sus imágenes vinculantes.
- Relación automática con `data/APP_Peru.xlsx` mediante la columna `BASE DE DATOS`.
- Mapas con anillos de 5, 10, 20 y 50 km, línea de tiempo acumulativa 2017–2026 y filtro por función.
- Globo temático para colegio, puerto o salud en lugar de la estrella del notebook.
- Fondo cartográfico Carto y alternativa `Sin conexión` que mantiene visibles anillos, proyectos y pictogramas sin teselas web.
- Ficha explicativa a la izquierda del mapa y enlace oficial de ficha técnica al final.
- Montos uniformes en millones (`MM`), con coma para miles y punto para decimales.
- Lectura exclusiva de archivos incluidos en esta carpeta. La aplicación no descarga datasets del MEF.

## Estructura esperada

```text
app_streamlit_proinversion/
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── app_core/
├── assets/
│   └── Imagenes/
│       └── *.{png,jpeg}
├── data/
│   ├── APP_Peru.xlsx
│   ├── EQUIPO.xlsx
│   └── Region/
│       └── df_region_final_*.xlsx
└── tests/
```

## Ejecutar

Desde `app_streamlit_proinversion`:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Desplegar en Streamlit Community Cloud

1. Publica **el contenido de esta carpeta** como raíz de un repositorio GitHub.
2. En Streamlit Community Cloud selecciona el repositorio y `app.py` como archivo principal.
3. No necesitas cargar archivos adicionales: catálogo, bases regionales, equipo, imágenes, tema y dependencias ya están incluidos.

El fondo Carto usa teselas web para aportar contexto geográfico. Todos los datos analíticos permanecen locales y el modo `Sin conexión` conserva la visualización sin esas teselas.
