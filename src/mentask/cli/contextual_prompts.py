# mentask/cli/contextual_prompts.py
"""
Sistema de prompts contextuales para mentask v0.22.0.
Soporta múltiples contextos (coding, music, analysis) con variantes por modelo.
Integración seamless con el sistema de temas existente.
"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .themes import ThemeConfig


class ContextType(str, Enum):
    """Tipos de contexto disponibles para mentask."""
    CODING = "coding"
    MUSIC_PRODUCTION = "music"
    ANALYSIS = "analysis"
    GENERAL = "general"
    CREATIVE = "creative"


@dataclass
class ContextualPrompt:
    """Representa un prompt contextual con variantes por modelo."""
    context: ContextType
    system_prompt: str
    task_examples: list[str]
    constraints: list[str]
    tone: str  # "professional", "creative", "direct", "technical"
    model_variants: dict[str, str]  # {model_family: adapted_prompt}


class ContextualPromptLibrary:
    """Biblioteca de prompts contextuales reutilizables."""

    PROMPTS = {
        ContextType.CODING: ContextualPrompt(
            context=ContextType.CODING,
            system_prompt="""Eres un experto en ingeniería de software y arquitectura de código.
Tu rol es ayudar con:
- Diseño y refactorización de código limpio
- Debugging y optimización
- Arquitectura de sistemas escalables
- Testing y CI/CD

Mantén un enfoque KISS (Keep It Simple, Stupid).
Siempre verifica y explica tu lógica antes de proponer soluciones.
Si hay múltiples enfoques, presenta trade-offs honestamente.""",
            task_examples=[
                "Refactor this async function to improve error handling",
                "Design a caching layer for this database query",
                "Help me architect a microservices system",
                "Debug this memory leak in Node.js",
            ],
            constraints=[
                "Nunca asumas sin verificar",
                "Explica el trade-off de cada decisión",
                "Proporciona tests junto con el código",
                "Considera performance desde el inicio",
            ],
            tone="technical",
            model_variants={
                "claude": """You are an expert software engineer with deep knowledge of async patterns and system design.
Focus on correctness first, optimization second. Always explain your reasoning and verify assumptions.
Use the KISS principle religiously. Avoid over-engineering.""",
                "gpt": """As a senior software architect, provide clear, actionable solutions.
Break down complex problems into smaller, testable components.
Consider multiple approaches and explain trade-offs objectively.""",
                "groq": """You are a pragmatic code reviewer. Be direct and concise.
Focus on what works, explain why, and highlight risks.
Value speed and clarity over lengthy explanations.""",
            },
        ),
        ContextType.MUSIC_PRODUCTION: ContextualPrompt(
            context=ContextType.MUSIC_PRODUCTION,
            system_prompt="""Eres un productor musical experto y audio engineer con 15+ años de experiencia.
Tu rol es:
- Guiar en mixing y mastering
- Optimizar cadenas de procesamiento de audio
- Arquitectura de proyectos DAW (REAPER, Pro Tools, Ableton)
- Workflow y automatización de audio
- Microtonalidad y síntesis de sonido

Hablas castellano con mezcla técnica en inglés.
Siempre da opciones prácticas basadas en equipamiento real.
KISS philosophy: soluciones directas, evita overcomplicate.""",
            task_examples=[
                "Cómo hacer headroom en un mix con demasiados tracks",
                "Cadena de procesamiento para voz rap en REAPER",
                "Optimizar latency en setup de 40GB RAM + GTX 1060",
                "Síntesis substractiva para bajos psicodélicos",
            ],
            constraints=[
                "Verifica capacidades de la DAW antes de sugerir",
                "Considera el equipamiento real del usuario",
                "Proporciona valores numéricos específicos (dB, Hz, ms)",
                "Explica el 'por qué' antes del 'cómo'",
            ],
            tone="direct",
            model_variants={
                "claude": """You are a seasoned music producer and audio engineer.
Provide production insights with practical, implementable solutions.
Consider real hardware constraints (CPU, RAM, audio interfaces).
Use technical terminology but always explain in Spanish-friendly context.""",
                "gpt": """As an experienced mixing engineer, guide with precision.
