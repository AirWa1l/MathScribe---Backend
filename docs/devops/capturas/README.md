# Capturas de evidencia — Docker y CI/CD

Evidencia visual de los entregables 4 (Docker) y 5 (Pipeline CI/CD). El
procedimiento para obtener cada una está en [`../evidencias.md`](../evidencias.md).

| Archivo | Qué debe mostrar |
|---|---|
| `01-docker-build.png` | Construcción de la imagen terminada sin error |
| `02-docker-run.png` | Contenedor en ejecución y `/health` respondiendo |
| `03-docker-compose.png` | API y PostgreSQL levantados juntos |
| `04-ci-pull-request.png` | Workflow en verde en un PR, sin job de despliegue |
| `05-ci-deploy.png` | Job `deploy` en `main` con el hook censurado como `***` |
| `06-render-deploy.png` | Despliegue en Render con el mismo commit |
| `07-ci-fallo.png` | Opcional: una ejecución fallida que bloqueó el despliegue |

La más valiosa es la `06`: la correspondencia entre el commit que disparó el
pipeline y el despliegue registrado en la plataforma es lo que evidencia el
ciclo completo de entrega continua.
