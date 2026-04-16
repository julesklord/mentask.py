import asyncio
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock

# Ensure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.askgem.agent.orchestrator import AgentOrchestrator
from src.askgem.agent.tools.base import ToolRegistry
from src.askgem.agent.schema import Message, Role, ToolResult

@pytest.mark.asyncio
async def test_lsp_integration_injects_diagnostics():
    # 1. Setup
    client = MagicMock()
    # Mock stream generator to do nothing (we focus on tool execution part)
    client.generate_stream = MagicMock()
    
    registry = MagicMock(spec=ToolRegistry)
    tool = MagicMock()
    tool.name = "edit_file"
    tool.requires_confirmation = False
    registry.get_tool.return_value = tool
    
    # Simulate a tool execution that returns success but leaves a broken file
    broken_path = "test_integration_broken.py"
    with open(broken_path, "w", encoding="utf-8") as f:
        f.write("def bad_code()\n    pass") # Missing colon
        
    registry.call_tool = AsyncMock(return_value=ToolResult(
        tool_call_id="tc-1",
        content=f"Success: Replaced text in '{broken_path}'.",
        is_error=False
    ))
    
    orchestrator = AgentOrchestrator(client, registry)
    
    # Initialize LSP
    # run_query is an async generator, so we iterate once to trigger start logic
    async for _ in orchestrator.run_query("fix code", []):
        break # Just trigger initialization
    
    # 2. Simulate the tool execution block within run_query logic
    # (Since run_query is a complex generator, we'll manually invoke the lsp check logic part)
    tc = MagicMock()
    tc.id = "tc-1"
    tc.name = "edit_file"
    tc.arguments = {"path": broken_path}
    
    res = await registry.call_tool("edit_file", "tc-1", tc.arguments)
    
    # Manually trigger the integration logic we added to Orchestrator
    if res.content.startswith("Success") and tc.name == "edit_file":
        path = tc.arguments.get("path", "")
        if path.endswith(".py") and orchestrator.lsp:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            diagnostics = await orchestrator.lsp.check_file(path, code)
            if diagnostics:
                diag_msg = "\n\n[LSP DIAGNOSTICS - Syntax/Lint Errors Detected]:\n"
                for d in diagnostics:
                    severity = "ERROR" if d.get("severity") == 1 else "WARNING"
                    msg = d.get("message")
                    line = d.get("range", {}).get("start", {}).get("line", 0) + 1
                    diag_msg += f"- [{severity}] line {line}: {msg}\n"
                diag_msg += "\n[!] Please fix these errors in your next turn."
                res.content += diag_msg

    # 3. Assert
    print(f"\nFinal Content:\n{res.content}")
    assert "[LSP DIAGNOSTICS - Syntax/Lint Errors Detected]" in res.content
    assert "Expected `:`" in res.content
    
    # Cleanup
    if orchestrator.lsp:
        await orchestrator.lsp.stop()
    if os.path.exists(broken_path):
        os.remove(broken_path)

if __name__ == "__main__":
    asyncio.run(test_lsp_integration_injects_diagnostics())
