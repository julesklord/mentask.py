import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from mentask.core.process_tracker import ProcessTracker

@pytest.fixture(autouse=True)
def reset_tracker():
    """Reset the singleton instance and its state before each test."""
    ProcessTracker._instance = None
    ProcessTracker._active_processes.clear()
    yield
    ProcessTracker._instance = None
    ProcessTracker._active_processes.clear()

def test_singleton():
    t1 = ProcessTracker()
    t2 = ProcessTracker()
    assert t1 is t2

def test_register_unregister():
    tracker = ProcessTracker()
    mock_proc = MagicMock(spec=asyncio.subprocess.Process)
    mock_proc.pid = 12345

    tracker.register(mock_proc)
    assert mock_proc in tracker._active_processes

    tracker.unregister(mock_proc)
    assert mock_proc not in tracker._active_processes

@pytest.mark.asyncio
async def test_kill_all_empty():
    tracker = ProcessTracker()
    await tracker.kill_all()
    assert len(tracker._active_processes) == 0

@pytest.mark.asyncio
async def test_kill_all_graceful():
    tracker = ProcessTracker()

    # Process that is already finished
    mock_proc_finished = AsyncMock(spec=asyncio.subprocess.Process)
    mock_proc_finished.returncode = 0
    mock_proc_finished.pid = 111

    # Process that is still running and will be killed
    mock_proc_running = AsyncMock(spec=asyncio.subprocess.Process)
    mock_proc_running.returncode = None
    mock_proc_running.pid = 222

    tracker.register(mock_proc_finished)
    tracker.register(mock_proc_running)

    await tracker.kill_all()

    assert len(tracker._active_processes) == 0
    mock_proc_finished.kill.assert_not_called()
    mock_proc_running.kill.assert_called_once()
    mock_proc_running.wait.assert_awaited_once()

@pytest.mark.asyncio
async def test_kill_all_timeout():
    tracker = ProcessTracker()

    mock_proc = AsyncMock(spec=asyncio.subprocess.Process)
    mock_proc.returncode = None
    mock_proc.pid = 333

    # Make wait() raise TimeoutError
    mock_proc.wait.side_effect = asyncio.TimeoutError()

    tracker.register(mock_proc)

    await tracker.kill_all()

    assert len(tracker._active_processes) == 0
    mock_proc.kill.assert_called_once()
    mock_proc.wait.assert_awaited_once()

@pytest.mark.asyncio
async def test_kill_all_exception():
    tracker = ProcessTracker()

    mock_proc = AsyncMock(spec=asyncio.subprocess.Process)
    mock_proc.returncode = None
    mock_proc.pid = 444

    # Make kill() raise an Exception
    mock_proc.kill.side_effect = RuntimeError("Failed to kill")

    tracker.register(mock_proc)

    await tracker.kill_all()

    assert len(tracker._active_processes) == 0
    mock_proc.kill.assert_called_once()
    mock_proc.wait.assert_not_awaited()
