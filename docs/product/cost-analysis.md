# Análisis de costos de la API

**Responsable:** Michael Ramírez (Product Owner)
**Versión:** 1.0 — 21 de julio de 2026

Costo de operar MathScribe, con las tarifas vigentes del modelo y el consumo
medido por el propio sistema en `GET /api/v1/metrics`.

---

## 1. Tarifas vigentes

`gemini-3.5-flash`, julio de 2026:

| Concepto | Tarifa (USD por millón de tokens) | Por cada 1000 tokens |
|---|---|---|
| Entrada (texto e imagen) | 1,50 | 0,0015 |
| Salida | 9,00 | 0,0090 |
| **Razonamiento** | **9,00 (se factura como salida)** | **0,0090** |
| Entrada cacheada | 0,15 | 0,00015 |

**La salida cuesta seis veces más que la entrada.** Y los tokens de
razonamiento —los que el modelo consume "pensando" antes de responder— se
facturan a tarifa de salida. Esto es lo que domina la factura y lo que motivó
corregir el modelo de costos del sistema (ver §5).

## 1.1 Sobre el uso de GPU

El sistema **no consume GPU propia, y es una consecuencia directa de su
arquitectura**, no una omisión de la medición.

| Etapa | Dónde se ejecuta | Recurso |
|---|---|---|
| Preprocesamiento y ROI (OpenCV) | Nuestro servidor | CPU |
| Reconocimiento y explicación (Gemini) | Infraestructura de Google | GPU/TPU **de Google**, facturada por tokens |
| Resolución simbólica (SymPy) | Nuestro servidor | CPU |

La única etapa que requiere aceleración por hardware está delegada en el
proveedor del modelo, que no expone métricas de GPU sino consumo de tokens. Por
eso el análisis de desempeño mide CPU y memoria del proceso, y el costo del
cómputo acelerado aparece como gasto de API en lugar de como utilización de
hardware.

Es también la razón de que la operación sea barata: **el proyecto no sostiene
ninguna GPU**. Un modelo de visión autoalojado eliminaría el costo por llamada,
pero exigiría una instancia con GPU —del orden de 300 USD al mes— que sólo
compensaría a un volumen muy superior al previsto (ver §6).

## 2. Consumo por operación

Medido en pruebas contra el modelo real, con imágenes ya recortadas por OpenCV:

| Operación | Entrada | Salida | Razonamiento | Costo |
|---|---|---|---|---|
| Reconocimiento (imagen → LaTeX) | 280 | 25 | 180 | **0,002265 USD** |
| Explicación (3 pasos) | 210 | 140 | 420 | **0,005355 USD** |
| **Conversión completa** | 490 | 165 | 600 | **0,007620 USD** |

Una conversión completa cuesta unos **0,0076 USD**, alrededor de **30 pesos
colombianos**. La resolución con SymPy no aparece porque **no cuesta nada**: se
ejecuta en nuestro propio servidor. Es un efecto económico directo de la
decisión arquitectónica de no delegar el cálculo en el modelo.

> Estas cifras son la referencia de partida. Las de la demostración se leen en
> vivo desde el panel de métricas, que reporta el consumo acumulado real.

## 3. Proyección mensual

Suponiendo 4 conversiones por usuario al mes (un estudiante consultando
ejercicios puntuales):

| Usuarios | Conversiones/mes | Costo mensual |
|---|---|---|
| 100 | 400 | **3,05 USD** |
| 1 000 | 4 000 | **30,48 USD** |
| 10 000 | 40 000 | **304,80 USD** |

A esto habría que sumar la infraestructura: en Render, el plan gratuito basta
para el proyecto, pero un uso real exigiría plan de pago (unos 7 USD/mes por el
servicio web y 7 USD/mes por PostgreSQL) para evitar la suspensión por
inactividad y la caducidad de la base de datos a los 30 días.

## 4. El costo del razonamiento

