# agents.py – v5.3 (with more specific exception classification + noise handling improvements)

import os, re, textwrap, json, requests
from collections import namedtuple
from .runner import Agent
from .llm import call_llm
from . import rag

# ─────────── helpers ────────────
RULES = rag.query("business rules", 1) or "(no rules)"
JUNK  = ("<|", "###", "=== ", "Answer:", "Example", "- response:")

def _clean(txt: str) -> str:
    return "\n".join(l for l in txt.splitlines()
                     if not any(l.strip().startswith(j) for j in JUNK)).strip()

def _bullets(t: str, n=3) -> str:
    bl = [l for l in t.splitlines() if l.lstrip().startswith("-")]
    return "\n".join(bl[:n])

def _safe_json(raw: str) -> dict:
    """extract first {...} block even if the model wraps it in text/markdown"""
    m = re.search(r"\{.*\}", raw, flags=re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}

# ─────────── 1 Monitor ───────────
MonitorAgent = Agent("Monitor", lambda log: log)

# ─────────── 2 Extractor ──────────
TB = namedtuple("TB", "score depth recency signal text")

_SIG = re.compile(r"(NoneType|KeyError|TypeError|ValueError|IntegrityError|ProgrammingError)", re.I)

def _split_tbs(log: str):
    # split on blank line separating tracebacks
    return re.split(r"\n\s*\n(?=\s*Traceback)", log)

def _score(tb: str, idx: int, total: int) -> TB:
    depth   = tb.count("Traceback")
    recency = total - idx
    signal  = 1 if _SIG.search(tb) else 0
    score   = depth*1.4 + recency*1.1 + signal*2
    return TB(score, depth, recency, signal, tb)

def _extract(log: str) -> dict:
    blocks = _split_tbs(log)
    scored = [_score(b, i, len(blocks)) for i, b in enumerate(blocks)]
    primary = max(scored, key=lambda t: t.score)
    kind = (_SIG.search(primary.text) or re.search(r":\s*([A-Za-z]+Error)", primary.text) or ["Error"])[0]

    # Classify secondary causes
    secondary = [tb for tb in scored if tb != primary]
    secondary_kinds = [(_SIG.search(tb.text) or re.search(r":\s*([A-Za-z]+Error)", tb.text) or ["Error"])[0] for tb in secondary]

    return {"trace": primary.text.strip(), "kind": kind, "secondary": secondary_kinds}

ExtractorAgent = Agent("Extractor", _extract)

# ─────────── 3 Memory ────────────
MemoryAgent = Agent("Memory", lambda q: rag.query(q, 2))

# ─────────── 4 Generator ─────────
def _gen(issue, ctx, tb, strict, temp):
    prompt = json.dumps([{
        "role":"system",
        "content":(
            "You are an incident summariser. "
            "Return *only* valid JSON matching "
            '{"title":str,"diagnosis":str,"remediation":[str],"snippet":str}. '
            f"{'STRICT FORMAT.' if strict else ''}")},
        {"role":"user",
         "content":f"Primary Traceback:\n{tb}\n\nLogs:\n{issue}\n\nSimilar:\n{ctx}\n\nRules:\n{RULES}"}])
    raw = call_llm(prompt, temp=temp)
    return _safe_json(raw)

GeneratorAgent = Agent("Generator", _gen)

# ─────────── 5 Critic ────────────
def _critic(obj, temp):
    if not obj:
        return {}
    ask = (
        "Fix this JSON if keys missing, title >7 words, "
        "or remediation count not 2-3. Else reply pass.\n"
        f"{json.dumps(obj)}")
    ans = call_llm(ask, temp=temp, max_tokens=120)
    return obj if ans.strip().lower().startswith("pass") else _safe_json(ans)

CriticAgent = Agent("Critic", _critic)

# ─────────── 6 Markdown wrap ─────
WRAP = textwrap.dedent("""\
# {title}

**Diagnosis**  
{diagnosis}

**Remediation**
{rem}

```text
{snippet}
```""")
MarkdownAgent = Agent("Markdown", lambda o: WRAP.format(
    title=o["title"],
    diagnosis=o["diagnosis"].strip(),
    rem="\n".join("- "+b.lstrip("-").strip() for b in o["remediation"]),
    snippet=o["snippet"].strip()))

# ─────────── 7 Patch ─────────────
PatchAgent = Agent("Patch", lambda md: (
    md if "- " in md else md + "\n- Add remediation step"))

# ─────────── 8 Push ──────────────
_WEB = os.getenv("SLACK_WEBHOOK", "")
PushAgent = Agent("Push", lambda md: requests.post(
    _WEB, json={"text": md.splitlines()[0]}, timeout=5).status_code
if _WEB.startswith("http") else "noop")
