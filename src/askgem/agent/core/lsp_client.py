import asyncio
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional


class LSPClient:
    """
    Asynchronous LSP client with background reader and request tracking.
    Specialized for Ruff Server.
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = os.path.abspath(workspace_path)
        self.process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 1
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._diagnostics: Dict[str, List[Dict[str, Any]]] = {}
        self._reader_task: Optional[asyncio.Task] = None
        self._initialized = False

    async def start(self) -> bool:
        """Starts the server and initiates the handshake."""
        try:
            self.process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "ruff", "server", "--preview",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Start background reader
            self._reader_task = asyncio.create_task(self._reader_loop())
            return await self._handshake()
        except Exception as e:
            print(f"LSP Error: {e}")
            return False

    async def _reader_loop(self):
        """Continuously reads messages from the server's stdout."""
        while self.process and self.process.stdout and not self.process.stdout.at_eof():
            try:
                # 1. Read headers
                content_length = 0
                while True:
                    line = await self.process.stdout.readline()
                    if not line:
                        break
                    # Strip to handle both \r\n and \n safely
                    clean_line = line.strip()
                    if not clean_line:
                        break
                    line_str = clean_line.decode("utf-8").lower()
                    if line_str.startswith("content-length:"):
                        content_length = int(line_str.split(":")[1].strip())

                if content_length == 0:
                    continue

                # 2. Read body
                body = await self.process.stdout.readexactly(content_length)
                msg = json.loads(body.decode("utf-8"))
                self._handle_message(msg)
            except asyncio.IncompleteReadError:
                break
            except Exception as e:
                print(f"LSP Reader Error: {e}")
                break

    def _handle_message(self, msg: Dict[str, Any]):
        """Dispatches incoming messages to pending requests or notification handlers."""
        if "id" in msg:
            # It's a response to a request
            req_id = msg["id"]
            if req_id in self._pending_requests:
                future = self._pending_requests.pop(req_id)
                if not future.done():
                    future.set_result(msg)
        elif "method" in msg:
            # It's a notification
            method = msg["method"]
            if method == "textDocument/publishDiagnostics":
                params = msg.get("params", {})
                uri = params.get("uri")
                self._diagnostics[uri] = params.get("diagnostics", [])

    async def send_request(self, method: str, params: Dict[str, Any]) -> Any:
        """Sends a request and waits for the response."""
        req_id = self._request_id
        self._request_id += 1
        
        future = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = future
        
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }
        await self._send_payload(payload)
        return await future

    async def send_notification(self, method: str, params: Dict[str, Any]):
        """Sends a one-way notification."""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        await self._send_payload(payload)

    async def _send_payload(self, payload: Dict[str, Any]):
        if not self.process or not self.process.stdin:
            return
        body = json.dumps(payload).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
        self.process.stdin.write(header + body)
        await self.process.stdin.drain()

    async def _handshake(self) -> bool:
        """LSP Handshake sequence."""
        init_params = {
            "processId": os.getpid(),
            "rootUri": f"file:///{self.workspace_path.replace(os.sep, '/')}",
            "capabilities": {
                "textDocument": {
                    "publishDiagnostics": {}
                }
            }
        }
        response = await self.send_request("initialize", init_params)
        if "result" not in response:
            return False
            
        await self.send_notification("initialized", {})
        self._initialized = True
        return True

    async def check_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Updates the server version of the file and returns current diagnostics."""
        abs_path = os.path.abspath(file_path).replace(os.sep, '/')
        uri = f"file:///{abs_path}"
        
        # Clear old diagnostics for this specific check session
        self._diagnostics[uri] = []

        await self.send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": "python",
                "version": 1,
                "text": content
            }
        })
        
        # Give Ruff a moment to push diagnostics
        await asyncio.sleep(0.5)
        return self._diagnostics.get(uri, [])

    async def stop(self):
        if self._reader_task:
            self._reader_task.cancel()
        if self.process:
            self.process.terminate()
            await self.process.wait()
