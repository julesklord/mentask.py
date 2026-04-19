import asyncio
import os
import sys

# Inyectar la raiz del proyecto en el path para resolver 'src' como paquete
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.askgem.agent.core.lsp_client import LSPClient


async def main():
    print("--- Initiating LSP Client Handshake ---", flush=True)
    client = LSPClient(workspace_path=".")

    print("DEBUG: Calling client.start()...", flush=True)
    success = await client.start()
    if not success:
        print("FAILED: Could not start or initialize LSP server.", flush=True)
        return

    print("SUCCESS: LSP Server initialized.", flush=True)

    broken_code = "def hello()\n    print('Missing colon!')"
    print("\nTesting Broken Code (Missing Colon):", flush=True)
    diagnostics = await client.check_file("test_broken.py", broken_code)

    if diagnostics:
        for diag in diagnostics:
            print(
                f"  [!] Found: {diag.get('message')} at line {diag.get('range', {}).get('start', {}).get('line') + 1}",
                flush=True,
            )
    else:
        print("  [?] No diagnostics found (Expected error).", flush=True)

    clean_code = "def hello():\n    print('All good!')"
    print("\nTesting Clean Code:", flush=True)
    diagnostics = await client.check_file("test_clean.py", clean_code)

    if not diagnostics:
        print("  SUCCESS: No errors found in clean code.", flush=True)
    else:
        print(f"  [!] Unexpected diagnostics: {diagnostics}", flush=True)

    await client.stop()
    print("\n--- LSP Session Closed ---", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
