# Despliegue en Render: configuración y nota sobre permisos

**Responsable:** Daniel Rojas Barreneche (DevOps / Scrum Master)
**Versión:** 1.0 — 21 de julio de 2026

Documenta cómo está desplegado el sistema, y deja constancia de una limitación
de permisos que condiciona **la forma** en que se conecta el despliegue, no su
funcionamiento.

---

## 1. Nota sobre la titularidad de los repositorios

Los repositorios del proyecto están alojados bajo la cuenta de GitHub de un
integrante del equipo (`AirWa1l`), que actúa como propietario:

- `github.com/AirWa1l/MathScribe---Backend`
- `github.com/AirWa1l/MathScribe---Frontend`

Render requiere **instalar su GitHub App sobre la cuenta propietaria** del
repositorio para poder vincularlo a un servicio. Esa instalación es una acción
de administración de la cuenta: sólo puede autorizarla el propietario, y no
puede delegarse en un colaborador con permisos de escritura sobre el
repositorio.

Como el responsable de DevOps no es el propietario de la cuenta, **el servicio
se creó apuntando a la URL pública del repositorio** en lugar de mediante la
vinculación directa. Render admite ambas modalidades para repositorios públicos.

**Esto es una restricción de gobernanza de cuentas, no una carencia técnica del
proyecto:** el `render.yaml` de cada repositorio está escrito, versionado y es
funcional; en el momento en que el propietario autorice la GitHub App, la
vinculación es cuestión de un par de minutos y sin cambios en el código.

## 2. Qué implica en la práctica

| Capacidad | Con URL pública (situación actual) | Con repositorio vinculado |
|---|---|---|
| Desplegar la aplicación | ✅ Funciona | ✅ Funciona |
| Despliegue manual desde el panel | ✅ Funciona | ✅ Funciona |
| **Despliegue por Deploy Hook** (el que usa nuestro pipeline) | ✅ Funciona | ✅ Funciona |
| Auto-deploy nativo de Render al hacer push | ❌ No disponible | ✅ Disponible |
| Aprovisionar recursos desde `render.yaml` (Blueprint) | ❌ Requiere vinculación | ✅ Disponible |
| Previews automáticos por pull request | ❌ No disponible | ✅ Disponible |

**El punto importante: la cadena de CI/CD del proyecto no depende del auto-deploy
nativo de Render.** El pipeline de GitHub Actions dispara el despliegue mediante
el *Deploy Hook*, que es independiente de cómo se haya vinculado el repositorio:

```
push a main → GitHub Actions → lint + pruebas + cobertura ≥ 50%
            → job deploy → POST al Deploy Hook → Render despliega
```

Esa decisión de diseño se tomó al escribir el pipeline (ver
`.github/workflows/ci.yml`), antes de conocer la restricción de permisos, y es
la razón por la que el despliegue continuo sigue siendo demostrable.

De hecho, disparar el despliegue desde el pipeline es **preferible** al
auto-deploy nativo: con auto-deploy, Render publica cualquier commit que llegue
a `main` aunque las pruebas fallen; con el hook, sólo se despliega lo que ya
pasó lint, pruebas y el umbral de cobertura.

## 3. Configuración actual

### Servicios en Render

| Servicio | Tipo | Origen |
|---|---|---|
| `mathscribe-api` | Web Service (Docker, `infra/Dockerfile`) | URL pública del repositorio |
| `mathscribe-web` | Static Site (build de Vite, publica `dist`) | URL pública del repositorio |

### Variables de entorno (definidas en el panel de Render)

| Variable | Servicio | Notas |
|---|---|---|
| `GEMINI_API_KEY` | api | Secreto. Nunca versionado |
| `GEMINI_MODEL` | api | `gemini-3.5-flash` |
| `JWT_SECRET` | api | Secreto, distinto del de desarrollo |
| `CORS_ORIGINS` | api | URL pública del frontend, sin barra final |
| `DATABASE_URL` | api | La entrega Render; `config.py` le añade el driver `psycopg` |
| `VITE_API_BASE_URL` | web | Se incrusta en el bundle durante el build |

### Secretos en GitHub Actions

| Secreto | Repositorio | Uso |
|---|---|---|
| `RENDER_DEPLOY_HOOK_URL` | backend | Dispara el despliegue de `mathscribe-api` |
| `RENDER_DEPLOY_HOOK_URL` | frontend | Dispara el despliegue de `mathscribe-web` |

`GEMINI_API_KEY` **no** se registra en GitHub: el pipeline ejecuta las pruebas
con dobles de prueba y no realiza llamadas reales al modelo, de modo que la
clave sólo existe en el entorno de ejecución de Render y en los `.env` locales.

## 4. Cómo restaurar la vinculación completa

Cuando el propietario de la cuenta esté disponible, en dos pasos:

1. El propietario entra a Render → **Account Settings → GitHub** → autoriza la
   Render GitHub App sobre los dos repositorios.
2. En cada servicio: **Settings → Build & Deploy → Repository** → seleccionar el
   repositorio vinculado, y activar **Auto-Deploy** si se desea.

Alternativamente, aplicar el Blueprint (**New + → Blueprint**) crea toda la
infraestructura descrita en `render.yaml` de una sola vez.

No se requiere ningún cambio en el código, el `render.yaml` ni el pipeline.

## 5. Limitaciones conocidas del plan gratuito

Relevantes para la demostración en vivo:

- **Suspensión por inactividad:** los servicios gratuitos se detienen tras 15
  minutos sin tráfico y tardan entre 30 y 60 segundos en responder de nuevo. Se
  mitiga abriendo la aplicación unos minutos antes de la sustentación.
- **PostgreSQL gratuito con caducidad:** las instancias gratuitas expiran a los
  30 días. Suficiente para el proyecto; en un entorno real exigiría plan de pago.
- **Minutos de construcción limitados** (500 al mes), holgados para el ritmo del
  equipo.

---

## Referencias

- `render.yaml` (raíz de cada repositorio) — infraestructura como código.
- `.github/workflows/ci.yml` — pipeline de validación y despliegue.
- [Render — Deploy Hooks](https://render.com/docs/deploy-hooks)
- [Render — Blueprints (IaC)](https://render.com/docs/infrastructure-as-code)
