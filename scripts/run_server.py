#!/usr/bin/env python
"""Start the Smart Dispatch FastAPI server with uvicorn."""

import sys
from pathlib import Path

# Ensure src/ is on the path when running the script directly (editable installs
# should already handle this, but this guards against broken .pth files).
_src = Path(__file__).parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

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
