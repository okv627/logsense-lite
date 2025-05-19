# main.py – v5.2 with improved retry logic and refined traceback processing
import sys, uuid, time, os
from pathlib import Path
from dotenv import load_dotenv; load_dotenv()
from .agents import *
from . import rag

MAX_RETRY = 4
BASE_T    = 0.16
def _t(i): return round(max(BASE_T*(0.5**i), 0.04), 3)

def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python -m logsense <logfile>")

    raw   = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
    issue = MonitorAgent(raw)
    ctx   = MemoryAgent(issue)
    tb_obj = ExtractorAgent(issue)
    tb     = tb_obj.get("trace", issue)

    obj = {}
    for i in range(MAX_RETRY):
        strict = (i >= 2)
        temp   = _t(i)
        os.environ["LOGSENSE_TEMPERATURE"] = str(temp)

        draft  = GeneratorAgent(issue, ctx, tb, strict, temp)
        obj    = CriticAgent(draft, temp)

        good = obj and all(k in obj for k in ("title", "diagnosis", "remediation", "snippet")) \
              and 1 < len(obj["remediation"]) <= 3
        if good:
            break
        print(f"retry {i+1}/{MAX_RETRY} temp={temp}")
        time.sleep(0.25)

    if not obj:   # final fallback
        obj = dict(
            title="Unparsed Airflow Error",
            diagnosis=tb.splitlines()[-1][:120],
            remediation=["Inspect DAG code", "Check upstream tasks"],
            snippet=tb[:400])

    md = PatchAgent(MarkdownAgent(obj))
    rag.add(md)
    PushAgent(md)
    Path("incident_report.md").write_text(md, encoding="utf-8")
    print("incident_report.md generated ✔")

if __name__ == "__main__":
    main()
