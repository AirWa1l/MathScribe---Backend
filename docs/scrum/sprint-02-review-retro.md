# Sprint 2 — Review & Retrospective

**Periodo:** 7 – 13 de julio de 2026
**Sprint goal:** *Integración multimodal y calidad* — pasar del andamiaje a un
flujo funcional de punta a punta, con métricas, IA responsable, despliegue en la
nube y cobertura ≥ 50%.
**Facilitador:** Daniel Rojas Barreneche (Scrum Master)
**Participantes:** los cinco integrantes del equipo.

---

## 1. Qué se planeó

Doce ítems, listados en [`sprint-02-planning.md`](./sprint-02-planning.md), con
prioridad alta en el flujo funcional (ítems 1–3) y la cobertura (ítem 9).

## 2. Qué se logró

| # | Ítem | Estado | Evidencia |
|---|---|---|---|
| 1 | Llamada real a Gemini Vision | ✅ Completado | `feature/be-gemini-real` · PR #7 |
| 2 | Resolución simbólica con SymPy | ✅ Completado | `feature/be-sympy-solver` · PR #9 |
| 3 | Explicación paso a paso | ✅ Completado | `feature/be-explainer-gemini` · PR #10 |
| 5 | Métricas de inferencia | ✅ Completado | `feature/be-metrics` · PR #13 |
| 7 | Despliegue desde el pipeline | ✅ Completado | `ci/be-cd-pipeline` · PR #11 |
| 8 | IA responsable | ✅ Completado | `docs/responsible-ai` · PR #12 |
| 9 | Cobertura ≥ 50% | ✅ Superado: **96%** | `test/be-suite-expand` · PR #14 |
| 10 | Flujo de resolución en el frontend | ✅ Completado | `feature/fe-solve-flow` · PR #9 (frontend) |
| 12 | Diagrama C4 | ✅ Completado | `docs/c4-architecture` |

Además, sin estar planificado:

- Detección de ROI con OpenCV por análisis de contornos.
- Estados de error diferenciados y accesibilidad en el frontend.
- Panel de métricas en la interfaz.
- Estrategia de prompting y análisis de costos documentados.

## 3. Qué quedó pendiente (y por qué)

| # | Ítem | Motivo |
|---|---|---|
| 4 | Autenticación real con JWT y persistencia | **Decisión de priorización.** El flujo que exige el taller —cámara → visión → IA → respuesta— no necesita cuentas de usuario. Se prefirió invertir en robustez y métricas del flujo principal |
| 6 | Docker Compose full-stack | El `docker-compose` existente cubre API y base de datos. Añadir el frontend aportaba poco, al desplegarse como sitio estático |
| 11 | Mockups | Se cubre al final del Sprint 3 documentando la interfaz ya construida, en lugar de diseñar prototipos de algo que ya existe |

Ninguno de los tres bloquea la entrega. El 4 y el 6 se reclasifican como mejoras
posteriores; el 11 pasa al Sprint 3.

## 4. Métricas del sprint

| Indicador | Sprint 1 | Sprint 2 |
|---|---|---|
| Ítems completados | 8 de 10 | 9 de 12 |
| Cobertura de pruebas (backend) | ~40% | **96%** |
| Pruebas automatizadas | 12 | 116 |
| Sistema desplegado | ❌ | ✅ |
| Flujo funcional de extremo a extremo | ❌ | ✅ |

## 5. Retrospectiva

### Qué funcionó bien

**Una rama por tarea con autoría individual.** Facilitó trabajar en paralelo sin
pisarse y, de paso, dejó evidencia verificable de la participación de cada
integrante.

**El pipeline atrapó lo que las pruebas locales no podían.** Un fallo de
resolución de dependencias hacía que el entorno local y el del CI instalaran
versiones distintas del SDK de Gemini. El código funcionaba en local y fallaba
en el pipeline; sin CI habría llegado a producción sin que nadie lo notara.

**Separar el cálculo de la redacción.** La decisión de que SymPy calcule y el
modelo sólo narre simplificó las pruebas —lo determinista se verifica
directamente— y eliminó por diseño la alucinación matemática.

### Qué no funcionó

**Diagnóstico por síntomas.** El fallo de dependencias costó tres intentos: los
dos primeros atacaron el error visible (un campo del SDK) en lugar de preguntar
por qué el entorno del CI difería del local. Mirar la versión instalada en el
primer log habría ahorrado dos iteraciones.

**Estimaciones optimistas.** Se planificaron doce ítems para una semana y se
cerraron nueve. Los tres restantes no eran críticos, pero la planificación no
distinguió lo imprescindible de lo deseable.

**Dependencias externas descubiertas tarde.** La necesidad de permisos de
administración sobre la cuenta de GitHub para vincular Render apareció al
intentar desplegar, no al planificar.

### Acciones para el Sprint 3

| Acción | Responsable |
|---|---|
| Ante un fallo que sólo ocurre en CI, comparar primero las versiones instaladas | Todo el equipo |
| Marcar en el planning qué ítems son imprescindibles para la entrega | Daniel |
| Fijar versiones mínimas de las dependencias críticas, no sólo el rango mayor | Adrián |
| Identificar en el planning las dependencias que requieren permisos de terceros | Daniel |

## 6. Nota de proceso

El equipo mantiene la distribución de roles descrita en
[`sprint-01-review-retro.md`](./sprint-01-review-retro.md) §5. Durante este
sprint se confirmó que la carga de backend es la mayor del proyecto, por lo que
QA asumió también parte de la verificación de la capa de inteligencia,
escribiendo pruebas que destaparon dos defectos reales en el cálculo de costos y
en la configuración del modelo.
