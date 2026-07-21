# Sprint 3 — Planning

**Periodo:** 14 – 21 de julio de 2026 (sprint de cierre)
**Sprint goal:** *Cerrar la entrega* — completar la documentación exigida,
consolidar la evidencia de proceso y dejar el sistema listo para la
demostración y la sustentación técnica.
**Facilitador:** Daniel Rojas Barreneche (Scrum Master)

---

## 1. Contexto

El Sprint 2 cerró con el producto **funcional y desplegado**: el flujo cámara →
OpenCV → Gemini → SymPy → explicación opera de extremo a extremo, con CI/CD y
96% de cobertura. Este sprint no añade capacidades al producto: completa lo que
falta para que el trabajo sea **evaluable y sustentable**.

Aplicando la acción acordada en la retrospectiva anterior, cada ítem se marca
como **imprescindible** para la entrega o **deseable**.

## 2. Backlog del sprint

| # | Ítem | Responsable | Rama | Prioridad | Criterio de aceptación |
|---|---|---|---|---|---|
| 1 | Arquitectura C4 (3 niveles) y diseño cloud-native | Daniel | `docs/c4-architecture` | **Imprescindible** | Los tres niveles documentados y coherentes con el despliegue real |
| 2 | Métricas técnicas: instrumentación y endpoint | Adrián | `feature/be-metrics` | **Imprescindible** | `/api/v1/metrics` reporta latencia, CPU, memoria, tokens y costo reales |
| 3 | Panel de métricas en la interfaz | Alejandra | `feature/fe-metrics-dashboard` | **Imprescindible** | Muestra las cifras del backend y maneja el error si no responde |
| 4 | Estrategia de prompting multimodal | Michael | `docs/prompting-y-costos` | **Imprescindible** | Documenta los prompts reales y su justificación |
| 5 | Análisis de costos de la API | Michael | `docs/prompting-y-costos` | **Imprescindible** | Cifras basadas en tarifas vigentes y consumo medido |
| 6 | Ampliar cobertura y elevar el umbral del CI | Juan Fernando | `test/be-suite-expand` | **Imprescindible** | Cobertura ≥ 85% verificada por el pipeline |
| 7 | Historias de usuario y backlog consolidado | Michael | `docs/user-stories-backlog` | **Imprescindible** | Formato *Como/requiero/para* con criterios de aceptación |
| 8 | Artefactos Scrum: review, retro y planning | Daniel | `docs/scrum-sprint2-3` | **Imprescindible** | Evidencia completa de los eventos del marco |
| 9 | Mockups y documentación de la interfaz | Daniel / Alejandra | `docs/mockups` | **Imprescindible** | Wireframes y capturas de la interfaz desplegada |
| 10 | Documento técnico integrador | Michael | `docs/technical-document` | **Imprescindible** | Cubre los nueve apartados exigidos |
| 11 | Documentar el despliegue y sus restricciones | Daniel | `docs/despliegue-permisos` | **Imprescindible** | Configuración reproducible por cualquiera del equipo |
| 12 | **Video demo técnico (10–15 min)** | **Todo el equipo** | — | **Imprescindible** | Todos los integrantes participan; cubre problema, arquitectura, funcionamiento, DevOps, métricas e IA responsable |
| 13 | Autenticación real y persistencia del historial | Adrián | `feature/be-auth-db` | Deseable | Arrastrado del Sprint 2; no lo exige el flujo del taller |
| 14 | Almacenamiento de imágenes en S3 | Adrián | `feature/be-s3-storage` | Deseable | Contradice parcialmente la política de no persistir imágenes |
| 15 | Smoke test contra el despliegue | Juan Fernando | `test/e2e-smoke` | Deseable | Verifica que producción responde |

## 3. Riesgo principal del sprint

**El ítem 12 es el único que depende de coordinar a las cinco personas a la vez**
y el único que no puede recuperarse si se deja para el final: exige el sistema
desplegado y la disponibilidad simultánea del equipo. Se agenda con prioridad
sobre los ítems de documentación, que sí admiten trabajo asíncrono.

Segundo riesgo: los servicios del plan gratuito se suspenden tras 15 minutos de
inactividad. **Mitigación:** abrir la aplicación unos minutos antes de grabar y
antes de sustentar.

## 4. Capacidad

Sprint corto —ocho días con la entrega dentro— y mayoritariamente documental.
La carga se reparte de forma que ningún integrante bloquee a otro: los
documentos no comparten archivos y el código restante es marginal.

## 5. Definition of Done

Aplica la [Definition of Done](./definition-of-done.md), actualizada en este
sprint con el umbral de cobertura y el despliegue automatizado.

Para los ítems documentales se añade un criterio: **las cifras y afirmaciones
deben poder verificarse contra el sistema real**. No se aceptan datos estimados
donde exista una medición disponible.
