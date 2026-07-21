# IA Responsable — MathScribe

**Responsable:** Michael Ramírez (Product Owner)
**Versión:** 1.0 — 21 de julio de 2026

Análisis de los riesgos éticos y de privacidad del sistema, con las mitigaciones
que efectivamente están implementadas en el código y las que quedan declaradas
como pendientes. Se distingue explícitamente entre ambas: presentar como
resuelto lo que no lo está sería, en sí mismo, una mala práctica.

---

## 1. Privacidad de imágenes y video

### El riesgo

MathScribe pide acceso a la cámara. Aunque el propósito sea fotografiar una
expresión matemática, lo que entra en el encuadre casi nunca es sólo eso: el
cuaderno completo puede tener el nombre del estudiante, el de la institución,
anotaciones personales; el fondo puede incluir a terceros que no consintieron
nada. Un examen fotografiado es, además, información sobre el desempeño
académico de una persona identificable.

A esto se suma que la imagen **sale del dispositivo**: viaja a nuestro servidor
y de ahí a un tercero (Google) para el reconocimiento. El usuario no
necesariamente lo intuye.

### Mitigaciones implementadas

| Mitigación | Dónde |
|---|---|
| **El video nunca se transmite.** El stream de la cámara vive sólo en el navegador; sólo viaja el fotograma que la persona decide capturar | `CameraCapture.tsx` |
| **La imagen no se persiste.** Se procesa en memoria y se descarta al terminar la petición; no se escribe en disco ni en la base de datos | `recognition.py`, `service.py` |
| **Se recorta antes de enviar.** OpenCV detecta la región de la expresión y descarta el resto de la hoja, de modo que buena parte del contexto potencialmente identificable no llega al tercero | `preprocessing.py` |
| **Sólo se guarda el LaTeX**, no la imagen, cuando hay historial de usuario | modelo `Conversion` |

Que el recorte por ROI reduzca la exposición de datos es un efecto secundario
del diseño técnico, pero es real y conviene señalarlo: menos píxeles enviados es
menos información entregada a un tercero.

### Pendientes declarados

- Aviso explícito en la interfaz de que la imagen se envía a un servicio externo
  de Google, mostrado **antes** de la primera captura.
- Política de privacidad enlazada desde la aplicación.
- Confirmar y documentar la política de retención de Google para los datos
  enviados a la API de Gemini.

## 2. Consentimiento

### El riesgo

El permiso del navegador es un consentimiento pobre: la persona acepta "usar la
cámara", no "enviar una foto de mi cuaderno a un servidor de un tercero para que
un modelo la procese". Hay una brecha entre lo que se autoriza y lo que ocurre.
En menores de edad —parte importante de nuestro público objetivo— la brecha es
mayor, porque ni siquiera son quienes pueden otorgar consentimiento válido.

### Mitigaciones implementadas

- **El permiso se pide sólo al pulsar "Usar la cámara"**, no al cargar la
  página: es una acción deliberada, no un diálogo que se acepta por inercia.
- **La cámara se apaga sola** tras la captura y al desmontar el componente
  (`getTracks().forEach(stop)`): no queda encendida en segundo plano.
- **Existe una vía alternativa** —subir una imagen— que nunca activa la cámara.
  Denegar el permiso no inutiliza la aplicación.

### Pendientes declarados

- Texto de consentimiento informado antes de la primera captura, explicando
  destino y tratamiento de la imagen.
- Consideración específica para menores de edad (aviso a acudientes).

## 3. Riesgos de vigilancia automatizada

Es el riesgo **menos severo** en este sistema, y conviene decirlo con franqueza
en lugar de inflarlo: MathScribe no identifica personas, no detecta rostros, no
rastrea ubicación, no opera de forma continua ni desatendida. Cada activación
requiere una acción explícita del usuario sobre su propio material.

El riesgo real, aunque acotado, es de **desvío de uso**: nada impide
técnicamente apuntar la cámara a algo que no sea una expresión matemática. Las
mitigaciones son que no se almacena la imagen y que el prompt instruye al modelo
a devolver una cadena vacía si no encuentra una expresión matemática, de modo
que el sistema no produce descripciones de contenido arbitrario.

## 4. Falsos positivos y falsos negativos

Esta es, junto con los sesgos, la categoría de riesgo **más relevante** para
MathScribe, porque afecta directamente al propósito educativo.

| Tipo | Qué ocurre | Consecuencia |
|---|---|---|
| **Falso positivo de reconocimiento** | El modelo transcribe una expresión distinta de la escrita (confunde 5 con S, x con ×, un exponente con un subíndice) | El sistema resuelve **correctamente el problema equivocado**. Es el fallo más peligroso porque el resultado se ve perfectamente válido |
| **Falso negativo de reconocimiento** | No detecta la expresión y devuelve vacío | Frustración, pero sin daño: el usuario reintenta |
| **Falso positivo de resolución** | SymPy interpreta el LaTeX de forma distinta a la intención | Resultado correcto para otra expresión |
| **Falso negativo de resolución** | El LaTeX no es parseable y no se resuelve | Frustración, sin daño |

