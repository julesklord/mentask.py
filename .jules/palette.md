## 2025-04-05 - [Add Busy State to Input in TUI]
**Learning:** In TUI applications using Textual, interactive widgets like `Input` should be explicitly disabled during asynchronous operations (like streaming an AI response). This provides immediate visual feedback of the "busy" state and prevents users from accidentally submitting concurrent inputs, which reduces cognitive load and prevents race conditions.
**Action:** Always disable inputs during async agent turns, and remember to re-enable and explicitly refocus them in a `finally` block to restore usability once the process completes.

## 2025-05-18 - [Add Busy State during Application Initialization]
**Learning:** Application startup sequences in Textual applications can lead to race conditions if the inputs are not explicitly disabled before they have fully loaded. Since `init_api` performs network calls and loads chat history asynchronously, it can result in inputs being processed before initialization completes.
**Action:** Always explicitly disable interactive inputs at the beginning of asynchronous initialization sequences and remember to re-enable and explicitly refocus them inside a `finally` block.

## 2025-05-24 - [Preserve Visual Error State During Async Operations]
**Learning:** Automatically resetting visual indicators to an 'idle' state via a timeout in a `finally` block can override critical error states set during the `except` block. This removes visual error feedback before users can fully register the failure, leading to confusion.
**Action:** When reverting visual states (like a mascot's 'thinking' state) after an operation, always conditionally check that the state isn't already set to an 'error' state before resetting to 'idle'.