Consider both technical specs and creative intent.
Provide step-by-step solutions with parameter examples.""",
                "groq": """You're a quick, practical music tech expert.
Give direct, tested solutions. Be specific with numbers (dB, Hz, ms).
Skip theory unless critical to understanding.""",
            },
        ),
        ContextType.ANALYSIS: ContextualPrompt(
            context=ContextType.ANALYSIS,
            system_prompt="""Eres un analista experto en datos, sistemas y procesos.
Tu rol:
- Extraer insights de datos complejos
- Identificar patrones y anomalías
- Proporcionar análisis causal
- Visualizar información compleja de forma clara
- Hacer recomendaciones basadas en evidencia

Sé escéptico pero justo. Verifica fuentes.
Distingue entre correlación y causalidad.
Presenta incertidumbre explícitamente.""",
            task_examples=[
                "Analiza las tendencias de mercado de los últimos 5 años",
                "Identifica bottlenecks en este pipeline de datos",
                "Qué factores correlacionan con este comportamiento anómalo",
                "Visualiza esta matriz de confusión de forma comprensible",
            ],
            constraints=[
                "Verifica todas las fuentes de datos",
                "Diferencia entre correlación y causalidad",
                "Expresa incertidumbre en intervalos de confianza",
                "Evita bias confirmation en análisis",
            ],
            tone="analytical",
            model_variants={
                "claude": """You are a rigorous data analyst.
Verify assumptions, cite evidence, acknowledge uncertainty.
Use statistical rigor but explain clearly.
Always show your work and reasoning.""",
                "gpt": """As a business intelligence expert, provide actionable insights.
Structure analysis clearly with evidence backing each claim.
Consider both quantitative and qualitative factors.""",
                "groq": """You are a fast pattern-finder.
Spot correlations, highlight anomalies, flag risks.
Be precise with numbers, concise with explanations.""",
            },
        ),
        ContextType.CREATIVE: ContextualPrompt(
            context=ContextType.CREATIVE,
            system_prompt="""Eres un creativo multidisciplinario: músico, escritor, designer.
Tu rol:
- Brainstorm ideas originales
- Refinar conceptos artísticos
- Proporcionar feedback constructivo sobre trabajo creativo
- Balancear innovación con accesibilidad
- Explorar múltiples direcciones creativas

Sé honesto pero respetuoso. Una mala idea dicha bien es mejor que una buena idea suavizada.
Desafiá suposiciones. Preguntá \"¿por qué?\" antes de juzgar.""",
            task_examples=[
                "Help me develop a concept album narrative",
                "Refine this visual design direction",
                "Brainstorm band names that fit our psych/folk vibe",
                "Give honest feedback on my demo track",
            ],
            constraints=[
                "Sé honesto pero constructivo",
                "Cuestiona suposiciones creativas",
                "Proporciona alternativas, no solo crítica",
                "Respeta la visión artística del creador",
            ],
            tone="creative",
            model_variants={
                "claude": """You are a thoughtful creative collaborator.
Challenge assumptions kindly, offer alternatives generously.
Help refine ideas without imposing your vision.
Appreciate both polish and raw authenticity.""",
                "gpt": """As a creative director, provide directional guidance.
Help identify core concept, remove clutter, amplify impact.
Give feedback that's specific and actionable.""",
                "groq": """You are a fast creative catalyst.
Spot what works, suggest quick iterations.
Be encouraging but honest about risks.""",
            },
        ),
    }

    @classmethod
    def get(cls, context: ContextType) -> ContextualPrompt:
        """Obtiene un prompt contextual por tipo."""
        return cls.PROMPTS.get(context, cls.PROMPTS[ContextType.GENERAL] if ContextType.GENERAL in cls.PROMPTS else cls.PROMPTS[ContextType.CODING])

    @classmethod
    def get_adapted(cls, context: ContextType, model_family: str) -> str:
        """Obtiene el prompt adaptado para un modelo específico."""
        prompt = cls.get(context)
        return prompt.model_variants.get(
            model_family.lower(),
            prompt.system_prompt
        )


