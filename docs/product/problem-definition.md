# Definición del problema — MathScribe

**Responsable:** Michael Ramírez (Product Owner)
**Versión:** 1.0 — 20 de julio de 2026
**Estado:** aprobado por el equipo

Este documento corresponde al entregable *Elección y Aprobación del Problema* del
Taller 3 y fija el alcance sobre el que se construyó el sistema.

---

## 1. Planteamiento del problema

La matemática se sigue produciendo a mano. Un estudiante que resuelve un ejercicio
en su cuaderno, un docente que plantea un problema en el tablero y un investigador
que bosqueja una derivación en una servilleta escriben todos en notación
manuscrita. Sin embargo, **el ecosistema digital que podría ayudarles —
calculadoras simbólicas, editores LaTeX, buscadores— sólo entiende texto
estructurado**.

Ese salto entre el papel y la herramienta digital hoy se cruza a mano: transcribir
`∫₀¹ x² dx` a `\int_0^1 x^2\,dx` exige conocer LaTeX, es lento y es propenso a
errores. La consecuencia es que quien más necesita ayuda —el estudiante que no
entiende el ejercicio— es también quien menos capacidad tiene de pedirla, porque
para consultarla primero tendría que saber escribirla.

Existen soluciones parciales, pero ninguna cierra el ciclo:

- Las **calculadoras simbólicas** (WolframAlpha, Symbolab) resuelven, pero exigen
  que el usuario teclee la expresión.
- Los **OCR matemáticos** (Mathpix) transcriben, pero no resuelven ni explican.
- Los **asistentes conversacionales** generales aceptan una foto y responden, pero
  su respuesta es texto generado probabilísticamente: **pueden equivocarse en la
  aritmética y presentarlo con la misma seguridad que un resultado correcto**.

El problema que MathScribe aborda es, entonces, doble: **eliminar la fricción de
transcripción y, a la vez, garantizar que el resultado entregado sea verificable**,
no una alucinación plausible.

## 2. Justificación

Tres razones sostienen la elección:

**Valor pedagógico real.** En un contexto educativo, un resultado sin procedimiento
no enseña. MathScribe no devuelve sólo la respuesta: devuelve los pasos intermedios
y una explicación en lenguaje natural de cada uno. La herramienta acompaña el
aprendizaje en vez de sustituirlo.

**Corrección verificable, no probabilística.** Es la decisión de diseño que
distingue al proyecto. El modelo multimodal se usa **únicamente** para dos cosas en
las que es bueno: leer la imagen y redactar en lenguaje natural. **La matemática la
hace SymPy**, un motor de álgebra simbólica determinista. Si SymPy dice que la
integral vale 1/3, vale 1/3, y el LLM no puede contradecirlo porque su tarea es
narrar los pasos que SymPy ya calculó. Esto convierte una debilidad conocida de los
LLM en un riesgo controlado por arquitectura.

**Pertinencia técnica con el taller.** El dominio exige genuinamente las cuatro
capas que el taller pide integrar: captura en tiempo real (cámara), visión
computacional open source (OpenCV para aislar la expresión del resto de la hoja),
modelo multimodal (Gemini para imagen → LaTeX) y razonamiento simbólico posterior.
Ninguna capa está puesta por cumplir un requisito.

## 3. Público objetivo

| Segmento | Necesidad | Uso previsto |
|---|---|---|
| **Primario — Estudiantes de secundaria y universidad** (cálculo, álgebra, física) | Verificar si su procedimiento es correcto y entender dónde se equivocaron | Fotografía del ejercicio del cuaderno; consulta el resultado y los pasos |
| **Secundario — Docentes** | Digitalizar ejercicios manuscritos para material de clase | Captura de un ejercicio del tablero y obtiene el LaTeX listo para pegar |
| **Terciario — Personas con dificultades motrices o visuales** | Reducir la barrera de teclear notación matemática compleja | Captura por cámara en lugar de escritura manual de LaTeX |

El segmento primario define las decisiones de producto: interfaz en español,
explicaciones didácticas y advertencia explícita de verificar los resultados.

## 4. Alcance

### Incluido en el MVP

- Captura desde cámara en vivo (`getUserMedia`) y carga de archivo como alternativa.
- Preprocesamiento con OpenCV: escala de grises, reducción de ruido, binarización
  adaptativa y **detección de la región de interés (ROI)** por análisis de contornos.
- Reconocimiento imagen → LaTeX con Gemini (`gemini-3.5-flash`).
- Resolución simbólica con SymPy: ecuaciones, derivadas, integrales y simplificación.
- Explicación paso a paso en lenguaje natural, restringida a los pasos de SymPy.
- Renderizado de la notación con KaTeX.
- Autenticación e historial de conversiones por usuario.
- Métricas técnicas: latencia, CPU, memoria, tokens y costo estimado.
- Despliegue público con contenerización y CI/CD.

