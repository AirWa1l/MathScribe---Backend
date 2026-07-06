# CLAUDE.md — Backend

Guía para sesiones con Claude Code en el backend de MathScribe.

## Qué es esto

API REST (FastAPI) y capa de inteligencia de MathScribe. Convierte imágenes de
expresiones matemáticas a LaTeX y, opcionalmente, las resuelve y explica paso a paso.

## Mapa del código

- `app/` — orquestador FastAPI (capa de aplicación).
  - `app/main.py` — entrada de la app; CORS y registro de routers.
  - `app/api/v1/endpoints/` — `recognition`, `solve`, `auth`, `history`.
  - `app/core/config.py` — configuración desde `.env`.
  - `app/schemas/` — modelos Pydantic; `app/models/` — modelos SQLAlchemy.
- `services/recognition/` — agente imagen → LaTeX; interfaz `base.py` + `providers/`.
- `services/solver/` — resolución con SymPy + explicación con LLM.
- `shared/` — tipos y constantes compartidas.

## Arquitectura

La capa de inteligencia está desacoplada detrás de interfaces. Para añadir un proveedor
de reconocimiento, implementa `RecognitionProvider` en `services/recognition/providers/`
y regístralo en `services/recognition/service.py`. No acoples el endpoint a un proveedor
concreto.

## Comandos

```bash
uvicorn app.main:app --reload   # servidor de desarrollo
pytest                          # pruebas
ruff check . && black .         # lint y formato
```

## Verificación antes de commit (obligatoria)

Antes de crear cualquier commit, ejecuta los mismos checks que corre el pipeline
(`.github/workflows/ci.yml`) y confirma que los tres pasan en verde. Nunca se hace
commit con alguno de estos fallando; corrige la causa primero.

```bash
ruff check .        # lint (0 errores)
black --check .     # formato (sin reformateos pendientes)
pytest              # pruebas (todas en verde)
```

Si `black --check .` reporta archivos, aplica `black .` y vuelve a verificar.
Esto evita romper el pipeline al empujar la rama.

## Convenciones

- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`…).
- Ramas `feature/*` y `fix/*`; `main` protegida.
- Docstrings y comentarios en español, alineados con la documentación del proyecto.

> Estado actual: andamiaje. Los servicios devuelven datos de ejemplo; la integración
> real con proveedores de IA, base de datos y S3 está pendiente.