# TEMAS NEON AVANZADOS
class NeonTheme:
    """Tema neon con soporte para animaciones y efectos visuales."""

    THEMES = {
        "neon_pink": ThemeConfig(
            brand_primary="#ff006e",      # Neon Pink
            brand_secondary="#fb5607",    # Neon Orange
            success="#00ff00",            # Neon Green
            warning="#ffbe0b",            # Neon Yellow
            error="#ff006e",              # Neon Pink
            info="#00d9ff",               # Neon Cyan
            text_primary="#ffffff",
            text_secondary="#00d9ff",
            text_dim="#666666",
            border="#ff006e",
            background="#0a0e27",
            think_color="#ff006e",
            code_theme="monokai",
        ),
        "neon_cyan": ThemeConfig(
            brand_primary="#00d9ff",      # Neon Cyan
            brand_secondary="#00ff00",    # Neon Green
            success="#00ff00",            # Neon Green
            warning="#ffff00",            # Neon Yellow
            error="#ff0080",              # Neon Red
            info="#00d9ff",               # Neon Cyan
            text_primary="#ffffff",
            text_secondary="#00ff00",
            text_dim="#666666",
            border="#00d9ff",
            background="#0a0e27",
            think_color="#00d9ff",
            code_theme="monokai",
        ),
        "neon_purple": ThemeConfig(
            brand_primary="#b537f2",      # Neon Purple
            brand_secondary="#ff006e",    # Neon Pink
            success="#39ff14",            # Neon Green
            warning="#ffff00",            # Neon Yellow
            error="#ff006e",              # Neon Pink
            info="#00d9ff",               # Neon Cyan
            text_primary="#ffffff",
            text_secondary="#b537f2",
            text_dim="#666666",
            border="#b537f2",
            background="#0a0e27",
            think_color="#b537f2",
            code_theme="monokai",
        ),
        "neon_matrix": ThemeConfig(
            brand_primary="#00ff00",      # Neon Green (Matrix)
            brand_secondary="#00aa00",    # Darker Green
            success="#00ff00",            # Neon Green
            warning="#ffff00",            # Neon Yellow
            error="#ff0000",              # Neon Red
            info="#00ffff",               # Neon Cyan
            text_primary="#00ff00",
            text_secondary="#00aa00",
            text_dim="#003300",
            border="#00ff00",
            background="#000000",
            think_color="#00aa00",
            code_theme="monokai",
        ),
    }

    @classmethod
    def get(cls, name: str) -> ThemeConfig:
        """Obtiene un tema neon por nombre."""
        return cls.THEMES.get(name, cls.THEMES["neon_cyan"])


# RENDERIZACIÓN AVANZADA CON RICH
class NeonRenderer:
    """Renderizador avanzado para mentask con efectos neon."""

    def __init__(self, theme: ThemeConfig, use_nerdfonts: bool = True):
        self.theme = theme
        self.use_nerdfonts = use_nerdfonts

    def render_header(self, text: str, context: ContextType) -> str:
        """Renderiza un header con contexto visual."""
        icons_map = {
            ContextType.CODING: "󰅩" if self.use_nerdfonts else "⚙",
            ContextType.MUSIC_PRODUCTION: "🎵",
            ContextType.ANALYSIS: "📊",
            ContextType.CREATIVE: "🎨",
            ContextType.GENERAL: "💬",
        }
        icon = icons_map.get(context, "💬")

        "─" * (len(text) + 4)
        return f"[{self.theme.brand_primary}]╭─ {icon} {text} ─╮[/]\n[{self.theme.brand_primary}]│[/]"

    def render_divider(self) -> str:
        """Renderiza un divisor neon."""
        return f"[{self.theme.brand_primary}]───────────────────────────────────[/]"

    def render_thinking(self, text: str) -> str:
        """Renderiza thinking process con styling neon."""
        return f"[{self.theme.think_color} dim]✦ Pensando...[/]\n[{self.theme.text_secondary}]{text}[/]"

    def render_code_block(self, code: str, language: str = "python") -> str:
        """Renderiza un bloque de código con syntax highlighting neon."""
        header = f"[{self.theme.brand_secondary}]┌─ {language.upper()} ─[/]\n"
        footer = f"\n[{self.theme.brand_secondary}]└──────────────────[/]"
        return f"{header}[{self.theme.info}]{code}[/]{footer}"

    def render_success(self, message: str) -> str:
        """Renderiza mensaje de éxito."""
        return f"[{self.theme.success}]✓ {message}[/]"

    def render_warning(self, message: str) -> str:
        """Renderiza advertencia."""
        return f"[{self.theme.warning}]⚠ {message}[/]"

    def render_error(self, message: str) -> str:
        """Renderiza error."""
        return f"[{self.theme.error}]✗ {message}[/]"

    def render_stats(self, stats: dict) -> str:
        """Renderiza estadísticas en grid neon."""
        lines = [f"[{self.theme.brand_primary}]┌─ STATS ─[/]"]
        for key, value in stats.items():
            lines.append(
                f"[{self.theme.brand_primary}]│[/] "
                f"[{self.theme.text_secondary}]{key}:[/] "
                f"[{self.theme.brand_primary}]{value}[/]"
            )
        lines.append(f"[{self.theme.brand_primary}]└──────────[/]")
        return "\n".join(lines)


