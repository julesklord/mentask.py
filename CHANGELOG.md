# Changelog - PyGemAi

## [2.0.0-dev2] - 2026-04-01

### Repensado Completo: Agente Autónomo CLI
- **Migración a SDK v2.0:** Todo el motor ha sido migrado a `google-genai>=0.2.0`, soportando nativamente `gemini-3.1-pro` y los últimos modelos de Google.
- **Tools Autónomas de Sistema y Archivos:** El CLI ahora no es solo un chat, sino un asistente con herramientas. Puede leer y editar archivos en el disco, ejecutar comandos bash (con timeout de 60s) y explorar directorios.
- **Protección "Human-in-the-Loop":** Todas las acciones destructivas y de edición requieren confirmación manual por defecto, protegiendo contra corrupciones accidentales mediante archivos `*.bkp` obligatorios.
- **Detección Dual de Funciones:** Solucionados fallos de streaming en el API de Gemini al invocar herramientas (gracias a detección por SDK y fallback nativo en `candidate.content.parts`).

### Arquitectura Modular Renovada
- **Desacoplamiento:** Estructura limpia y orientada a capas: `core/`, `engine/`, `tools/` y `ui/`.
- **Configuración JSON Pura:** `ConfigManager` actualizado. Todas las configuraciones (`~/.pygemai/settings.json`) ahora son manejadas con simpleza y persistencia automática.
- **Limpieza Total:** Eliminación completa de features obsoletos de la v1.x (sistema de cifrado con `cryptography`, temas rígidos, seguridad compleja) para facilitar su transición a una herramienta de desarrollo DevOps ligera.

### Contexto y Memoria
- **Historial con "Rolling Window":** `HistoryManager` guarda sesión automáticamente en `~/.pygemai/history/` optimizando y truncando las ventanas de tokens en cargas completas.

### Interfaz Renovada
- **Comandos de Barra:** Introducidos `/history load|list|delete`, `/clear`, `/model`, `/mode` (auto/manual) y `/help`.
- **Streaming UI:** Pantalla mejorada con `Rich` soportando Markdown y sintaxis en tiempo real para las respuestas del AI, sin romper las tool invocations intermedias.

---

## [1.3.0] - 2026-03-29

### Auditoria Senior y Refactorización
- **Arquitectura Modular Inicial:** Modulación y separación generalizada en v1.3.
- **Corrección de UX:** Eliminado el bug de "doble impresión".
- **Mejoras Técnicas Iniciales:** Primer paso a `pyproject.toml` (antes `setup.py`) y limpieza de broad exceptions.

---

## [1.2.1] - 2026-03-29
- Correcciones menores de versión y empaquetado inicial pyproject.

## [1.2.0] - Antes
- Versión inicial experimental con gestión de perfiles y temas (Deprecada).
