import asyncio
import json
import os
import subprocess
from typing import Any, Dict, List, Optional


class LSPClient:
    """
    Minimal asynchronous LSP client specialized for Ruff Server communication.
    Handles the JSON-RPC handshake and diagnostic retrieval.
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = os.path.abspath(workspace_path)
        self.process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 1
        self._diagnostics: Dict[str, List[Dict[str, Any]]] = {}
        self._initialized = False

    async def start(self) -> bool:
        """Starts the Ruff LSP server as a subprocess."""
        try:
            self.process = await asyncio.create_subprocess_exec(
                "ruff", "server", "--preview",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return await self._handshake()
        except Exception as e:
            print(f"LSP Error: Failed to start ruff server: {e}")
            return False

    async def _send_to_server(self, payload: Dict[str, Any]):
        """Encodes and sends a JSON-RPC message with Content-Length header."""
        if not self.process or not self.process.stdin:
            return

        body = json.dumps(payload).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
        self.process.stdin.write(header + body)
        await self.process.stdin.drain()

    async def _read_from_server(self) -> Optional[Dict[str, Any]]:
        """Parses a single JSON-RPC message from the server's stdout."""
        if not self.process or not self.process.stdout:
            return None

        # 1. Read headers until \r\n\r\n
        content_length = 0
        while True:
            line = await self.process.stdout.readline()
            if not line or line == b"\r\n":
                break
            line_str = line.decode("utf-8").lower()
            if line_str.startswith("content-length:"):
                content_length = int(line_str.split(":")[1].strip())

        if content_length == 0:
            return None

        # 2. Read exact number of bytes for the body
        body = await self.process.stdout.readexactly(content_length)
        return json.loads(body.decode("utf-8"))

    async def _handshake(self) -> bool:
        """Performs the 'initialize' and 'initialized' LSP sequence."""
        init_request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": "initialize",
            "params": {
                "processId": os.getpid(),
                "rootUri": f"file:///{self.workspace_path.replace(os.sep, '/')}",
                "capabilities": {
                    "textDocument": {
                        "publishDiagnostics": {}
                    }
                }
            }
        }
        self._request_id += 1
        await self._send_to_server(init_request)

        # Wait for initialize response
        response = await self._read_from_server()
        if not response or "result" not in response:
            return False

        # Send 'initialized' notification
        await self._send_to_server({
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        })
        self._initialized = True
        return True

    async def check_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Sends code to the server and waits for diagnostics.
        Returns a list of diagnostic objects (errors, warnings, etc.).
        """
        if not self._initialized:
            return [{"message": "LSP Server not initialized"}]

        abs_path = os.path.abspath(file_path)
        uri = f"file:///{abs_path.replace(os.sep, '/')}"

        # 1. Open/Update the document in the server virtuosly
        await self._send_to_server({
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": uri,
                    "languageId": "python",
                    "version": 1,
                    "text": content
                }
            }
        })

        # 2. In a real Client Bridge, we would listen for publishDiagnostics asynchroneously.
        # For this prototype, we'll try to catch the next relevant message or timeout.
        try:
            # We wait a brief moment for Ruff to publish diagnostics
            # Note: This is an simplified synchronous wait for the first diagnostics.
            # In a production version, we would manage a background listener.
            for _ in range(5): 
                msg = await asyncio.wait_for(self._read_from_server(), timeout=1.0)
                if msg and msg.get("method") == "textDocument/publishDiagnostics":
                    params = msg.get("params", {})
                    if params.get("uri") == uri:
                        return params.get("diagnostics", [])
        except asyncio.TimeoutError:
            pass

        return []

    async def stop(self):
        """Cleanly terminates the LSP server process."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
