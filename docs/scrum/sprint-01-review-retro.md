# Sprint 1 — Review & Retrospective

**Periodo:** 30 de junio – 6 de julio de 2026
**Sprint goal:** *Core Visual Intelligence Development* — dejar el andamiaje del
producto, integrar un modelo/librería de visión **open source** en el flujo y
tener Docker y CI/CD iniciales.

> Nota de trazabilidad: los PR se enlazan por nombre de rama. Cuando estén
> abiertos en GitHub, reemplazar `(rama: …)` por el enlace real del PR.

## 1. Qué se planeó

- Desarrollo frontend (uploader de imagen, render de LaTeX).
- Captura de video/cámara.
- Integración de un modelo/librería open source de visión computacional.
- Desarrollo backend (API REST + capa de inteligencia desacoplada).
- Docker inicial.
- CI/CD inicial (lint + formato + pruebas).

## 2. Qué se logró

| Ítem | Responsable | Estado | Evidencia |
|---|---|---|---|
| Andamiaje backend (FastAPI, routers, modelos, servicios desacoplados) | Adrián | ✅ | Estructura inicial del repo backend |
| Docker inicial (Dockerfile + `docker-compose.yml` con Postgres) | Adrián | ✅ | `infra/` |
| CI/CD inicial (lint + formato + pytest en cada push/PR) | Adrián / Daniel | ✅ | `.github/workflows/ci.yml` |
| **Preprocesamiento de visión open source (OpenCV)** en el flujo de reconocimiento | Adrián | ✅ | (rama: `feature/be-opencv-preprocessing`) |
| Suite de pruebas base backend (solve, auth, history, preprocessing) — de 2 a 11 pruebas | Juan Fernando | ✅ | (rama: `test/be-baseline-suite`) |
| Artefactos Scrum (DoD, cierre Sprint 1, planning Sprint 2) | Daniel | ✅ | (rama: `docs/scrum-artifacts-sprint1-dod`) |
| Uploader de imagen y render de LaTeX (frontend) | Alejandra | ✅ | Repo frontend (ya existían) |
| Captura de cámara (frontend) | Alejandra | ✅ | Repo frontend (rama de captura) |
| Documentación de producto / riesgos | Michael | ✅ | Repo de producto |

El requisito de rúbrica de mayor peso (uso obligatorio de una librería de visión
open source, ~15%) quedó cubierto con el paso de **OpenCV** que limpia la imagen
antes de enviarla al proveedor multimodal, manteniendo el flujo
**Cámara → Visión (OpenCV) → LLM → Respuesta**.

## 3. Qué quedó pendiente (y por qué)

Todo lo siguiente está **agendado por el propio taller para el Sprint 2
(7–13 de julio)**, no es atraso:

- Llamada real a Gemini Vision (hoy el proveedor devuelve un stub).
- Resolución simbólica real con SymPy y explicación paso a paso vía LLM.
- Autenticación real (hash de contraseña, JWT, persistencia en PostgreSQL).
- Métricas de inferencia (latencia, CPU, memoria, costo por llamada).
- Despliegue en la nube (Render/Railway) desde el pipeline.
- Cobertura de pruebas hasta el 50% exigido por la rúbrica.

## 4. Retrospectiva

**Qué funcionó**
- Trabajar en ramas paralelas por rol (backend, visión, QA, frontend, Scrum)
  evitó bloqueos y mantuvo `main` estable.
- La capa de inteligencia desacoplada detrás de interfaces permitió insertar el
  paso de OpenCV sin tocar la API ni el frontend.

**Qué mejorar**
- Empezar antes la integración de visión open source: es el ítem más pesado en la
  rúbrica y se cerró el último día del sprint.
- Definir de entrada las firmas compartidas (p. ej. `preprocess()`) para que QA
  no tenga que esperar para escribir pruebas.

## 5. Nota de proceso — composición del equipo

El taller sugiere equipos de **tres** integrantes y el equipo tiene **cinco**.
La distribución de los seis roles sugeridos (backend, frontend, visión,
integración multimodal, DevOps/cloud, gestión Scrum) se repartió de forma
intencional entre las cinco personas:

- **Adrián** — Backend + visión (OpenCV, integración multimodal).
- **Alejandra** — Frontend.
- **Michael** — Producto, riesgos e IA responsable.
- **Juan Fernando** — QA / pruebas automatizadas.
- **Daniel** — Scrum Master + DevOps/despliegue.

Se deja constancia aquí (y se comentará con el profesor si hay ocasión) para que
quede claro que la repartición de responsabilidades fue deliberada.
