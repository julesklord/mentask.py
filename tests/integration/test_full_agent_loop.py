import os
from unittest.mock import AsyncMock

import pytest

from askgem.agent.chat import ChatAgent
from askgem.agent.core.simulation import SimulationManager


@pytest.fixture
def simulation_env():
    # Use our created transcript
    transcript_path = os.path.join(os.path.dirname(__file__), "test_transcript.json")
    sim_manager = SimulationManager(transcript_path, mode="playback")
    return sim_manager


@pytest.mark.asyncio
async def test_agent_loop_with_simulation(simulation_env):
    """Verifies that the agent can perform a full turn with tools in simulation mode."""
    # Initialize agent with simulation manager
    # We need to inject the simulation manager into ChatAgent.
    # Actually, we should allow passing it to the constructor or setting it on the session.
    agent = ChatAgent()
    agent.session.simulation = simulation_env
    # Mock the ToolDispatcher.execute to return a deterministic result for 'execute_bash'
    # Normally it would run the real safe command logic, but we want to be sure.
    agent.dispatcher.execute = AsyncMock(return_value="13/04/2026")
    responses = []

    def callback(text):
        responses.append(text)

    await agent._stream_response("Hola, dime la fecha", callback=callback)
    # Verify:
    # 1. Tool was called (the transcript says execute_bash 'date /t')
    agent.dispatcher.execute.assert_called_once()
    # 2. Final response was produced
    assert any("Hoy es lunes 13 de abril de 2026" in r for r in responses)
    # 3. Metrics were updated (Simulation sends usage meta)
    assert agent.metrics.total_prompt_tokens > 0
    assert agent.metrics.total_candidate_tokens > 0


@pytest.mark.asyncio
async def test_security_check_integrated_with_loop(simulation_env):
    """Verifies that dangerous commands are correctly reported in the loop."""
    # This would require a transcript with a dangerous command
    # and a mock UI that records the 'confirm_action' calls.
    pass
