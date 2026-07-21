# Arquitectura C4 — MathScribe

**Responsable:** Daniel Rojas Barreneche (Arquitectura / DevOps)
**Versión:** 1.0 — 21 de julio de 2026

Descripción de la arquitectura en los tres primeros niveles del modelo C4:
contexto, contenedores y componentes. Los diagramas reflejan el sistema tal
como está construido y desplegado, no un diseño previo.

---

## Nivel 1 — Contexto

Qué es MathScribe y con quién habla.

```mermaid
flowchart TB
    subgraph externo[" "]
        direction TB
        estudiante["👤 Estudiante<br/><i>Usuario principal</i><br/>Fotografía un ejercicio<br/>manuscrito y obtiene la<br/>solución explicada"]
        docente["👤 Docente<br/><i>Usuario secundario</i><br/>Digitaliza ejercicios<br/>a LaTeX"]
    end

    sistema["<b>MathScribe</b><br/><i>Sistema</i><br/>Agente visual multimodal que convierte<br/>matemática manuscrita en LaTeX,<br/>la resuelve y la explica paso a paso"]

    gemini["☁️ Google Gemini API<br/><i>Sistema externo</i><br/>Transcribe la imagen a LaTeX<br/>y redacta las explicaciones"]

    estudiante -->|"Captura una expresión<br/>y consulta el resultado"| sistema
    docente -->|"Digitaliza expresiones"| sistema
    sistema -->|"Envía la imagen recortada<br/>y los pasos a redactar<br/><b>HTTPS / SDK</b>"| gemini
    gemini -->|"LaTeX y texto explicativo"| sistema

    style sistema fill:#1f2937,stroke:#111827,color:#fff
    style gemini fill:#dbeafe,stroke:#2563eb
    style externo fill:none,stroke:none
```

**Decisión de contexto:** el único sistema externo es Gemini. No hay
integraciones con plataformas educativas ni servicios de autenticación de
terceros; reduce la superficie de dependencia y el alcance del tratamiento de
datos personales.

---

## Nivel 2 — Contenedores

Las piezas desplegables y cómo se comunican.

```mermaid
flowchart TB
    usuario["👤 Estudiante"]

    subgraph render["☁️ Render"]
        spa["<b>SPA Web</b><br/>[React 18 + TypeScript + Vite]<br/>Sitio estático servido por CDN<br/><br/>Captura por cámara, render de<br/>LaTeX con KaTeX y panel<br/>de métricas"]

        api["<b>API</b><br/>[Python 3.11 + FastAPI, Docker]<br/>Web Service<br/><br/>Orquesta visión, reconocimiento,<br/>resolución y explicación.<br/>Instrumenta latencia y consumo"]

        db[("<b>Base de datos</b><br/>[PostgreSQL 16]<br/>Servicio administrado<br/><br/>Usuarios y<br/>conversiones")]
    end

    gemini["☁️ <b>Google Gemini</b><br/>gemini-3.5-flash"]

    usuario -->|"HTTPS"| spa
    spa -->|"JSON sobre HTTPS<br/>/api/v1/*"| api
    api -->|"SQL sobre TCP<br/>SQLAlchemy + psycopg"| db
    api -->|"HTTPS<br/>SDK google-genai"| gemini

    style spa fill:#dcfce7,stroke:#16a34a
    style api fill:#1f2937,stroke:#111827,color:#fff
    style db fill:#fef3c7,stroke:#d97706
    style gemini fill:#dbeafe,stroke:#2563eb
    style render fill:#f9fafb,stroke:#d1d5db
```

### Justificación de la separación

| Contenedor | Por qué está separado |
|---|---|
| **SPA estática** | No necesita servidor de aplicación: se sirve desde CDN, escala sin costo y aísla los fallos del backend de la disponibilidad de la interfaz |
| **API en Docker** | Requiere Python con OpenCV y SymPy, dependencias nativas que exigen una imagen controlada. El contenedor garantiza que lo que corre en producción es lo mismo que en desarrollo |
| **PostgreSQL administrado** | Los datos son relacionales (usuario → conversiones) y delegar la operación evita gestionar respaldos y actualizaciones |

**Nota sobre el estado:** la API es **sin estado** salvo por el registro de
métricas, que vive en memoria del proceso y se reinicia con él. Es una decisión
consciente de alcance, documentada en `cloud-native.md`: mantener un histórico
exigiría infraestructura de observabilidad fuera del alcance del proyecto.

---

## Nivel 3 — Componentes de la API

El interior del contenedor que concentra la lógica.

