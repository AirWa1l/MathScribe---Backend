# Sprint 2 — Planning

**Periodo:** 7 – 13 de julio de 2026
**Sprint goal:** *Integración multimodal y calidad* — pasar del andamiaje a un
flujo funcional de punta a punta (imagen real → LaTeX → resolución → explicación),
con métricas, IA responsable, despliegue en la nube y cobertura de pruebas ≥ 50%.

## Backlog del sprint

Cada ítem toma como base las ramas ya listadas en `plan_backend.md` y
`plan_frontend.md` bajo "Sprint 2".

| # | Ítem | Responsable | Rama sugerida | Criterio de aceptación (resumen) |
|---|---|---|---|---|
| 1 | Llamada real a Gemini Vision (reemplaza el stub) | Adrián | `feature/be-gemini-real-call` | Una imagen real devuelve LaTeX del modelo; clave por `.env`. |
| 2 | Resolución simbólica con SymPy (`solve_expression`) | Adrián | `feature/be-sympy-solver` | Parseo LaTeX → SymPy → resultado y pasos verificables. |
| 3 | Explicación paso a paso vía LLM (`explain`) | Adrián | `feature/be-explainer-llm` | Los pasos de SymPy se redactan en lenguaje natural. |
| 4 | Auth real: hash de contraseña, JWT, persistencia en Postgres | Adrián | `feature/be-auth-db-wiring` | Register/login reales contra la base de datos. |
| 5 | Métricas de inferencia (latencia, CPU, memoria, costo) | Adrián / Daniel | `feature/be-metrics` | Cada llamada instrumentada y observable en logs/endpoint. |
| 6 | Docker Compose full-stack (API + Postgres + Frontend) | Adrián | `feature/be-docker-compose-fullstack` | `docker compose up` levanta el sistema completo. |
| 7 | Despliegue en la nube desde el pipeline (Render/Railway) | Adrián / Daniel | `feature/be-cicd-deploy` | Merge a `main` despliega automáticamente. |
| 8 | IA responsable (privacidad, sesgos, mitigación) | Michael / Daniel | `docs/be-responsible-ai` | Sección documentada en el repo. |
| 9 | Cobertura de pruebas ≥ 50% ejecutada por CI | Juan Fernando | `test/be-coverage-50` | `pytest --cov` reporta ≥ 50% en CI. |
| 10 | Flujo de resolución en el frontend | Alejandra | (repo frontend) | La UI resuelve y muestra la explicación paso a paso. |
| 11 | Mockups y diseño de API | Alejandra / Michael | (repo frontend / docs) | Mockups y contrato de API documentados. |
| 12 | Diagrama C4 real del sistema | Daniel / Michael | `docs/be-c4-architecture` | C4 (contexto + contenedores) documentado. |

## Capacidad y foco

- **Prioridad alta:** ítems 1–3 (flujo funcional imagen → LaTeX → resolución) y 9
  (cobertura), porque son los que más pesan en rúbrica y desbloquean la demo.
- **Prioridad media:** 4, 5, 6.
- **Prioridad de cierre de sprint:** 7, 8, 12 (despliegue, IA responsable, C4).

## Definition of Done

Aplica la [Definition of Done](definition-of-done.md) del equipo a cada ítem
antes de darlo por cerrado.