# INTEGRACIÓN CON CONFIGMANAGER
class ContextualConfigManager:
    """Administrador de configuración contextual persistente."""

    CONFIG_FILE = ".mentask/contexts.json"

    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path.home() / ".mentask"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / "contexts.json"
        self.contexts = self._load_contexts()

    def _load_contexts(self) -> dict:
        """Carga contextos guardados."""
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text())
            except:
                return self._default_contexts()
        return self._default_contexts()

    def _default_contexts(self) -> dict:
        """Contextos por defecto."""
        return {
            "active_context": ContextType.GENERAL.value,
            "active_theme": "neon_cyan",
            "model_context_map": {
                "claude-opus": ContextType.CODING.value,
                "gpt-4o": ContextType.ANALYSIS.value,
                "mixtral": ContextType.MUSIC_PRODUCTION.value,
            },
            "user_preferences": {
                "use_nerdfonts": True,
                "stream_thinking": True,
                "show_stats": True,
            },
        }

    def save_contexts(self) -> None:
        """Persiste configuración de contextos."""
        self.config_path.write_text(json.dumps(self.contexts, indent=2))

    def set_context(self, context: ContextType) -> None:
        """Cambia el contexto activo."""
        self.contexts["active_context"] = context.value
        self.save_contexts()

    def set_theme(self, theme: str) -> None:
        """Cambia el tema neon activo."""
        self.contexts["active_theme"] = theme
        self.save_contexts()

    def get_active_context(self) -> ContextType:
        """Obtiene el contexto activo."""
        return ContextType(self.contexts.get("active_context", ContextType.GENERAL.value))

    def get_active_theme(self) -> ThemeConfig:
        """Obtiene el tema activo."""
        theme_name = self.contexts.get("active_theme", "neon_cyan")
        return NeonTheme.get(theme_name)


# ORQUESTADOR CONTEXTUAL
class ContextualOrchestrator:
    """Orquestador que integra contexto, prompts y renderización."""

    def __init__(self, config_manager, console):
        self.config_manager = config_manager
        self.console = console
        self.renderer = NeonRenderer(
            config_manager.get_active_theme(),
            config_manager.contexts["user_preferences"]["use_nerdfonts"]
        )

    def prepare_system_prompt(self, model_family: str) -> str:
        """Prepara el system prompt adaptado al contexto y modelo."""
        context = self.config_manager.get_active_context()
        return ContextualPromptLibrary.get_adapted(context, model_family)

    def render_context_header(self) -> str:
        """Renderiza header con contexto actual."""
        context = self.config_manager.get_active_context()
        return self.renderer.render_header(
            f"Contexto: {context.value.upper()}",
            context
        )

    def log_with_context(self, message: str, level: str = "info") -> None:
        """Registra con estilos contextuales."""
        if level == "success":
            self.console.print(self.renderer.render_success(message))
        elif level == "warning":
            self.console.print(self.renderer.render_warning(message))
        elif level == "error":
            self.console.print(self.renderer.render_error(message))
        else:
            self.console.print(f"[{self.renderer.theme.info}]ℹ {message}[/]")
