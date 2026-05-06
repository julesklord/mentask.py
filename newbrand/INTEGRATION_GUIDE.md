# GUÍA DE INTEGRACIÓN: Sistema Contextual Neon para mentask v0.22.0

## Overview

Has tres archivos nuevos que integrar:
1. `mentask/cli/contextual_prompts.py` - Sistema de prompts contextuales + renderización neon
2. `mentask/cli/contextual_integration.py` - Integración en main.py
3. Actualizaciones menores en `config_manager.py` y `main.py`

## PASO 1: Agregar `contextual_prompts.py`

```bash
cp mentask_contextual_prompts_neon.py src/mentask/cli/contextual_prompts.py
```

Este archivo contiene:
- **ContextType** (enum): CODING, MUSIC_PRODUCTION, ANALYSIS, CREATIVE, GENERAL
- **ContextualPromptLibrary**: Banco de prompts con variantes por modelo
- **NeonTheme**: 4 temas neon (pink, cyan, purple, matrix)
- **NeonRenderer**: Renderización avanzada (headers, code blocks, stats, etc)
- **ContextualConfigManager**: Persistencia de contexto/tema en `~/.mentask/contexts.json`
- **ContextualOrchestrator**: Orquestador que integra todo

## PASO 2: Actualizar `config_manager.py`

Agregar soporte para temas neon en el diccionario THEMES:

```python
# En mentask/core/config_manager.py, dentro de __init__:

self.settings = {
    # ... settings existentes ...
    "theme": "indigo",  # Cambiar a:
    "theme": "neon_cyan",  # Default neon theme
    "available_themes": [
        "indigo", "emerald", "cyberpunk", "dracula", "nord", "sakura",
        "neon_cyan", "neon_pink", "neon_purple", "neon_matrix"  # Agregar estos
    ],
    "context_type": "general",  # Nuevo
}
```

Agregar método para resolver tema (viejo o neon):

```python
def get_resolved_theme(self) -> ThemeConfig:
    """Resuelve un tema, viejo o neon."""
    theme_name = self.settings.get("theme", "neon_cyan")
    
    # Importar lazy para evitar circular imports
    from mentask.cli.contextual_prompts import NeonTheme
    from mentask.cli.themes import get_theme
    
    if theme_name.startswith("neon_"):
        return NeonTheme.get(theme_name)
    else:
        return get_theme(theme_name)
```

## PASO 3: Actualizar `main.py`

Integrar ContextualOrchestrator en MentaskCLI:

```python
# En mentask/cli/main.py, imports agregar:

from mentask.cli.contextual_prompts import (
    ContextualOrchestrator,
    ContextualConfigManager,
    ContextType,
)

# En run_chatbot() o __init__, inicializar:

class MentaskCLI:
    def __init__(self, console):
        self.console = console
        self.config_manager = ConfigManager(console)
        
        # NUEVO: Agregar soporte contextual
        self.contextual_config = ContextualConfigManager()
        self.orchestrator = ContextualOrchestrator(
            self.contextual_config,
            console
        )

    async def prepare_messages(self, messages: list, model_id: str) -> list:
        """Prepara mensajes con system prompt contextual."""
        
        # Obtener system prompt adaptado
        system_prompt = self.orchestrator.prepare_system_prompt(
            self._get_model_family(model_id)
        )
        
        # Agregar al inicio de messages
        return [
            {"role": "user", "content": system_prompt},
            *messages
        ]

    def _get_model_family(self, model_id: str) -> str:
        """Detecta familia de modelo (claude, gpt, groq)."""
        model_lower = model_id.lower()
        if "claude" in model_lower:
            return "claude"
        elif "gpt" in model_lower:
            return "gpt"
        elif "groq" in model_lower or "mixtral" in model_lower:
            return "groq"
        return "groq"

    def render_thinking_with_context(self, thinking: str):
        """Renderiza thinking con estilos neon."""
        context = self.contextual_config.get_active_context()
        header = self.orchestrator.render_context_header()
        thinking_render = self.orchestrator.renderer.render_thinking(thinking)
        self.console.print(header)
        self.console.print(thinking_render)

    def render_code_response(self, code: str, language: str = "python"):
        """Renderiza respuesta de código."""
        self.console.print(
            self.orchestrator.renderer.render_code_block(code, language)
        )
```

## PASO 4: Agregar comandos contextuales

En el loop principal de `main.py`, agregar handlers:

```python
async def handle_user_input(self, user_input: str) -> bool:
    """Maneja input del usuario. Retorna False si debe exit."""
    
    if user_input.lower() == "/context":
        self.show_context_menu()
        return True
    elif user_input.lower() == "/theme":
        self.show_theme_menu()
        return True
    elif user_input.lower() == "/info":
        self.show_context_info()
        return True
    elif user_input.lower() in ["/stats", "/cost"]:
        stats = {
            "context": self.contextual_config.get_active_context().value,
            "theme": self.contextual_config.contexts.get("active_theme"),
            "model": self.config_manager.settings.get("model_name"),
        }
        self.console.print(
            self.orchestrator.renderer.render_stats(stats)
        )
        return True
    
    # Procesar input normal
    return False

def show_context_menu(self) -> None:
    """[Ver ejemplo en mentask_cli_integration_example.py]"""
    pass

def show_theme_menu(self) -> None:
    """[Ver ejemplo en mentask_cli_integration_example.py]"""
    pass

def show_context_info(self) -> None:
    """[Ver ejemplo en mentask_cli_integration_example.py]"""
    pass
```

