# llm.py

import os, re
from llama_cpp import Llama
from dotenv import load_dotenv
load_dotenv()

_MODEL_FILE = os.getenv("LOGSENSE_MODEL_FILE", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
_MODEL_PATH = os.path.join(os.getenv("LOGSENSE_MODEL", "models"), _MODEL_FILE)
_CTX        = int(os.getenv("LOGSENSE_CONTEXT", 4096))
_THREADS    = int(os.getenv("LOGSENSE_THREADS", 6))
_MAXTOK     = int(os.getenv("LOGSENSE_MAX_NEW_TOKENS", 320))
_TEMP       = float(os.getenv("LOGSENSE_TEMPERATURE", 0.1))

_llm = None

def _strip(t: str) -> str:
    t = t.strip().lstrip("\"'").strip()
    t = re.sub(r'^(Answer|Solution|Example solution|Response|Explanation)[:\-]\s*', '', t, flags=re.I)
    return t

def call_llm(prompt: str, *, max_tokens=_MAXTOK, temp=_TEMP) -> str:
    global _llm
    if _llm is None:
        _llm = Llama(
            model_path=_MODEL_PATH,
            n_ctx=_CTX,
            n_threads=_THREADS,
            verbose=False
        )
    out = _llm(prompt, max_tokens=max_tokens, temperature=temp,
               stop=["<|end|>", "<|user|>", "<|assistant|>"])
    return _strip(out["choices"][0]["text"])
