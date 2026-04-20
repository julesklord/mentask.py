# 📔 Base de Conocimiento: Implementación de Mejoras (Claude Code > AskGem)

Este documento centraliza los hallazgos de la arquitectura de **Claude Code** (referencia) y define la estrategia para inyectar sus mejores prácticas en **AskGem**.

---

## 🏗️ 1. Mapeo Arquitectónico (Cross-Stack)

| Componente Claude Code (TS) | Componente AskGem (Py) | Función |
| :--- | :--- | :--- |
| `QueryEngine.ts` | `src/askgem/agent/orchestrator.py` | Ciclo principal de razonamiento (Think -> Act). |
| `Tool.ts` | `src/askgem/agent/tools_registry.py` | Registro y validación de esquemas de herramientas. |
| `services/compact/` | `src/askgem/core/compression.py` | Estrategias de reducción de tokens y resumen. |
| `ink/` / `components/` | `src/askgem/cli/` (Rich-based) | Interfaz de usuario y renderizado de streaming. |
| `bridge/` | `src/askgem/agent/session_manager.py` | Gestión de sesiones y persistencia remota. |
| `utils/queryContext.ts` | `src/askgem/core/identity_manager.py` | Construcción dinámica del System Prompt. |

---

## 🚀 2. Mejoras Críticas para AskGem (Roadmap de Implementación)

### 🧠 A. Sistema de Compactación Dinámica (Inspirado en `autoCompact.ts`)
Claude Code no solo trunca el historial; genera un "Snip" (Resumen proyectado).
- **Trigger**: Se activa al alcanzar el ~75% del límite de tokens del modelo.
- **Acción**: 
    1. Llamada a `summarizer.py` para generar un `SystemSummary`.
    2. Guardado del historial "sucio" en `.askgem/history/archives/`.
    3. Reinicio de `history_manager` inyectando el `SystemSummary` como primer mensaje `USER`.
- **Diferenciador AskGem**: Mantener el resumen en `.askgem_summary.md` para visibilidad del usuario.

### ⚡ B. Orquestación de Herramientas Avanzada
AskGem ya usa `asyncio.gather`, pero Claude Code maneja mejor las **dependencias** y las **denegaciones**.
- **Orphaned Permissions**: Implementar la detección de herramientas que se quedaron "colgadas" si el proceso murió (usando el archivo de sesión).
- **Security Check Layer**: Separar la lógica de seguridad en un "Middleware" de herramientas (similar a `wrappedCanUseTool` en `QueryEngine.ts`).

### ⌨️ C. Comandos Slash Proactivos
Claude Code procesa comandos como `/clear`, `/force-snip`, `/undo` **antes** de enviar el prompt al modelo.
- **Mejora**: Integrar `command_handler.py` en el ciclo inicial de `run_query` en `orchestrator.py` para interceptar inputs que empiezan con `/`.

### 📺 D. UI Reactiva con Rich Live
Claude Code usa **Ink** para una UI tipo React. AskGem puede usar `rich.live.Live` para:
- Mostrar el "Pensamiento" en un panel colapsable en tiempo real.
- Mostrar una tabla de "Herramientas en Ejecución" que se actualice dinámicamente.
- Status Bar persistente con uso de tokens (Cost Tracker).

---

## 🛠️ 3. Tácticas de Implementación (Flujo de Trabajo)

1. **Investigación Continua**: Usar `grep_search` en Claude Code para encontrar implementaciones específicas de herramientas (ej. `grep_search` en reference_code).
2. **Surgical Updates**: No reescribir `askgem`, sino añadir "Managers" o extender los existentes.
3. **Validation First**: Cada mejora de Claude Code debe ir precedida de un test en `tests/` que verifique la nueva capacidad (ej. `test_autocompact.py`).

---

## 📂 4. Archivos de Referencia Clave (Claude Code)

- `QueryEngine.ts`: El corazón del loop de mensajes.
- `services/compact/autoCompact.ts`: Lógica de thresholds para compactación.
- `services/api/claude.ts`: Manejo de retries y errores de red.
- `utils/messages/systemInit.ts`: Cómo se ensambla el prompt inicial con herramientas.

---
*Nota: Este documento es dinámico y debe actualizarse conforme se descubran nuevos patrones en el código de referencia.*
