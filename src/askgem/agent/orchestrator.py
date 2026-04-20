import os
from collections.abc import AsyncGenerator, Callable
from typing import Any

from .core.execution import ExecutionManager
from .core.provider import ProviderManager
from .schema import AgentTurnStatus, Message, Role, ToolResult
from .tools.base import ToolRegistry


class AgentOrchestrator:
    """
    High-level Coordinator for AskGem.
    Implements the Thinking -> Action -> Observation loop by orchestrating 
    specialized managers.
    """

    def __init__(self, client, tool_registry: ToolRegistry, config: Any = None):
        self.client = client
        self.tools = tool_registry
        self.config = config
        self.active_status = AgentTurnStatus.IDLE
        
        # Specialized Managers (Modular Architecture)
        self.provider = ProviderManager(client)
        self.executor = ExecutionManager(tool_registry)

    def _build_plan_context(self, plan_file: str = ".askgem_plan.md") -> str:
        if not os.path.exists(plan_file):
            return ""

        try:
            with open(plan_file, encoding="utf-8") as handle:
                raw_plan = handle.read().strip()
        except Exception:
            return ""

        if not raw_plan:
            return ""

        return (
            f"\n\n## ACTIVE EXECUTION PLAN (from {plan_file}):\n"
            "You are currently executing the following multi-turn plan. "
            "Reference this to maintain state and know your next steps:\n"
            f"```markdown\n{raw_plan}\n```"
        )

    def _build_turn_config(self, config: Any | None) -> Any | None:
        plan_context = self._build_plan_context()
        if not plan_context or not config or not hasattr(config, "system_instruction"):
            return config

        from copy import copy
        turn_config = copy(config)
        instruction = turn_config.system_instruction or ""
        turn_config.system_instruction = f"{instruction}{plan_context}"
        return turn_config

    def _find_tool_call_name(self, tool_calls: list[Any], tool_call_id: str) -> str:
        for tool_call in tool_calls:
            if tool_call.id == tool_call_id:
                return tool_call.name
        return "unknown"

    async def run_query(
        self,
        user_prompt: str | Any,
        history: list[Message],
        config: Any | None = None,
        confirmation_callback: Callable | None = None,
    ) -> AsyncGenerator[Any, None]:
        """
        Main Agentic Loop. Coordinates thinking and execution phases.
        """
        # 1. Setup Turn
        history.append(Message(role=Role.USER, content=user_prompt))
        self.active_status = AgentTurnStatus.THINKING

        while True:
            await self.executor.ensure_lsp_started()
            yield {"status": AgentTurnStatus.THINKING}

            try:
                turn_config = self._build_turn_config(config)
                # Delegate LLM streaming to ProviderManager
                async for event in self.provider.stream_turn(
                    history, 
                    self.tools.get_all_schemas(), 
                    config=turn_config
                ):
                    yield event
                assistant_msg = history[-1]
            except Exception as exc:
                yield {"type": "error", "content": f"Critical model failure: {exc}"}
                break

            # 2. Check for completion
            if not assistant_msg.tool_calls:
                self.active_status = AgentTurnStatus.COMPLETED
                yield {"status": AgentTurnStatus.COMPLETED}
                break

            # 3. Execution Phase
            self.active_status = AgentTurnStatus.EXECUTING
            yield {"status": AgentTurnStatus.EXECUTING, "tool_calls": assistant_msg.tool_calls}

            # Delegate execution batch to ExecutionManager
            all_results = await self.executor.run_batch(
                assistant_msg.tool_calls, 
                confirmation_callback,
                client=self.client
            )

            # 4. Process Observations
            tool_call_map = {tc.id: tc for tc in assistant_msg.tool_calls}
            for result in all_results:
                tool_call = tool_call_map.get(result.tool_call_id)
                if tool_call is not None:
                    # Enrich result with LSP diagnostics if applicable
                    result = await self.executor.append_lsp_diagnostics(tool_call, result)
                
                tool_name = self._find_tool_call_name(assistant_msg.tool_calls, result.tool_call_id)

                history.append(
                    Message(
                        role=Role.TOOL,
                        content=result.content,
                        metadata={"tool_call_id": result.tool_call_id, "tool_name": tool_name},
                    )
                )
                yield {
                    "type": "tool_result",
                    "content": result.content,
                    "is_error": result.is_error,
                    "tool_name": tool_name,
                }
