# agents.py  – v5 iron-clad
import os, re, textwrap, json, requests
from .runner import Agent
from .llm    import call_llm
from . import rag

# ───────── helpers ──────────
RULES = rag.query("business rules", 1) or "(no rules)"
JUNK  = ("<|", "###", "=== ", "Answer:", "Example", "- response:")

def _clean(t: str) -> str:
    return "\n".join(l for l in t.splitlines()
                     if not any(l.strip().startswith(j) for j in JUNK)).strip()

def _bullets(t: str, n=3) -> str:
    bl = [l for l in t.splitlines() if l.strip().startswith("-")]
    return "\n".join(bl[:n])

# 1  Monitor
def _monitor(log:str)->str:
    pat=re.compile(r"ERROR\s*-\s*Task failed",re.I)
    lines=log.splitlines()
    i=next((i for i,l in enumerate(lines) if pat.search(l)),0)
    return "\n".join(lines[max(0,i-4):i+15]) if lines else log[:600]
MonitorAgent=Agent("Monitor",_monitor)

# 2  Memory
MemoryAgent=Agent("Memory",lambda q:rag.query(q,2))

# JSON schema for generator
def _json_prompt(issue, ctx, strict):
    sys = {
      "role":"system",
      "content":(
        "Return **valid JSON** only, following this schema:\n"
        "{title:str, diagnosis:str, remediation:list[str], snippet:str}\n"
        "No markdown, no commentary.\n"
        f"{'STRICT FORMAT' if strict else ''}")
    }
    usr = {
      "role":"user",
      "content":(
        f"Issue Logs:\n{issue}\n\nSimilar:\n{ctx}\n\nRules:\n{RULES}")
    }
    return json.dumps([sys, usr])

# 3  Generator (LLM-Gen)
def _generate(issue, ctx, strict, temp):
    prompt=_json_prompt(issue,ctx,strict)
    raw=call_llm(prompt,temp=temp)
    try:
        obj=json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return obj
GeneratorAgent=Agent("Generator",_generate)

# 4  Critic (LLM-Critic) – validates & fixes minor stuff
def _critic(obj, temp):
    if not obj: return {}
    critique = (
      "You are a QA assistant.\n"
      "Here is a JSON incident report:\n"
      f"{json.dumps(obj,indent=2)}\n"
      "Validate keys present, title ≤7 words, 2-3 bullets, "
      "bullets address diagnosis.\n"
      "Respond ONLY with 'pass' or a fixed JSON object.")
    res=call_llm(critique,temp=temp,max_tokens=120)
    if res.strip().lower().startswith("pass"): return obj
    try: return json.loads(res)
    except: return obj
CriticAgent=Agent("Critic",_critic)

# 5  Markdown wrapper
WRAP=textwrap.dedent("""\
# {title}

**Diagnosis**  
{diagnosis}

**Remediation**
{rem}

```text
{snippet}
```""")
MarkdownAgent=Agent("Markdown",lambda o: WRAP.format(
    title=o['title'],
    diagnosis=o['diagnosis'].strip(),
    rem="\n".join("- "+b.lstrip("-").strip() for b in o['remediation']),
    snippet=o['snippet'].strip() ))

# 6  Patch agent
def _patch(md:str)->str:
    lines=md.splitlines()
    if not lines or not lines[0].startswith("# "):
        lines.insert(0,"# Untitled Incident")
    if "Remediation" in md and "- " not in md:
        lines.append("- Review DAG retry configuration")
    return "\n".join(lines)
PatchAgent=Agent("Patch",_patch)

# 7  Push
_WEB=os.getenv("SLACK_WEBHOOK","")
PushAgent=Agent("Push",lambda md:requests.post(
    _WEB,json={"text":md.splitlines()[0]},timeout=5).status_code
    if _WEB.startswith("http") else "noop")
