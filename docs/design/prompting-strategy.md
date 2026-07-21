# Estrategia de prompting multimodal

**Responsable:** Michael Ramírez (Product Owner)
**Versión:** 1.0 — 21 de julio de 2026

Documenta cómo se diseñaron los dos prompts del sistema, qué restricciones del
modelo obligaron a cada decisión y cómo se validan las respuestas. Los prompts
transcritos son los que están efectivamente en el código.

---

## 1. Principio de diseño

El sistema hace **dos** llamadas al modelo, y ninguna de las dos le pide
resolver matemática. Esa es la decisión de la que se deriva todo lo demás:

| Llamada | Qué se le pide | Qué NO se le permite |
|---|---|---|
| Reconocimiento | Transcribir a LaTeX lo que ve en la imagen | Resolver, simplificar, interpretar |
| Explicación | Redactar en lenguaje natural pasos ya calculados | Recalcular, añadir o quitar pasos |

El modelo se usa para lo que hace bien —leer imágenes y redactar— y se le retira
la tarea en la que puede fallar sin que se note: calcular. SymPy se encarga de
eso, y su resultado es verificable.

## 2. Prompt de reconocimiento (imagen → LaTeX)

Definido en `services/recognition/providers/gemini.py`:

```
Eres un OCR matemático. Transcribe la expresión matemática de la imagen a LaTeX válido.
Reglas estrictas:
1. Devuelve ÚNICAMENTE la expresión en LaTeX, sin explicaciones ni comentarios.
2. No uses delimitadores: nada de ```latex, ```, $, $$ ni \[ \].
3. No resuelvas ni simplifiques la expresión: transcríbela tal como aparece.
4. Si la imagen no contiene ninguna expresión matemática legible, devuelve una cadena vacía.
```

### Justificación de cada regla

**Asignación de rol ("Eres un OCR matemático").** No es adorno. Durante las
pruebas iniciales comprobamos que, sin un rol explícito, el modelo improvisa:
ante una entrada ambigua puede saludar, interpretar la intención del usuario o
responder en otro idioma. Anclar el rol acota drásticamente el espacio de
respuestas posibles.

