# runner.py  – pretty traces + zero-risk edits
import time
from contextlib import contextmanager
from typing import Callable, Any, Dict

# --------------------------------------------------------------------------- #
# You may freely edit the PHASE_MSG dict to change / add emojis or text.      #
# Do NOT rename the variable or the keys (they must match Agent names).       #
# --------------------------------------------------------------------------- #
PHASE_MSG: Dict[str, str] = {
    "Monitor":     "Scanning log for failure block... (this may take a moment)",
    "Memory":      "Searching context memory... (this may take a moment)",
    "Diagnosis":   "Diagnosing root cause... (this may take a moment)",
    "Remediation": "Suggesting remediation steps... (this may take a moment)",
    "Title":       "Generating incident title...",
    "Snippet":     "Extracting traceback snippet...",
    "Reporter":    "Assembling Markdown report...",
    "Sanitize":    "Cleaning up output...",
    "Critic":      "Self-critiquing JSON...",
    "Patch":       "Auto-patching small issues...",
    "Push":        "Sending to Slack...",
}

class Agent:
    """Callable thin wrapper with pretty tracing."""
    def __init__(self, name: str, fn: Callable[..., Any]):
        self.name = name
        self.fn   = fn

    def __call__(self, *a, **kw):
        with trace(self.name):
            return self.fn(*a, **kw)

@contextmanager
def trace(name: str):
    msg = PHASE_MSG.get(name, f"Running {name}…")
    print(f"→ {msg}", flush=True)
    t0 = time.time()
    yield
    print(f"✓ {name} done ({time.time()-t0:.1f}s)", flush=True)