Es el hallazgo más relevante del análisis. De los 765 tokens facturados a tarifa
de salida en una conversión completa, **600 son de razonamiento**: el modelo
gasta más "pensando" que respondiendo.

| Escenario | Costo por conversión | Diferencia |
|---|---|---|
| Actual (razonamiento por defecto) | 0,007620 USD | — |
| Sin razonamiento | 0,002220 USD | **−71 %** |

Desactivarlo reduciría la factura a menos de un tercio. La variable
`GEMINI_THINKING_BUDGET` permite hacerlo, y la decisión razonable es
diferenciada:

- **Reconocimiento:** transcribir una expresión es una tarea mecánica de
  percepción. El razonamiento aporta poco y encarece. Candidato claro a
  reducirlo o desactivarlo.
- **Explicación:** redactar una explicación didáctica sí se beneficia de que el
  modelo elabore. Aquí el gasto se justifica.

Se deja documentado como palanca de optimización y no como cambio ya aplicado,
porque exige medir la pérdida de precisión en el reconocimiento antes de fijarlo.

## 5. Corrección del modelo de costos

La primera implementación aplicaba **una tarifa única** al total de tokens. Al
contrastarla con las tarifas reales se detectó que subestimaba el gasto de forma
sistemática, porque trataba los tokens de razonamiento —los más numerosos— como
si costaran lo mismo que la entrada, siendo seis veces más caros.

El cálculo ahora separa ambas tarifas (`gemini_input_cost_per_1k` y
`gemini_output_cost_per_1k`) y suma el razonamiento al lado de la salida. Hay
pruebas automatizadas que fijan ese comportamiento, precisamente para que la
distinción no se pierda en un cambio futuro.

## 6. Comparación con alternativas

| Opción | Costo aproximado por conversión | Valoración |
|---|---|---|
| **Gemini 3.5 Flash** (elegida) | 0,0076 USD | Multimodal, buena precisión en notación, SDK oficial en Python |
| Gemini 3.5 Flash con razonamiento reducido | 0,0022 USD | La misma opción optimizada; pendiente de medir precisión |
| GPT-4o | ≈ 0,010–0,015 USD | Precisión comparable, costo mayor |
| Mathpix (OCR especializado) | ≈ 0,004 USD por imagen | Mejor OCR matemático, pero **no explica**: exigiría un segundo modelo para la explicación, y el total superaría al actual |
| Modelo open source autoalojado | 0 USD por llamada | Sin costo por uso, pero requiere GPU (≈ 300 USD/mes) y sólo compensa a gran volumen |

La elección de Gemini se sostiene por cubrir **las dos** necesidades —visión y
redacción— con un único proveedor y un nivel gratuito suficiente para el
proyecto. La interfaz `RecognitionProvider` mantiene abierta la puerta a
cambiar: si Mathpix resultara netamente mejor en reconocimiento, podría usarse
para transcribir y Gemini sólo para explicar, sin reescribir la aplicación.

## 7. Conclusiones

1. El costo por conversión es **bajo en términos absolutos** (0,0076 USD) y la
   operación resulta viable incluso a escala de diez mil usuarios.
2. **El razonamiento domina la factura**: es el 71 % del costo y la primera
   palanca a ajustar si hiciera falta optimizar.
3. **SymPy no cuesta nada.** Delegar el cálculo en el modelo habría añadido
   tokens de salida —los caros— además de comprometer la corrección. La decisión
   arquitectónica resulta ser simultáneamente la más barata y la más fiable.
4. El sistema **mide su propio consumo**, de modo que estas cifras pueden
   verificarse en cualquier momento en lugar de quedarse en una estimación.

---

## Referencias

- `app/core/metrics.py` y `services/llm/gemini_client.py` — medición del consumo.
- [`../design/prompting-strategy.md`](../design/prompting-strategy.md) — diseño de los prompts.
- [Gemini API — precios](https://ai.google.dev/pricing)
