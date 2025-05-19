# rag.py
import os, chromadb, json, hashlib
from pathlib import Path
from sentence_transformers import SentenceTransformer

_DB  = os.getenv("LOGSENSE_RAG_DIR", "rag_db")
_EMB = os.getenv("LOGSENSE_EMBED_MODEL", "all-MiniLM-L6-v2")

_cli  = chromadb.PersistentClient(path=_DB)
_coll = _cli.get_or_create_collection("logsense")
_emb  = SentenceTransformer(_EMB)

# one-time ingest of business rules
rules_p = Path("rag_docs/business_rules.md")
if rules_p.is_file() and not _coll.get(ids=["rules"]).get("ids"):
    _coll.add(ids=["rules"], documents=[rules_p.read_text()], metadatas=[{"src":"rules"}])

def _hash(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()

def add(doc: str):
    hid = _hash(doc[:200])
    if _coll.get(ids=[hid]).get("ids"): return
    _coll.add(ids=[hid], documents=[doc], metadatas=[{"src":"log"}])

def query(q: str, k: int = 2) -> str:
    if _coll.count()==0: return ""
    k = min(k, _coll.count())
    res = _coll.query(query_texts=[q], n_results=k)
    return "\n---\n".join(res["documents"][0])