**Regla 1 — sólo la expresión.** Cualquier texto adicional ("Aquí tienes la
expresión:") rompe `sympy.parsing.latex.parse_latex` aguas abajo, que espera
exclusivamente notación.

**Regla 2 — sin delimitadores.** Es la instrucción que el modelo desobedece con
más frecuencia: aunque se le prohíba, envuelve la respuesta en ```` ```latex ````
o `$$` de forma intermitente. Por eso existe la limpieza descrita en §4: **el
prompt reduce la frecuencia del problema, no lo elimina**, y el código no confía
en que se cumpla.

**Regla 3 — no resolver.** Sin ella, ante `\int_0^1 x^2 dx` el modelo tiende a
devolver `1/3`. Eso destruiría el propósito del sistema: perderíamos la
expresión original y el resultado dejaría de ser verificable.

**Regla 4 — vacío ante ausencia.** Da una salida explícita para las fotos
borrosas, mal encuadradas o sin contenido matemático. Sin ella, el modelo
alucina una expresión plausible antes que admitir que no ve ninguna.

### Estructuración del contexto

La imagen que recibe el modelo **no es la foto original**: OpenCV la convierte a
escala de grises, reduce el ruido, aplica umbral adaptativo y recorta la región
de interés detectada por análisis de contornos. Se envía sólo esa región, con la
instrucción, en un único turno sin historial.

Esto tiene tres efectos: mejora la precisión (menos ruido que interpretar),
reduce el costo (menos píxeles son menos tokens de imagen) y limita la
exposición de datos personales que pudiera haber en el resto de la hoja.

## 3. Prompt de explicación (pasos → lenguaje natural)

Definido en `services/solver/explainer.py`:

```
Eres un profesor de matemáticas que explica a un estudiante de secundaria.
Te doy la expresión original y los pasos ya resueltos por un motor de álgebra simbólica.

Reglas estrictas:
1. NO recalcules nada. Los valores de los pasos son correctos y definitivos.
2. Reescribe únicamente la descripción de cada paso, en español, con una o dos
   frases claras que expliquen QUÉ se hace y POR QUÉ.
3. Mantén el mismo número de pasos y el mismo orden.
4. No menciones el motor simbólico ni el proceso interno.
5. Responde SÓLO con un arreglo JSON de cadenas, una por paso, sin ningún otro
   texto ni delimitadores de código.

Ejemplo de respuesta para dos pasos:
["Primera explicación.", "Segunda explicación."]
```

El contexto que acompaña al prompt se construye en `construir_entrada()`: la
expresión original y la lista numerada de pasos con su LaTeX.

### Justificación

**Rol pedagógico con nivel explícito.** "Estudiante de secundaria" calibra el
vocabulario. Sin nivel declarado, el modelo oscila entre lo trivial y lo
universitario.

**Regla 1 — no recalcular.** Es la instrucción central del sistema. El modelo
recibe resultados correctos y su única tarea es narrarlos.

**Regla 3 — mismo número de pasos.** Habilita la validación automática: si
devuelve una cantidad distinta, sabemos que se desvió y descartamos la
respuesta completa.

**Regla 5 — JSON.** Una salida estructurada es verificable por programa; una
prosa libre habría que interpretarla heurísticamente. El ejemplo incluido
("one-shot") reduce mucho la tasa de formatos inesperados.

## 4. Control y validación de las respuestas

Ninguna respuesta del modelo se usa tal cual. Las dos pasan por validación:

### Reconocimiento

```python
def limpiar_latex(texto: str) -> str:
    # elimina ```latex / ``` y delimitadores $, $$, \[ \], \( \)
```

Se aplica de forma repetida hasta que la cadena deja de cambiar, porque el
modelo llega a anidar envoltorios (```` ```latex $$...$$ ``` ````). Si tras
limpiar queda vacío, se devuelve una respuesta degradada explícita en lugar de
propagar basura al solucionador.

### Explicación

`extraer_descripciones()` exige que la respuesta sea un arreglo JSON de cadenas
no vacías **con exactamente la longitud esperada**. Ante el mínimo desajuste
devuelve `None` y se conservan las descripciones originales de SymPy.

El criterio es deliberado: emparejar explicaciones con pasos equivocados sería
peor que no explicar, porque produciría un texto convincente y erróneo. Se
prefiere una explicación seca y correcta a una elocuente y desalineada.

### Validación final

SymPy es la última verificación: el LaTeX reconocido tiene que ser parseable
para poder resolverse. Un LaTeX inválido no produce un resultado inventado, sino
un resultado vacío con aviso al usuario. Y en el frontend, KaTeX renderiza con
`throwOnError: false`, de modo que una notación imperfecta se muestra degradada
en vez de romper la interfaz.

## 5. Restricciones del modelo que condicionaron el diseño

| Restricción | Efecto | Cómo se aborda |
|---|---|---|
| **No obedece siempre el formato** | Añade delimitadores pese a prohibirlos | Limpieza programática; el prompt reduce la frecuencia, el código garantiza el resultado |
| **Deriva de idioma** | Puede responder en otro idioma ante entradas ambiguas | Prompt en español con rol explícito; en la explicación se exige "en español" |
| **Alucinación ante ausencia** | Inventa antes que admitir que no ve nada | Regla explícita de devolver vacío |
| **Tokens de razonamiento** | Los modelos 3.x razonan antes de responder, y eso se factura | `GEMINI_THINKING_BUDGET` configurable; ver el análisis de costos |
| **No determinista** | La misma imagen puede dar transcripciones distintas | Se muestra el LaTeX al usuario para que lo verifique antes de resolver |
| **Latencia variable** | Depende de carga y del razonamiento | Medida por ruta en el endpoint de métricas |

## 6. Cómo se probaron los prompts

Los prompts están cubiertos por pruebas automatizadas que fijan sus invariantes
(`tests/test_gemini_provider.py`, `tests/test_explainer.py`):

- Que el prompt de reconocimiento siga prohibiendo resolver y delimitar.
- Que el de explicación siga prohibiendo recalcular y alterar el número de pasos.

Son pruebas sobre el texto del prompt, no sobre el modelo. Su propósito es que
nadie relaje esas instrucciones sin darse cuenta de que son parte del contrato
con SymPy, no redacción decorativa.

---

## Referencias

- `services/recognition/providers/gemini.py` — prompt de reconocimiento y limpieza.
- `services/solver/explainer.py` — prompt de explicación y validación.
- [`../product/cost-analysis.md`](../product/cost-analysis.md) — impacto económico del razonamiento.
- [`../responsible-ai/responsible-ai.md`](../responsible-ai/responsible-ai.md) — mitigación de falsos positivos.