```mermaid
flowchart TB
    spa["SPA Web"]

    subgraph apic["Contenedor: API (FastAPI)"]
        direction TB

        subgraph capa_api["Capa de entrada"]
            router["<b>Router v1</b><br/>[APIRouter]<br/>Monta y versiona<br/>los endpoints"]
            e_rec["<b>Endpoint<br/>recognition</b>"]
            e_solve["<b>Endpoint<br/>solve</b>"]
            e_met["<b>Endpoint<br/>metrics</b>"]
            e_auth["<b>Endpoints<br/>auth / history</b>"]
        end

        mw["<b>Middleware de métricas</b><br/>[app.core.metrics]<br/>Cronometra cada petición,<br/>muestrea CPU y memoria"]

        subgraph capa_serv["Capa de servicios"]
            s_rec["<b>RecognitionService</b><br/>Orquesta visión + proveedor"]
            prep["<b>preprocessing</b><br/>[OpenCV]<br/>Gris, ruido, umbral<br/>adaptativo y recorte de ROI"]
            prov["<b>RecognitionProvider</b><br/><i>interfaz</i><br/>Gemini · OpenAI · Mathpix"]
            s_solve["<b>SolverService</b><br/>Orquesta cálculo + redacción"]
            sympy_c["<b>sympy_solver</b><br/>[SymPy]<br/>Integra, deriva, resuelve<br/>y simplifica"]
            expl["<b>explainer</b><br/>Redacta los pasos<br/>y valida la respuesta"]
        end

        cli["<b>gemini_client</b><br/>[google-genai]<br/>Cliente compartido y<br/>contabilidad de tokens"]
        cfg["<b>config</b><br/>[pydantic-settings]<br/>Variables de entorno"]
    end

    db[("PostgreSQL")]
    gemini["Google Gemini"]

    spa --> mw --> router
    router --> e_rec & e_solve & e_met & e_auth

    e_rec --> s_rec
    s_rec --> prep --> prov
    prov --> cli

    e_solve --> s_solve
    s_solve --> sympy_c
    s_solve --> expl --> cli

    cli --> gemini
    e_met -.->|"consulta agregados"| mw
    e_met -.->|"consulta tokens"| cli
    e_auth --> db
    cfg -.->|"configura"| cli
    cfg -.->|"configura"| s_rec

    style sympy_c fill:#dcfce7,stroke:#16a34a,stroke-width:3px
    style prep fill:#dcfce7,stroke:#16a34a
    style cli fill:#dbeafe,stroke:#2563eb
    style prov fill:#e0e7ff,stroke:#6366f1
```

En verde, los componentes que ejecutan **cómputo propio y determinista**
(OpenCV y SymPy); en azul, los que dependen del modelo externo. La frontera
entre ambos es la garantía central del sistema: **el resultado matemático se
calcula en verde y sólo se narra en azul**.

### Responsabilidad de cada componente

| Componente | Responsabilidad | Por qué está aislado |
|---|---|---|
| `preprocessing` | Limpieza y detección de ROI con OpenCV | Cumple el requisito de visión open source y es sustituible sin tocar el resto |
| `RecognitionProvider` | Contrato imagen → LaTeX | Permite cambiar de proveedor de IA sin modificar la API ni el frontend. Es la mitigación del riesgo de dependencia externa |
| `gemini_client` | Cliente y contabilidad de tokens | Único punto por el que pasan las llamadas al modelo, lo que hace fiable la medición de consumo |
| `sympy_solver` | Cálculo simbólico | Fuente de verdad del resultado. No depende de ningún servicio externo |
| `explainer` | Redacción y **validación** de la respuesta | Descarta explicaciones que no encajen con los pasos calculados |
| `metrics` | Instrumentación transversal | Middleware: mide sin que los endpoints tengan que colaborar |

---

## Flujo de una petición completa

```mermaid
sequenceDiagram
    autonumber
    participant U as Estudiante
    participant S as SPA
    participant M as Middleware
    participant R as RecognitionService
    participant O as OpenCV
    participant G as Gemini
    participant Y as SymPy
    participant E as Explainer

    U->>S: Captura la expresión
    S->>M: POST /api/v1/recognition
    M->>M: inicia el cronómetro
    M->>R: delega
    R->>O: preprocesa y recorta la ROI
    O-->>R: imagen limpia
    R->>G: imagen + prompt de transcripción
    G-->>R: LaTeX
    R-->>M: RecognitionResponse
    M->>M: registra latencia y tokens
    M-->>S: 200 con el LaTeX

    S-->>U: muestra el LaTeX reconocido
    Note over U,S: Punto de verificación humana:<br/>el usuario confirma antes de resolver

    U->>S: pulsa «Resolver»
    S->>M: POST /api/v1/solve
    M->>Y: resuelve la expresión
    Y-->>M: resultado y pasos verificados
    M->>E: pasos a redactar
    E->>G: pasos + prompt de explicación
    G-->>E: descripciones
    E->>E: valida que encajen con los pasos
    E-->>M: pasos redactados
    M-->>S: 200 con resultado y pasos
    S-->>U: resultado, procedimiento y aviso de verificación
```

---

## Decisiones arquitectónicas relevantes

| # | Decisión | Alternativa descartada | Motivo |
|---|---|---|---|
| 1 | El cálculo lo hace SymPy, no el modelo | Pedirle a Gemini que resuelva | Convierte el resultado en determinista y verificable; elimina la alucinación matemática por diseño |
| 2 | Reconocimiento tras una interfaz | Llamar a Gemini directamente desde los endpoints | Cambiar de proveedor no toca la API ni el frontend |
| 3 | Dos endpoints (reconocer y resolver) en vez de uno | Un único endpoint de extremo a extremo | Habilita la verificación humana intermedia y evita gastar cuota resolviendo transcripciones incorrectas |
| 4 | Frontend estático, sin renderizado en servidor | Next.js con SSR | No hay necesidad de SEO ni de datos en el servidor; abarata y simplifica el despliegue |
| 5 | Métricas en memoria del proceso | Prometheus o similar | Suficiente para caracterizar el sistema en una sesión; la infraestructura completa excede el alcance |
| 6 | Degradación en lugar de error | Propagar 500 ante fallo del modelo | Una API caída por un tercero es peor experiencia que una respuesta vacía con aviso |

---

## Referencias

- [`cloud-native.md`](./cloud-native.md) — topología de despliegue y principios operativos.
- [`bpmn.md`](./bpmn.md) — el mismo flujo desde la perspectiva de proceso de negocio.
- [`../devops/despliegue-y-permisos.md`](../devops/despliegue-y-permisos.md) — configuración real del despliegue.
