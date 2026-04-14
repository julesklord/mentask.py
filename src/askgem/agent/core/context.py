"""
Context management module for AskGem.

Handles system instruction assembly (Memory, Missions, OS) and context window optimization (summarization).
"""

import logging
import os
import platform

from google.genai import types

from ...core.i18n import _
from ...core.memory_manager import MemoryManager
from ...core.mission_manager import MissionManager

_logger = logging.getLogger("askgem")


class ContextManager:
    """Manages the semantic context and memory of the agent."""

    def __init__(self):
        self.memory = MemoryManager()
        self.mission = MissionManager()

    def build_system_instruction(self) -> str:
        """Assembles the full system instruction string."""
        # Base context from localization files
        base_context = _("sys.context", os=f"{platform.system()} {platform.release()}", cwd=os.getcwd())

        # Load persistent memory and active missions
        memory_content = self.memory.read_memory()
        mission_content = self.mission.read_missions()

        full_instruction = f"{base_context}\n\n"
        full_instruction += "## INFORMACIÓN DE MEMORIA PERSISTENTE (memory.md)\n"
        full_instruction += f"{memory_content}\n\n"
        full_instruction += "## MISIONES Y TAREAS ACTIVAS (heartbeat.md)\n"
        full_instruction += f"{mission_content}\n\n"
        full_instruction += "INSTRUCCIÓN CRÍTICA: Usa 'manage_memory' para guardar hechos importantes y 'manage_mission' para rastrear tu progreso."

        return full_instruction

    async def summarize_if_needed(self, session_manager, model_name: str, config_builder: any) -> None:
        """Triggered when history length exceeds a threshold. Compresses early turns."""
        if not session_manager.chat_session:
            return

        history = session_manager.chat_session.get_history()
        # Threshold optimized for Gemini Pro: 100 turns
        if len(history) < 100:
            return

        _logger.info("Context threshold reached (%d messages). Starting summarization...", len(history))

        # We keep the first message (usually user intent) and the last 6 messages (active context)
        first_msg = history[0]
        active_context = history[-6:]
        to_summarize = history[1:-6]

        summary_prompt = "Resume los puntos clave, decisiones técnicas y descubrimientos de esta conversación hasta ahora en un solo párrafo conciso en español. No pierdas detalles sobre rutas de archivos o comandos ejecutados."

        try:
            # We use the client to summarize
            temp_response = await session_manager.client.models.generate_content(
                model=model_name,
                contents=to_summarize + [types.Content(role="user", parts=[types.Part.from_text(text=summary_prompt)])],
                config=types.GenerateContentConfig(temperature=0.3),
            )

            summary_text = temp_response.text
            _logger.info("Context summarized successfully.")

            # Reconstruct history: [Original Start] + [Summary Hub] + [Recent Context]
            summary_part = types.Part.from_text(text=f"[RESUMEN DE CONTEXTO ANTERIOR]: {summary_text}")
            summary_content = types.Content(role="model", parts=[summary_part])

            new_history = [first_msg, summary_content] + active_context

            # Re-initialize the active session with the compacted history
            session_manager.chat_session = session_manager.client.aio.chats.create(
                model=model_name, config=config_builder(), history=new_history
            )

        except Exception as e:
            _logger.error("Failed to summarize context: %s", e)
