# Definition of Done — MathScribe

Una historia o tarea se considera **terminada (Done)** cuando cumple *todos* los
criterios de esta lista. Aplica por igual al backend y al frontend; los puntos
específicos de cada repo se indican entre paréntesis.

## Criterios generales

1. **Compila y linta sin errores.**
   - Backend: `ruff check .` y `black --check .` pasan en verde.
   - Frontend: `npm run lint` (o el linter configurado) pasa en verde.
2. **Tiene al menos una prueba automatizada asociada** cuando agrega lógica (no
   solo estructura o documentación).
   - Backend: `pytest` en verde.
   - Frontend: `npm run test` (Vitest) en verde.
3. **CI pasa en verde** en el PR (build + lint + formato + pruebas). El pipeline
   está definido en `.github/workflows/ci.yml`.
4. **Tiene un Pull Request revisado y mergeado a `main`.**
   - `main` está protegida; no se hace push directo.
   - El PR incluye una descripción corta de qué cambia y por qué.
   - Se revisa entre pares (o se auto-aprueba si el equipo lo acuerda para una
     tarea de bajo riesgo, dejando constancia en el PR).
5. **No expone credenciales ni secretos.** Cualquier variable nueva se agrega a
   `.env.example` sin valor real; los valores reales viven solo en entornos y en
   los *secrets* del repositorio.
6. **Documentado** en el `README` (o en `docs/`) cuando cambia algo de cara al
   usuario, al contrato de la API o al proceso de *setup*.

## Verificación previa a commit (backend, obligatoria)

Antes de crear cualquier commit se ejecutan los mismos checks que corre el
pipeline y se confirma que los tres pasan en verde:

```bash
ruff check .        # lint (0 errores)
black --check .     # formato (sin reformateos pendientes)
pytest              # pruebas (todas en verde)
```

Si `black --check .` reporta archivos, se aplica `black .` y se vuelve a
verificar antes de commitear.

## Notas

- Convención de commits: **Conventional Commits** (`feat:`, `fix:`, `docs:`,
  `test:`, `chore:`…).
- Ramas `feature/*`, `fix/*`, `test/*` y `docs/*`; `main` protegida.
- Docstrings y comentarios en español, alineados con la documentación del
  proyecto.
