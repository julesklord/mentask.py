import logging

from ..schema import EngineeringLevel

_logger = logging.getLogger("mentask")

CLASSIFICATION_PROMPT = """
Analyze the following USER REQUEST and classify it into one of four Engineering Levels:

- L0_INQUIRY: Pure questions, requests for information, or general discussion where NO CODE CHANGES or system actions are needed.
- L1_PRAGMATIC: Simple technical tasks, single-file scripts, file lookups, or straightforward commands.
- L2_STANDARD: Feature development, multi-file changes, bug fixes requiring research, or new logic implementation.
- L3_ARCHITECT: Core refactoring, architectural changes, complex migrations, or tasks affecting the entire system.

Respond ONLY with the level key (e.g., L1_PRAGMATIC).

USER REQUEST: {prompt}
"""


class TaskClassifier:
    def __init__(self, provider):
        self.provider = provider

    async def classify(self, prompt: str, config=None) -> EngineeringLevel:
        try:
            # We use a non-streaming turn for a quick classification
            from ..schema import Message, Role

            messages = [Message(role=Role.USER, content=CLASSIFICATION_PROMPT.format(prompt=prompt))]

            # Use a copy of config to limit output tokens for speed
            import copy

            fast_config = copy.copy(config) if config else {}
            if isinstance(fast_config, dict):
                fast_config["max_output_tokens"] = 10
            elif hasattr(fast_config, "max_output_tokens"):
                fast_config.max_output_tokens = 10

            raw_response = ""
            async for event in self.provider.stream_turn(messages, [], config=fast_config):
                if event["type"] == "text":
                    raw_response += event["content"]

            raw_response = raw_response.strip().upper()

            if "L3" in raw_response:
                return EngineeringLevel.L3_ARCHITECT
            elif "L2" in raw_response:
                return EngineeringLevel.L2_STANDARD
            elif "L1" in raw_response:
                return EngineeringLevel.L1_PRAGMATIC
            elif "L0" in raw_response:
                return EngineeringLevel.L0_INQUIRY

            _logger.warning(f"Unexpected classification response: {raw_response}. Defaulting to L2.")
            return EngineeringLevel.L2_STANDARD

        except Exception as e:
            _logger.error(f"Task classification failed: {e}")
            return EngineeringLevel.L2_STANDARD
