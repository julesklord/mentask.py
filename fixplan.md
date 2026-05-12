# Plan de Recuperación del Repositorio (Fix Plan)

Este plan detalla los pasos necesarios para restaurar el código perdido y resolver el estado inconsistente del repositorio dejado por una tarea previa fallida.

## Estado Actual
- El repositorio se encuentra en medio de un merge (PR 138).
- Existen conflictos activos en:
    - `src/mentask/cli/main.py`
    - `tests/agent/core/providers/dummy_cli.py`
    - `tests/core/test_compression.py`
- Se han recuperado archivos básicos (.mentask_knowledge.md, tests de i18n, etc.).
- Se han integrado exitosamente los PRs 141, 140 y 139.

## Objetivos
1. Resolver los conflictos del PR 138 y finalizar su integración.
2. Integrar secuencialmente los PRs restantes (137, 136, 135) y cualquier otro PR relevante detectado (142, 160).
3. Asegurar que todos los tests pasen después de cada integración.
4. Limpiar archivos temporales de la recuperación (patches, logs intermedios).

## Pasos Detallados

### Fase 1: Resolver PR 138
- [ ] Analizar y resolver conflictos en `src/mentask/cli/main.py`.
- [ ] Analizar y resolver conflictos en `tests/agent/core/providers/dummy_cli.py`.
- [ ] Analizar y resolver conflictos en `tests/core/test_compression.py`.
- [ ] Validar con `pytest tests/core/test_compression.py`.
- [ ] Hacer commit del merge.

### Fase 2: Integración de PRs Restantes
Para cada PR en la lista (137, 136, 135, 142, 160):
- [ ] Hacer fetch del branch remoto.
- [ ] Intentar merge.
- [ ] Resolver conflictos si aparecen (especialmente en archivos comunes como `main.py` o mocks de tests).
- [ ] Validar con la suite de tests correspondiente.
- [ ] Hacer commit.

### Fase 3: Validación Final y Limpieza
- [ ] Ejecutar la suite completa de tests (`pytest`).
- [ ] Verificar integridad de archivos clave (`ROADMAP.md`, `.mentask_knowledge.md`).
- [ ] Eliminar `pr140.patch`, `pr141.patch`, `closed_prs.json` y otros archivos temporales si existen.
- [ ] Actualizar `Recovering Lost Codebase Changes.md` indicando la finalización exitosa.

## Lista de PRs a Procesar (Orden Inverso)
1. **PR 138**: `test-compression-coverage-11155417293985932695` (En progreso)
2. **PR 137**: `test-get-global-memory-path-12481053889664646225`
3. **PR 136**: `test-get-tasks-path-18014317426614185659`
4. **PR 135**: `test-context-snapper-get-token-status-10900783634695593359`
5. **PR 142**: `testing-improvement-code-replacer-8701786272809024227`
6. **PR 160**: `test-reset-historical-11066893225969199013`
