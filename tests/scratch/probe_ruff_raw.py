import asyncio
import json
import os
import sys

async def probe():
    print("--- Starting RAW LSP Probe ---")
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "ruff", "server", "--preview",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "processId": os.getpid(),
            "rootUri": "file:///C:/",
            "capabilities": {}
        }
    }
    
    body = json.dumps(init_msg).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    
    print(f"Sending: {header + body}")
    process.stdin.write(header + body)
    await process.stdin.drain()

    print("Waiting for response (RAW bytes)...")
    try:
        # Read exactly some bytes to see the header
        while True:
            char = await asyncio.wait_for(process.stdout.read(1), timeout=5.0)
            if not char:
                print("EOF reached.")
                break
            sys.stdout.write(char.decode('utf-8', errors='replace'))
            sys.stdout.flush()
    except asyncio.TimeoutError:
        print("\n--- Timeout reached. No more data. ---")
    
    process.terminate()
    await process.wait()

if __name__ == "__main__":
    asyncio.run(probe())
