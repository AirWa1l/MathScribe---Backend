# Historias de usuario — MathScribe

**Responsable:** Michael Ramírez (Product Owner)
**Versión:** 1.0 — 21 de julio de 2026

Historias del producto en el formato **Como [ROL] requiero [NECESIDAD] para
[PROPÓSITO]**, con criterios de aceptación verificables. La numeración continúa
la del backlog existente (PB-01 … PB-21), por lo que estas arrancan en **HU-01**
para distinguirlas como historias y no como ítems de backlog.

## Roles

| Rol | Quién es |
|---|---|
| **Estudiante** | Usuario principal: resuelve ejercicios y quiere entender el procedimiento |
| **Docente** | Digitaliza ejercicios manuscritos para material de clase |
| **Usuario con dificultades motrices** | Necesita evitar teclear notación compleja |
| **Equipo técnico** | Opera y evalúa el sistema |

---

## Épica 1 — Captura

### HU-01 · Capturar con la cámara

> **Como** estudiante **requiero** fotografiar una expresión matemática con la
> cámara de mi dispositivo **para** no tener que transcribirla a mano.

**Criterios de aceptación**

- Al pulsar «Usar la cámara» el navegador solicita permiso explícitamente.
- Concedido el permiso, se muestra la vista previa en vivo.
- «Tomar foto» captura el fotograma actual y lo envía a reconocer.
- La cámara se apaga tras capturar y al abandonar la vista.
- El video nunca se transmite: sólo viaja la imagen capturada.

**Estado:** ✅ Implementado · `CameraCapture.tsx`

### HU-02 · Alternativa sin cámara

> **Como** estudiante sin cámara disponible o que denegó el permiso **requiero**
> subir una imagen desde mi dispositivo **para** poder usar la aplicación igual.

**Criterios de aceptación**

- La carga de archivo está visible desde el inicio, no oculta tras un fallo.
- Acepta PNG, JPEG y WebP.
- Si se deniega el permiso de cámara, se explica cómo desbloquearlo y se
  recuerda esta alternativa.

**Estado:** ✅ Implementado · `ImageUploader.tsx`

### HU-03 · Entender por qué falló la cámara

> **Como** estudiante al que no le funciona la cámara **requiero** saber la causa
> concreta **para** saber qué hacer al respecto.

**Criterios de aceptación**

- Se distinguen permiso denegado, ausencia de cámara y navegador sin soporte.
- Cada caso ofrece la acción que corresponde; no se ofrece reintentar cuando no
  cambiaría nada.
- El mensaje se anuncia a los lectores de pantalla.

**Estado:** ✅ Implementado · 5 pruebas asociadas

---

## Épica 2 — Reconocimiento

### HU-04 · Obtener el LaTeX de una expresión manuscrita

> **Como** estudiante **requiero** que el sistema convierta la foto de mi
> ejercicio en notación LaTeX **para** poder usarla en herramientas digitales.

**Criterios de aceptación**

- La imagen se preprocesa con OpenCV antes de enviarse al modelo.
- Se detecta y recorta la región de la expresión, descartando el resto de la hoja.
- La respuesta contiene sólo la expresión, sin delimitadores ni explicaciones.
- El resultado se renderiza con KaTeX y puede copiarse al portapapeles.

**Estado:** ✅ Implementado · `preprocessing.py`, `providers/gemini.py`

### HU-05 · Verificar antes de resolver

> **Como** estudiante **requiero** ver qué entendió el sistema antes de que
> resuelva **para** no recibir la solución correcta de un problema equivocado.

**Criterios de aceptación**

- El LaTeX reconocido se muestra siempre antes de resolver.
- Resolver requiere una acción explícita del usuario.
- Si el reconocimiento es incorrecto, se puede volver a capturar.

**Estado:** ✅ Implementado — es la mitigación del riesgo R-01

### HU-06 · Saber que no se reconoció nada

> **Como** estudiante que fotografió mal **requiero** un aviso claro **para**
> repetir la captura en mejores condiciones.

**Criterios de aceptación**

- Si no hay expresión legible, se avisa y se sugiere qué mejorar.
- No se inventa una expresión: el sistema devuelve vacío antes que alucinar.

**Estado:** ✅ Implementado

---

## Épica 3 — Resolución y explicación

### HU-07 · Resolver la expresión

> **Como** estudiante **requiero** que el sistema resuelva la expresión
> reconocida **para** comprobar si mi resultado es correcto.

**Criterios de aceptación**

- Resuelve ecuaciones, derivadas, integrales y simplificaciones.
- El cálculo lo realiza un motor simbólico determinista, no el modelo de lenguaje.
- Un LaTeX no interpretable devuelve resultado vacío con aviso, sin romperse.

**Estado:** ✅ Implementado · `sympy_solver.py` · 18 pruebas

### HU-08 · Entender el procedimiento

> **Como** estudiante que no comprende el ejercicio **requiero** ver los pasos
> explicados **para** aprender a resolverlo por mi cuenta, no sólo copiar la
> respuesta.

**Criterios de aceptación**

- Se muestran los pasos intermedios en LaTeX, numerados y en orden.
- Cada paso lleva una explicación en español de qué se hace y por qué.
- Si la explicación del modelo no encaja con los pasos calculados, se descarta y
  se conservan las descripciones originales.
- Si el modelo no está disponible, se muestran igualmente los pasos del motor
  simbólico.

**Estado:** ✅ Implementado · `explainer.py` · 16 pruebas

### HU-09 · Recordar que debo verificar

> **Como** estudiante **requiero** que se me recuerde comprobar el resultado
> **para** no dar por bueno un error de reconocimiento.

