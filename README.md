# MathScribe — Backend

API REST y capa de inteligencia de **MathScribe**, el agente visual multimodal para la
digitalización, conversión a LaTeX y resolución de contenido matemático.

> Universidad del Valle · Programa de Ingeniería de Sistemas · Proyecto Integrador 2 (2026)

Este repositorio implementa la **capa de aplicación** (orquestador FastAPI) y la **capa de
inteligencia** (servicios de reconocimiento y resolución) descritas en la arquitectura
preliminar del proyecto. El cliente SPA vive en el repositorio
[`MathScribe---Frontend`](https://github.com/AirWa1l/MathScribe---Frontend).

## Arquitectura

```
Cliente (SPA)  ──HTTP──▶  app/ (FastAPI · orquestador)
                              │  autenticación · cuotas · trazabilidad
                              ├─▶ services/recognition  (imagen → LaTeX)
                              │       └─ providers: Gemini · GPT-4 Vision · Mathpix
                              └─▶ services/solver       (LLM + SymPy → solución y pasos)

Persistencia:  PostgreSQL (usuarios e historial) · S3 (imágenes)
```

La capa de inteligencia está **desacoplada** detrás de interfaces, de modo que se puede
cambiar de proveedor o añadir un modelo open source sin tocar la API ni el frontend.

## Stack

| Área         | Tecnologías                                        |
| ------------ | -------------------------------------------------- |
| Framework    | Python 3.11+, FastAPI, Uvicorn                     |
| Inteligencia | Google Gemini / GPT-4 Vision, SymPy, Mathpix (opc.)|
| Datos        | PostgreSQL (SQLAlchemy), almacenamiento S3         |
| Calidad      | Ruff, Black, Pytest                                |
| Infra        | Docker, docker-compose, GitHub Actions             |

## Estructura

```
app/                 # Orquestador FastAPI (capa de aplicación)
  core/              #   configuración, logging
  api/v1/endpoints/  #   recognition, solve, auth, history
  schemas/           #   modelos Pydantic (request/response)
  models/            #   modelos SQLAlchemy
  db/                #   sesión y base declarativa
services/
  recognition/       # Agente imagen → LaTeX (interfaz + providers)
  solver/            # Resolución y explicación (LLM + SymPy)
shared/              # Tipos y utilidades compartidas
infra/               # Dockerfile y docker-compose
tests/               # Pruebas con Pytest
```

## Puesta en marcha (desarrollo)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # completar credenciales
uvicorn app.main:app --reload
```

La documentación interactiva queda disponible en `http://localhost:8000/docs`.

> Sin `GEMINI_API_KEY` la API arranca igual: el reconocimiento devuelve LaTeX vacío
> y la explicación conserva los pasos de SymPy, en lugar de fallar. La resolución
> simbólica funciona sin ninguna credencial.

## Despliegue

Desplegado en Render como servicio Docker, con PostgreSQL administrado y
despliegue disparado por el pipeline tras pasar lint, pruebas y cobertura.

- Infraestructura como código: [`render.yaml`](./render.yaml)
- Configuración, secretos y nota sobre permisos de la cuenta:
  [`docs/devops/despliegue-y-permisos.md`](./docs/devops/despliegue-y-permisos.md)

## Convenciones

- Ramas: `main` protegida; `feature/*`, `fix/*`, `ci/*`, `docs/*`, `chore/*`.
- Commits: [Conventional Commits](https://www.conventionalcommits.org/), en español.
- Cada PR ejecuta linters, pruebas y umbral de cobertura antes de fusionar.