### Mitigaciones implementadas

La arquitectura ataca directamente el caso peligroso:

1. **El LaTeX reconocido se muestra al usuario antes de resolver**, y resolver
   requiere pulsar un botón. Es un punto de verificación humana deliberado: la
   persona ve qué entendió el sistema antes de confiar en la respuesta.
2. **SymPy calcula, el modelo sólo redacta.** El resultado no es una predicción
   de un modelo de lenguaje sino el cómputo de un motor simbólico determinista.
3. **La explicación se valida contra los pasos.** Si el modelo devuelve un
   número de explicaciones distinto al de pasos calculados, se descarta por
   completo y se conservan las descripciones originales (`explainer.py`): se
   prefiere una explicación seca y correcta a una elocuente y desalineada.
4. **Se expone `confidence`** en la respuesta del reconocimiento.
5. **Aviso permanente** junto al resultado: *"Verifica siempre el resultado: el
   reconocimiento de la imagen puede equivocarse."*

### Pendientes declarados

- Permitir **editar manualmente el LaTeX** reconocido antes de resolver. Es la
  mitigación más valiosa que falta: hoy el usuario puede detectar el error pero
  no corregirlo sin volver a capturar.
- Destacar visualmente el resultado cuando `confidence` sea baja.

## 5. Sesgos

### Sesgos identificados

| Sesgo | Origen | A quién perjudica |
|---|---|---|
| **De caligrafía** | Los modelos se entrenan predominantemente con notación impresa o manuscrita "estándar" | Personas con letra irregular, temblor, dislexia disgráfica, o quienes escriben con la mano no dominante |
| **De notación regional** | La notación matemática **no es universal**: el separador decimal (coma en Colombia, punto en EE.UU.), los símbolos de intervalo abierto (`(a,b)` vs `]a,b[`), `tg` frente a `tan` | Estudiantes formados en convenciones latinoamericanas y europeas, incluido nuestro propio público objetivo |
| **De idioma** | El sistema y los prompts operan en español, pero el modelo tiende a responder en inglés o a interpretar texto ambiguo con sesgo anglófono | Usuarios hispanohablantes, que son el público objetivo |
| **De calidad del dispositivo** | Una cámara de gama baja produce imágenes ruidosas | Usuarios con menos recursos económicos — un sesgo socioeconómico que amplifica desigualdades educativas existentes |
| **De condiciones materiales** | Papel amarillento, iluminación deficiente, lápiz tenue | Igual que el anterior |

El sesgo de notación regional merece énfasis: es fácil de pasar por alto porque
no se manifiesta como un error evidente, sino como una interpretación
sistemáticamente distinta de lo que el estudiante escribió.

### Mitigaciones implementadas

- **Preprocesamiento con OpenCV** (binarización adaptativa, reducción de ruido):
  compensa parcialmente el sesgo de dispositivo y de condiciones materiales,
  igualando la calidad de entrada al modelo.
- **Prompt en español** con instrucciones explícitas de formato.
- **Verificación humana previa** a la resolución: permite al usuario detectar una
  interpretación regionalmente equivocada.
- **Interfaz en español**, sin dar por supuesto el inglés.

### Pendientes declarados

- Probar con muestras de caligrafía diversa y documentar la tasa de acierto por
  tipo de escritura, en lugar de asumir un desempeño uniforme.
- Configuración explícita de convenciones regionales (separador decimal).
- Evaluación con imágenes tomadas por dispositivos de gama baja.

## 6. Impacto potencial sobre los usuarios

### Riesgos

**Dependencia y atrofia del aprendizaje.** Es el riesgo de fondo de toda
herramienta que resuelve ejercicios: el estudiante puede usarla para *evitar*
pensar en lugar de para *verificar* su pensamiento. Ninguna medida técnica lo
elimina por completo.

**Propagación de errores en contexto educativo.** Un resultado equivocado
aceptado como correcto no sólo falla en un ejercicio: puede fijar una
comprensión errónea que persiste.

**Falsa autoridad.** Una respuesta bien formateada, con pasos numerados y
notación elegante, proyecta más certeza de la que merece.

**Inequidad de acceso.** Requiere teléfono con cámara y conexión estable. En el
plan gratuito, además, el servicio tarda en despertar tras inactividad.

### Mitigaciones implementadas

- **Se muestran los pasos, no sólo la respuesta.** El diseño del producto
  favorece el uso pedagógico: quien quiera sólo el número igual lo obtiene, pero
  el procedimiento está delante.
- **Explicaciones del *porqué*,** no sólo del *qué*: el prompt pide explicar la
  razón de cada paso.
