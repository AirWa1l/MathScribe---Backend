# Evidencias funcionales — Docker y CI/CD

**Responsable:** Daniel Rojas Barreneche (DevOps)
**Versión:** 1.0 — 21 de julio de 2026

Procedimientos **reproducibles** para verificar que la contenerización y el
pipeline funcionan. Cada apartado indica el comando, lo que debe observarse y la
captura que lo documenta.

El criterio de este documento es que la evidencia sea *repetible por un tercero*:
cualquiera con el repositorio puede ejecutar estos comandos y obtener el mismo
resultado, en lugar de tener que creerse una captura.

---

## 1. Contenerización

### 1.1 Construir la imagen

```bash
docker build -f infra/Dockerfile -t mathscribe-api .
```

**Qué debe observarse:** la construcción termina sin error y reporta las capas.
Las dependencias se instalan antes de copiar el código, de modo que un cambio en
el código no invalida esa capa y las reconstrucciones posteriores son rápidas.

```bash
docker images mathscribe-api
```

📷 `capturas/01-docker-build.png`

### 1.2 Ejecutar el contenedor

```bash
docker run --rm -p 8000:8000 --env-file .env mathscribe-api
```

**Qué debe observarse:** Uvicorn arranca y queda escuchando en el puerto 8000.

Verificación desde otra terminal:

```bash
curl http://localhost:8000/health
# {"status":"ok","environment":"development"}

curl -X POST http://localhost:8000/api/v1/solve \
  -H "Content-Type: application/json" \
  -d '{"latex": "\\int_0^1 x^2\\,dx"}'
# {"result":"\\frac{1}{3}","steps":[...]}
```

📷 `capturas/02-docker-run.png`

### 1.3 Sistema completo con Docker Compose

```bash
docker compose -f infra/docker-compose.yml up --build
```

Levanta la API y PostgreSQL con la red entre ambos. Verificación:

```bash
docker compose -f infra/docker-compose.yml ps
curl http://localhost:8000/health
```

📷 `capturas/03-docker-compose.png`

### 1.4 Cerrar

```bash
docker compose -f infra/docker-compose.yml down -v
```

---

## 2. Pipeline de integración continua

### 2.1 Ejecución en un pull request

Cada PR dispara el workflow definido en `.github/workflows/ci.yml`, con cuatro
pasos: lint con Ruff, formato con Black, pruebas con cobertura y publicación del
reporte.

**Qué debe observarse:** los cuatro pasos en verde y la línea final del reporte:

```
Required test coverage of 85% reached. Total coverage: 95.83%
116 passed
```

**En un pull request el job de despliegue no se ejecuta**, por diseño: la
condición `github.ref == 'refs/heads/main' && github.event_name == 'push'` impide
que un PR publique nada.

📷 `capturas/04-ci-pull-request.png`

### 2.2 Ejecución en `main` con despliegue

Al mergear, el mismo workflow ejecuta además el job `deploy`, que notifica a
Render mediante el Deploy Hook.

**Qué debe observarse:**

```
Notificando a Render el commit abc1234…
Despliegue solicitado correctamente.
```

La URL del hook aparece censurada como `***`: GitHub oculta automáticamente el
valor de los secretos en los registros.

📷 `capturas/05-ci-deploy.png`

### 2.3 Despliegue recibido en Render

En el panel de Render, el servicio registra un despliegue nuevo con el mismo
identificador de commit que disparó el pipeline. **Esa correspondencia entre el
commit y el despliegue es la evidencia del ciclo completo de entrega continua.**

📷 `capturas/06-render-deploy.png`

### 2.4 Un fallo detiene la cadena

Evidencia de que la validación no es decorativa: durante el Sprint 3, un fallo de
resolución de dependencias hizo que el pipeline instalara una versión distinta
del SDK de Gemini a la del entorno local. El pipeline falló, **el despliegue no
se ejecutó** y el defecto se corrigió antes de llegar a producción.

Está descrito en `../scrum/sprint-02-review-retro.md` §5 y en el documento
técnico §8.

📷 `capturas/07-ci-fallo.png` *(opcional, pero es la evidencia más convincente:
demuestra que el pipeline realmente bloquea)*

---

## 3. Verificación del despliegue público

```bash
curl https://mathscribe-api.onrender.com/health

curl -X POST https://mathscribe-api.onrender.com/api/v1/solve \
  -H "Content-Type: application/json" \
  -d '{"latex": "x^2 - 4 = 0"}'

curl https://mathscribe-api.onrender.com/api/v1/metrics
```

> **Antes de la demostración:** los servicios del plan gratuito se suspenden tras
> 15 minutos de inactividad y tardan entre 30 y 60 segundos en despertar. La
> primera petición puede parecer que falla cuando en realidad está arrancando.
> Conviene lanzar estos comandos unos minutos antes.

---

## 4. Reproducir la validación en local

Los mismos checks que ejecuta el pipeline:

```bash
# Backend
ruff check .
black --check .
pytest --cov=app --cov=services --cov=shared --cov-fail-under=85

# Frontend
npm run lint
npm run test:cov
npm run build
```

Si estos pasan en local, el pipeline pasa — **con una salvedad aprendida en el
Sprint 3**: si las versiones instaladas difieren, el resultado puede diferir. Ante
un fallo que sólo ocurre en el pipeline, lo primero es comparar las versiones,
no el código.

---

## Referencias

- `infra/Dockerfile`, `infra/docker-compose.yml` — contenerización.
- `.github/workflows/ci.yml` — definición del pipeline.
- [`despliegue-y-permisos.md`](./despliegue-y-permisos.md) — configuración y secretos.
