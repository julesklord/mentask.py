## 2024-06-25 - [Optimize recent files reading in _compact_history]
**Learning:** Reading multiple large files synchronously in an async method like `_compact_history` blocks the event loop and wastes memory if only a limited number of characters is needed from each file.
**Action:** Use `asyncio.to_thread` with `asyncio.gather` for concurrent file reads, and cap file reads by using `f.read(2001)` instead of reading entire files into memory when a length limit is imposed downstream.