### Fuera del alcance (declarado explícitamente)

- Reconocimiento de **varias expresiones simultáneas** en una misma imagen: el MVP
  procesa la expresión dominante detectada por el ROI.
- Diagramas, gráficas, geometría y matrices manuscritas.
- Resolución de problemas planteados en **texto narrativo** ("un tren sale de...").
- Aplicación móvil nativa; el acceso es vía navegador (que sí funciona en móvil).
- Corrección o calificación del procedimiento escrito por el estudiante: el sistema
  resuelve la expresión, no evalúa el desarrollo del usuario.
- Uso sin conexión: el reconocimiento depende de una API externa.

## 5. Riesgos

El registro completo, con probabilidad, impacto y mitigación, está en
[`riesgos.md`](https://github.com/AirWa1l/MathScribe---Frontend/blob/main/docs/product/riesgos.md)
del repositorio de frontend (R-01 a R-10). Los tres
riesgos que más condicionaron el diseño:

| Riesgo | Por qué es crítico | Mitigación adoptada |
|---|---|---|
| **Error de reconocimiento en letra manuscrita** (R-01) | Un LaTeX mal leído produce una respuesta correcta a la pregunta equivocada | Preprocesamiento OpenCV + ROI; se muestra el LaTeX reconocido **antes** de resolver, para que el usuario lo valide |
| **Dependencia de una API externa de pago** (R-02) | Corte de servicio o de cuota deja el sistema inutilizable | Interfaz `RecognitionProvider` desacoplada: cambiar de proveedor no toca la API ni el frontend. Degradación controlada si falta la clave |
| **Alucinación matemática del LLM** (R-09) | Un error presentado con seguridad en contexto educativo enseña algo falso | SymPy como única fuente de verdad; el LLM narra, no calcula |

## 6. Flujo esperado

```
Cámara en vivo (navegador)
  → captura de frame PNG
  → POST /api/v1/recognition
      → OpenCV: preprocesamiento + detección de ROI
      → Gemini Vision: imagen → LaTeX
  → el usuario verifica el LaTeX reconocido
  → POST /api/v1/solve
      → SymPy: resuelve y produce los pasos verificables
      → Gemini (texto): redacta la explicación de cada paso
  → LaTeX + resultado + pasos, renderizados con KaTeX
```

El detalle por actividad, con carriles y puntos de decisión, está modelado en
[`../design/bpmn.md`](../design/bpmn.md).

## 7. Justificación tecnológica

| Decisión | Alternativas evaluadas | Por qué esta |
|---|---|---|
| **OpenCV** (visión open source) | YOLO, MediaPipe, Detectron2 | El problema no es *detección de objetos* sino *limpieza y recorte de la región con la expresión*. OpenCV resuelve exactamente eso con operaciones clásicas (binarización adaptativa, contornos), sin coste de inferencia ni necesidad de entrenar. Usar YOLO habría exigido un dataset etiquetado que no aporta valor aquí |
| **Gemini** (multimodal) | GPT‑4V, Claude Vision, Qwen‑VL | Nivel gratuito suficiente para el proyecto, buena precisión en notación matemática y SDK oficial en Python. La interfaz `RecognitionProvider` permite sustituirlo sin reescribir la aplicación |
| **SymPy** (motor simbólico) | Delegar la resolución al propio LLM | Es la decisión central: convierte el resultado en **determinista y verificable**. Además `parse_latex` acepta directamente la salida del reconocimiento |
| **FastAPI** | Django, Flask | Asíncrono (importante con dos llamadas externas por petición), validación con Pydantic y documentación OpenAPI automática, útil para el contrato con el frontend |
| **React + Vite + TypeScript** | Next.js, Vue | No se requiere renderizado en servidor; el tipado ayuda a mantener el contrato de la API alineado entre capas |
| **KaTeX** | MathJax | Renderizado notablemente más rápido y suficiente para la notación del alcance |
| **PostgreSQL** | MongoDB, SQLite | Los datos son relacionales (usuario → conversiones) y Render lo ofrece administrado |
| **Docker + Render + GitHub Actions** | AWS, Azure, GCP | Cubre contenerización, CI/CD y despliegue público con nivel gratuito, sin la complejidad de configuración de las nubes mayores para un proyecto de este tamaño |

---

## Referencias

- Requisitos del taller: *Taller #3 — Desarrollo de Agentes Visuales Multimodales
  en Tiempo Real*, Universidad del Valle, junio de 2026.
- Arquitectura C4 y diseño cloud-native: [`../design/c4-architecture.md`](../design/c4-architecture.md).
- Análisis de IA responsable: [`../responsible-ai/responsible-ai.md`](../responsible-ai/responsible-ai.md).