**Criterios de aceptación**

- Junto al resultado aparece siempre un aviso de verificación.
- El aviso es permanente, no descartable.

**Estado:** ✅ Implementado

---

## Épica 4 — Digitalización (docente)

### HU-10 · Copiar el LaTeX para reutilizarlo

> **Como** docente **requiero** copiar la expresión en LaTeX con un clic **para**
> pegarla en mis materiales de clase sin transcribirla.

**Criterios de aceptación**

- Botón de copia junto al LaTeX en bruto.
- Confirmación visual de que se copió.

**Estado:** ✅ Implementado · `LatexResult.tsx`

---

## Épica 5 — Operación y evaluación

### HU-11 · Conocer el desempeño real del sistema

> **Como** equipo técnico **requiero** medir latencia, uso de recursos y consumo
> del modelo **para** sustentar el análisis de desempeño con datos y no con
> estimaciones.

**Criterios de aceptación**

- Se mide la latencia de cada petición, con percentiles y desglose por ruta.
- Se muestrea CPU y memoria del proceso.
- Se contabilizan los tokens y el costo, separando los de razonamiento.
- El healthcheck y las consultas al propio endpoint se excluyen de la medición.

**Estado:** ✅ Implementado · `metrics.py` · 13 pruebas

### HU-12 · Consultar las métricas desde la interfaz

> **Como** equipo técnico **requiero** ver las métricas en la aplicación **para**
> mostrar el desempeño en vivo durante la demostración.

**Criterios de aceptación**

- Panel colapsable que no interfiere con el flujo principal.
- Sólo consulta al desplegarse, para no alterar lo que mide.
- Si el backend no responde, informa sin romper la aplicación.

**Estado:** ✅ Implementado · `MetricsPanel.tsx` · 8 pruebas

### HU-13 · Cambiar de proveedor de IA sin reescribir

> **Como** equipo técnico **requiero** que el proveedor de reconocimiento sea
> sustituible **para** no quedar atados a un servicio externo.

**Criterios de aceptación**

- Existe una interfaz común que todo proveedor implementa.
- Cambiar de proveedor es cambiar una variable de entorno.
- Una configuración inválida recae en el proveedor por defecto en lugar de
  dejar el sistema sin capacidad de reconocer.

**Estado:** ✅ Implementado · `RecognitionProvider`

### HU-14 · Que un fallo externo no tumbe el servicio

> **Como** estudiante **requiero** que la aplicación siga respondiendo aunque
> falle el servicio de IA **para** no encontrarme una pantalla de error.

**Criterios de aceptación**

- Sin clave, con error de red o cuota agotada, la API responde con resultado
  vacío y registro del incidente, nunca con error 500.
- La resolución simbólica funciona sin ninguna credencial.
- La interfaz comunica el problema y ofrece reintentar.

**Estado:** ✅ Implementado

---

## Épica 6 — Privacidad (transversal)

### HU-15 · Que no se guarde mi imagen

> **Como** estudiante que fotografía su cuaderno **requiero** que la imagen no se
> almacene **para** que un dato personal accidental no quede registrado.

**Criterios de aceptación**

- La imagen se procesa en memoria y se descarta al terminar la petición.
- No se escribe en disco ni en base de datos.
- Sólo se envía al proveedor externo la región recortada, no la foto completa.

**Estado:** ✅ Implementado — ver `responsible-ai.md`

---

## Historias pendientes

Registradas para dar continuidad al producto; ninguna es requisito de la entrega.

### HU-16 · Corregir el LaTeX reconocido

> **Como** estudiante que detecta un error de transcripción **requiero** editar
> el LaTeX antes de resolver **para** corregirlo sin repetir la captura.

**Estado:** ⏳ Pendiente — es la mitigación más valiosa que falta: hoy el usuario
puede detectar el error pero no corregirlo.

### HU-17 · Consultar mi historial

> **Como** estudiante registrado **requiero** ver mis conversiones anteriores
> **para** retomar un ejercicio sin volver a fotografiarlo.

**Estado:** ⏳ Pendiente — despriorizada: el flujo que exige el taller no
requiere cuentas de usuario.

### HU-18 · Recibir sólo una pista

> **Como** estudiante que quiere aprender **requiero** una pista del siguiente
> paso en lugar de la solución completa **para** resolverlo yo mismo.

**Estado:** ⏳ Pendiente — mitigación propuesta frente al riesgo de dependencia.

---

## Trazabilidad

| Épica | Historias | Cobertura |
|---|---|---|
| Captura | HU-01 a HU-03 | 3 de 3 implementadas |
| Reconocimiento | HU-04 a HU-06 | 3 de 3 |
| Resolución y explicación | HU-07 a HU-09 | 3 de 3 |
| Digitalización | HU-10 | 1 de 1 |
| Operación | HU-11 a HU-14 | 4 de 4 |
| Privacidad | HU-15 | 1 de 1 |
| Pendientes | HU-16 a HU-18 | 0 de 3 (fuera de alcance declarado) |

**15 de 15 historias comprometidas están implementadas y cubiertas por pruebas.**
Las tres pendientes se declararon fuera de alcance con justificación, no por
falta de tiempo.

---

## Referencias

- [`problem-definition.md`](./problem-definition.md) — público objetivo y alcance.
- [`../responsible-ai/responsible-ai.md`](../responsible-ai/responsible-ai.md) — HU-15 y las mitigaciones.
- `docs/product/backlog-sprint2.md` (frontend) — backlog PB-01 a PB-21.
- [`../scrum/definition-of-done.md`](../scrum/definition-of-done.md) — criterios de cierre.
