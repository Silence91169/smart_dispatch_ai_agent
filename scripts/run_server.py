#!/usr/bin/env python
"""Start the Smart Dispatch FastAPI server with uvicorn."""

import sys
from pathlib import Path

# Ensure src/ and project root are on the path.
# Root is needed so `evaluation/` (Phase 8 eval module) is importable.
_root = Path(__file__).parents[1]
_src = _root / "src"
for _p in (_src, _root):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "smart_dispatch.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(_src)],
        log_level="info",
    )
