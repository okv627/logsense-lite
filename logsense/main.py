# main.py  – v5 iron-clad orchestrator
import sys, uuid, time, os
from pathlib import Path
from dotenv import load_dotenv; load_dotenv()
from .agents import *
from . import rag

MAX_TRIES = 4           # 0..3 normal, 3 = very strict
BASE_T    = 0.18

def _temp(i): return round(max(BASE_T*(0.5**i),0.04),3)

def main():
    if len(sys.argv)<2:
        sys.exit("Usage: python -m logsense <logfile>")

    raw   = Path(sys.argv[1]).read_text(encoding="utf-8",errors="ignore")
    issue = MonitorAgent(raw)
    ctx   = MemoryAgent(issue)

    obj=None
    for i in range(MAX_TRIES):
        strict = (i>=2)
        t=_temp(i)
        os.environ["LOGSENSE_TEMPERATURE"]=str(t)

        draft  = GeneratorAgent(issue,ctx,strict,t)
        obj    = CriticAgent(draft,t)

        # simple structural checks
        if obj and all(k in obj for k in ("title","diagnosis","remediation","snippet")) \
           and 1< len(obj["remediation"])<=3:
            break
        print(f"🔁 retry {i+1}/{MAX_TRIES-1}  temp={t}")
        time.sleep(0.25)

    if not obj:
        # catastrophic fallback
        obj=dict(
            title="Airflow Failure",
            diagnosis=issue.splitlines()[0][:120],
            remediation=["Investigate DAG logs","Fix offending code"],
            snippet=issue[:400]
        )

    md=MarkdownAgent(obj)
    md=PatchAgent(md)

    rag.add(md)
    PushAgent(md)
    Path("incident_report.md").write_text(md,encoding="utf-8")
    print("incident_report.md generated ✔")

if __name__=="__main__":
    main()