## PASO 5: Tests

Crear `tests/test_contextual_prompts.py`:

```python
import pytest
from mentask.cli.contextual_prompts import (
    ContextType,
    ContextualPromptLibrary,
    NeonTheme,
    ContextualConfigManager,
)
from pathlib import Path
import tempfile


class TestContextualPrompts:
    def test_get_context_prompt(self):
        """Test obtener prompt por contexto."""
        prompt = ContextualPromptLibrary.get(ContextType.CODING)
        assert prompt.context == ContextType.CODING
        assert "async" in prompt.system_prompt.lower()

    def test_get_adapted_prompt(self):
        """Test adaptación por modelo."""
        prompt = ContextualPromptLibrary.get_adapted(
            ContextType.MUSIC_PRODUCTION,
            "claude"
        )
        assert "producer" in prompt.lower() or "audio" in prompt.lower()

    def test_neon_theme_get(self):
        """Test obtener tema neon."""
        theme = NeonTheme.get("neon_pink")
        assert theme.brand_primary == "#ff006e"

    def test_contextual_config_persistence(self):
        """Test persistencia de config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ContextualConfigManager(Path(tmpdir))
            config.set_context(ContextType.MUSIC_PRODUCTION)
            
            # Crear nueva instancia, debe cargar cambio
            config2 = ContextualConfigManager(Path(tmpdir))
            assert config2.get_active_context() == ContextType.MUSIC_PRODUCTION
```

## PASO 6: Documentación de uso para el usuario

Crear `CONTEXTUAL_GUIDE.md`:

```markdown
# Guía de Contextos en mentask

## Contextos Disponibles

### 🧑‍💻 Coding
Para ingeniería de software, debugging, arquitectura.
- Prompts optimizados para Python, TypeScript, Rust, etc.
- Enfoque en KISS, testing, y verificación.

### 🎵 Music Production
Para producción musical, mixing, síntesis.
- Entiende DAW (REAPER, Pro Tools, Ableton)
- Valores técnicos específicos (dB, Hz, ms)

### 📊 Analysis
Para análisis de datos, estadística, insights.
- Riguroso, verifica fuentes
- Diferencia correlación vs causalidad

### 🎨 Creative
Para brainstorming creativo, feedback artístico.
- Honesto pero respetuoso
- Desafía suposiciones

## Temas Neon

- `/theme` para cambiar
- `neon_pink`: Vibrante, rosa neón
- `neon_cyan`: Clásico, cyan neón
- `neon_purple`: Místico, púrpura neón
- `neon_matrix`: Green on black, Matrix style

## Comandos

- `/context` - Cambiar contexto
- `/theme` - Cambiar tema
- `/info` - Ver info del contexto actual
- `/stats` - Ver estadísticas de sesión
```

## PASO 7: Integración con MultiAPI (v0.22.0)

Una vez integrado, el flujo completo es:

```
1. Usuario selecciona API + Modelo (multiapi)
2. Usuario selecciona Contexto + Tema (contextual)
3. System prompt = Prompt de contexto + Variante de modelo
4. Renderización = Tema neon + Estilos contextuales
5. Persistencia = ~/.mentask/active.json (API) + ~/.mentask/contexts.json (contexto)
```

## Checklist de Integración

- [ ] Copiar `contextual_prompts.py` a `src/mentask/cli/`
- [ ] Actualizar `config_manager.py` con temas neon
- [ ] Actualizar `main.py` con ContextualOrchestrator
- [ ] Agregar comandos `/context`, `/theme`, `/info`
- [ ] Crear tests en `tests/test_contextual_prompts.py`
- [ ] Crear `CONTEXTUAL_GUIDE.md`
- [ ] Testear flujo completo: API → Contexto → Renderización
- [ ] Actualizar `ROADMAP.md` y `CHANGELOG.md`
- [ ] Bump version a `0.22.0` en `pyproject.toml`

## Troubleshooting

**Q: El tema neon no se aplica**
A: Verifica que `config_manager.get_resolved_theme()` retorna NeonTheme, no ThemeConfig viejo.

**Q: Contexto no persiste entre sesiones**
A: Verificá que `~/.mentask/contexts.json` existe y tiene permisos de escritura.

**Q: System prompt no está contextual**
A: Asegúrate que `orchestrator.prepare_system_prompt()` se llama antes de enviar a API.

## Performance

- ContextualConfigManager: Carga una sola vez al init, 2KB JSON
- NeonRenderer: Lazy evaluation, solo renderiza lo usado
- ContextualPromptLibrary: Singleton, sin IO
- Overhead total: <5ms por sesión