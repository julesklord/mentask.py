"""
General persistent memory manager for mentask.

Handles reading and writing to memory.md, which stores long-term facts,
user preferences, and project-specific context.
"""

import os
from typing import Any

from .paths import (
    get_config_dir,
    get_local_knowledge_path,
    get_memory_path,
)

DEFAULT_MEMORY_TEMPLATE = """# mentask Persistent Memory
# Last Updated: {date}

## User Profile & Preferences
- Preferred Language: Spanish (Default)

## Lessons Learned & Facts
-

## Rules & Constraints
-
"""

DEFAULT_LOCAL_TEMPLATE = """# Project Knowledge: {project}
# Last Updated: {date}

## Project Patterns
-

## Fixed Errors
-

## Tech Stack
-
"""


class MemoryManager:
    """Manages both global (~/.mentask/memory.md) and project-local memory.

    Local memory is stored in .mentask/memory.md if the directory is initialized,
    otherwise it falls back to .mentask_knowledge.md in the project root.
    """

    def __init__(self, config=None):
        self.config = config
        self.path_global = get_memory_path()
        self.path_local = get_local_knowledge_path()
        self.memory_dir = os.path.join(get_config_dir(), "memories")
        os.makedirs(self.memory_dir, exist_ok=True)

        self._ensure_memory_exists(self.path_global, DEFAULT_MEMORY_TEMPLATE)

    def _ensure_memory_exists(self, path: str, template: str):
        """Creates a memory file with a template if it doesn't exist."""
        if not os.path.exists(path):
            from datetime import datetime

            project_name = os.path.basename(os.getcwd())
            content = template.format(date=datetime.now().strftime("%Y-%m-%d"), project=project_name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

    def scan_memories(self) -> list[dict]:
        """Scans the memories directory for additional context files."""
        memories = []
        for file in os.listdir(self.memory_dir):
            if file.endswith(".md"):
                path = os.path.join(self.memory_dir, file)
                # Quick read for description (first few lines)
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read(1000)
                    desc = ""
                    # Simple heuristic for description: first line after title or first paragraph
                    lines = content.splitlines()
                    if len(lines) > 2:
                        desc = lines[2] if lines[0].startswith("#") else lines[0]

                    memories.append(
                        {"filename": file, "path": path, "description": desc[:200], "mtime": os.path.getmtime(path)}
                    )
                except Exception:
                    continue
        return sorted(memories, key=lambda x: x["mtime"], reverse=True)

    async def find_relevant_memories(self, query: str, orchestrator: Any) -> str:
        """Uses a side-query to select the most relevant memories for the current task."""
        memories = self.scan_memories()
        if not memories:
            return ""

        manifest = "\n".join([f"- {m['filename']}: {m['description']}" for m in memories[:50]])

        selection_prompt = (
            "You are a memory retrieval system. Given the USER QUERY and the AVAILABLE MEMORIES, "
            "select up to 3 filenames that are MOST relevant to answering the query.\n"
            f"AVAILABLE MEMORIES:\n{manifest}\n\n"
            f"USER QUERY: {query}\n\n"
            "Respond ONLY with a comma-separated list of filenames, or 'NONE' if no relevant memories found."
        )

        try:
            # We use the provided orchestrator to run a non-history side-query
            selected_raw = ""
            async for event in orchestrator.provider.stream_turn(
                [{"role": "user", "content": selection_prompt}], [], config={"temperature": 0.1}
            ):
                if event["type"] == "text":
                    selected_raw += event["content"]

            if "NONE" in selected_raw.upper():
                return ""

            selected_files = [
                f.strip() for f in selected_raw.split(",") if f.strip() in [m["filename"] for m in memories]
            ]

            relevant_content = "\n--- RELEVANT CONTEXT FROM MEMORY ---\n"
            for filename in selected_files:
                path = os.path.join(self.memory_dir, filename)
                with open(path, encoding="utf-8") as f:
                    relevant_content += f"\nFile: {filename}\n{f.read()}\n"

            return relevant_content
        except Exception:
            return ""

    def read_memory(self, scope: str = "all") -> str:
        """Reads memory content.

        Args:
            scope: 'global', 'local', or 'all' (merged).
        """
        global_content = ""
        local_content = ""

        if scope in ("global", "all") and os.path.exists(self.path_global):
            with open(self.path_global, encoding="utf-8") as f:
                global_content = f"--- GLOBAL PERSISTENT MEMORY ---\n{f.read()}\n"

        if scope in ("local", "all") and os.path.exists(self.path_local):
            with open(self.path_local, encoding="utf-8") as f:
                local_content = f"--- LOCAL PROJECT KNOWLEDGE ---\n{f.read()}\n"

        if scope == "all":
            return f"{global_content}\n{local_content}"
        return global_content if scope == "global" else local_content

    def add_fact(self, fact: str, category: str = "Lessons Learned & Facts", scope: str = "local") -> bool:
        """Appends a new fact to a specific category in global or local memory.

        Args:
            fact: The fact to remember.
            category: The markdown section.
            scope: 'global' or 'local'.
        """
        path = self.path_local if scope == "local" else self.path_global
        template = DEFAULT_LOCAL_TEMPLATE if scope == "local" else DEFAULT_MEMORY_TEMPLATE

        # Ensure it exists before adding
        self._ensure_memory_exists(path, template)

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()

            lines = content.splitlines()
            target_index = -1
            for i, line in enumerate(lines):
                if line.strip().lower() == f"## {category}".lower():
                    target_index = i
                    break

            if target_index != -1:
                lines.insert(target_index + 1, f"- {fact}")
            else:
                lines.append(f"\n## {category}")
                lines.append(f"- {fact}")

            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True
        except Exception:
            return False

    def reset_memory(self, scope: str = "global"):
        """Wipes specific memory file."""
        path = self.path_local if scope == "local" else self.path_global
        if os.path.exists(path):
            os.remove(path)
        # Re-ensure if global
        if scope == "global":
            self._ensure_memory_exists(self.path_global, DEFAULT_MEMORY_TEMPLATE)