- **Aviso explícito de verificación** junto a cada resultado.
- **SymPy como fuente de verdad**, que acota drásticamente la propagación de
  errores de cálculo.

### Pendientes declarados

- Mensaje orientado al uso responsable en el primer acceso ("úsalo para
  verificar tu procedimiento, no para reemplazarlo").
- Modo "sólo pistas" que insinúe el siguiente paso sin dar el resultado.

---

## 7. Resumen de mitigaciones

| # | Riesgo | Mitigación | Estado |
|---|---|---|---|
| 1 | Exposición de la imagen | No se persiste; sólo se envía la ROI recortada | ✅ Implementado |
| 2 | Transmisión de video | Sólo viaja el fotograma capturado | ✅ Implementado |
| 3 | Consentimiento por inercia | Permiso pedido ante acción explícita; vía alternativa siempre disponible | ✅ Implementado |
| 4 | Cámara activa en segundo plano | Se apaga tras capturar y al desmontar | ✅ Implementado |
| 5 | Resolver el problema equivocado | LaTeX visible y confirmación humana antes de resolver | ✅ Implementado |
| 6 | Alucinación matemática | SymPy calcula; el modelo sólo redacta | ✅ Implementado |
| 7 | Explicación desalineada | Validación estricta; se descarta si no encaja | ✅ Implementado |
| 8 | Exceso de confianza del usuario | Aviso de verificación junto al resultado | ✅ Implementado |
| 9 | Sesgo de dispositivo y condiciones | Preprocesamiento con OpenCV | ✅ Implementado |
| 10 | Desconocimiento del envío a terceros | Aviso previo a la primera captura | ⏳ Pendiente |
| 11 | Error detectado pero no corregible | Edición manual del LaTeX | ⏳ Pendiente |
| 12 | Sesgo de caligrafía y notación regional | Evaluación documentada y configuración regional | ⏳ Pendiente |
| 13 | Dependencia del estudiante | Mensaje de uso responsable y modo "sólo pistas" | ⏳ Pendiente |
| 14 | Telemetría accesible sin autenticación | Restringir `/metrics` a personal autorizado | ⏳ Pendiente (decisión consciente, ver §7.1) |

Nueve mitigaciones operativas y cinco pendientes explícitas. Las pendientes no
son omisiones descubiertas al escribir el documento: son decisiones de alcance
tomadas con el calendario del proyecto a la vista, y quedan registradas para que
cualquiera que retome el sistema sepa qué falta y por qué.

### 7.1 Sobre la exposición pública de las métricas

El endpoint `GET /api/v1/metrics` y el panel que lo consume son accesibles sin
autenticación en el despliegue público. **Es una decisión deliberada, no un
descuido**, y conviene dejarla razonada.

Lo que se expone es telemetría operativa agregada: número de peticiones,
latencia, uso de CPU y memoria del proceso, y tokens y costo acumulados. **No se
expone ningún dato personal**: ni imágenes, ni expresiones reconocidas, ni
identificadores de usuario. Tampoco credenciales ni rutas internas no
documentadas —la propia API es pública y está descrita en `/docs`.

La razón de mantenerlo abierto es de transparencia y verificabilidad: cualquiera
puede comprobar el desempeño y el costo real del sistema en lugar de confiar en
las cifras que reporta este documento. En un proyecto académico cuyo objetivo es
justamente evidenciar la medición, ocultarla sería contraproducente.

El riesgo residual es de **divulgación de información operativa**: un tercero
podría inferir el volumen de uso o el gasto en la API, y consultar el endpoint
de forma repetida para inflar el tráfico. Ninguno de los dos compromete a los
usuarios ni sus datos.

En un despliegue de producción real la recomendación es la contraria: restringir
el endpoint a personal autorizado, mediante autenticación o exponiéndolo sólo en
una red interna, y conservar la telemetría en un sistema de observabilidad en
lugar de en memoria del proceso.

---

## 8. Composición del equipo y participación

El taller propone equipos de tres integrantes con seis roles sugeridos. Este
equipo es de cinco personas, con los roles repartidos así:

| Persona | Rol |
|---|---|
| José Adrián Marín | Backend, visión computacional e integración multimodal |
| María Alejandra Moya | Frontend |
| Michael Ramírez | Product Owner, IA responsable y documentación |
| Juan Fernando Calle | Calidad y pruebas automatizadas |
| Daniel Rojas Barreneche | Scrum Master, DevOps/cloud y arquitectura |

La participación de cada integrante es verificable en el historial de commits:
cada tarea se desarrolló en su propia rama, con autoría individual, y se integró
mediante pull request revisado.

---

## Referencias

- [`../product/problem-definition.md`](../product/problem-definition.md) — alcance y público objetivo.
- [`../design/bpmn.md`](../design/bpmn.md) — puntos de control del proceso.
- `docs/product/riesgos.md` (repositorio de frontend) — registro de riesgos R-01 a R-10.
