import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from google.genai import types

# Where config lives — mirrors ConfigManager's approach without circular imports
def _get_history_dir() -> str:
    history_dir = os.path.join(os.path.expanduser("~"), ".pygemai", "history")
    os.makedirs(history_dir, exist_ok=True)
    return history_dir

# Maximum number of messages to inject back into context when loading a session.
# Older messages are archived on disk but excluded from the API call to save tokens.
MAX_CONTEXT_WINDOW = 20


class HistoryManager:
    """
    Handles persistent storage and retrieval of chat sessions.
    Applies a rolling context window to cap token usage on session reload.
    """

    def __init__(self, console):
        self.console = console
        self.history_dir = _get_history_dir()
        # Each run gets a unique timestamped session ID
        self.current_session_id = (
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            + f"_{uuid.uuid4().hex[:6]}"
        )

    # ------------------------------------------------------------------ #
    # Serialization helpers (google-genai v0.2.0 Content <-> JSON)        #
    # ------------------------------------------------------------------ #

    def _content_to_dict(self, content: types.Content) -> Dict[str, Any]:
        """Converts a SDK Content object into a JSON-serializable dictionary."""
        parts_list = []
        for part in content.parts:
            if part.text:
                parts_list.append({"text": part.text})
            elif part.function_call:
                parts_list.append({
                    "function_call": {
                        "name": part.function_call.name,
                        "args": dict(part.function_call.args or {}),
                    }
                })
            elif part.function_response:
                parts_list.append({
                    "function_response": {
                        "name": part.function_response.name,
                        "response": dict(part.function_response.response or {}),
                    }
                })
        return {"role": content.role, "parts": parts_list}

    def _dict_to_content(self, data: Dict[str, Any]) -> Optional[types.Content]:
        """Rebuilds a SDK Content object from a stored dictionary. Returns None on failure."""
        try:
            parts = []
            for p in data.get("parts", []):
                if "text" in p:
                    parts.append(types.Part.from_text(text=p["text"]))
                elif "function_call" in p:
                    parts.append(
                        types.Part.from_function_call(
                            name=p["function_call"]["name"],
                            args=p["function_call"]["args"],
                        )
                    )
                elif "function_response" in p:
                    parts.append(
                        types.Part.from_function_response(
                            name=p["function_response"]["name"],
                            response=p["function_response"]["response"],
                        )
                    )
            if not parts:
                return None
            return types.Content(role=data.get("role", "user"), parts=parts)
        except Exception as e:
            self.console.print(f"[dim red]Warning: Could not deserialize a history entry: {e}[/dim red]")
            return None

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def save_session(self, history: List[types.Content]) -> None:
        """
        Serializes the current chat history to disk under the active session ID.
        Safe to call repeatedly — it overwrites the same file each time.
        """
        if not history:
            return

        filepath = os.path.join(self.history_dir, f"{self.current_session_id}.json")
        try:
            serialized = [self._content_to_dict(h) for h in history]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(serialized, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.console.print(f"[dim red]Error saving session history: {e}[/dim red]")

    def load_session(self, session_id: str) -> Optional[List[types.Content]]:
        """
        Loads a previously saved session from disk and applies the rolling
        context window to keep token usage bounded.
        """
        filepath = os.path.join(self.history_dir, f"{session_id}.json")
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Token optimization: only feed the most recent N messages back
            if len(data) > MAX_CONTEXT_WINDOW:
                data = data[-MAX_CONTEXT_WINDOW:]
                # The context must always start with a 'user' turn
                while data and data[0].get("role") != "user":
                    data = data[1:]

            contents = [self._dict_to_content(d) for d in data]
            # Filter out any entries that failed deserialization
            return [c for c in contents if c is not None]

        except Exception as e:
            self.console.print(f"[dim red]Error loading session '{session_id}': {e}[/dim red]")
            return None

    def list_sessions(self) -> List[str]:
        """Returns all saved session IDs sorted chronologically (newest last)."""
        try:
            files = [f for f in os.listdir(self.history_dir) if f.endswith(".json")]
            files.sort()
            return [f.replace(".json", "") for f in files]
        except Exception:
            return []

    def delete_session(self, session_id: str) -> bool:
        """Removes a specific session file from disk."""
        filepath = os.path.join(self.history_dir, f"{session_id}.json")
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception:
            return False
