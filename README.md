# LogSense – AI-Powered Airflow Incident Diagnosis

**LogSense** is a lightweight, fully-offline Python tool that scans Airflow logs, pinpoints the root cause of failures, and produces a clear Markdown incident report in seconds—no paid cloud APIs required.

---

## What It Does

| Stage                  | Details                                                                                                                                                                  |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Input**              | Plain `.log` files from failed Airflow DAG runs.                                                                                                                         |
| **Context-Aware Analysis** | Root-cause detection, fix suggestions using embedded business rules (`rag_docs/business_rules.md`), headline + snippet generation, and similarity search against past incidents. |
| **Output**             | `incident_report.md` containing: <br>– 5-word title <br>– 1-sentence diagnosis <br>– 2–3 actionable fix bullets <br>– Traceback snippet <br>– *(Optional)* Slack alert    |

---

## Architecture at a Glance

| File / Module   | Purpose                                                        |
|------------------|----------------------------------------------------------------|
| `main.py`        | Retry ladder & overall orchestration                           |
| `agents.py`      | Modular generator, evaluator, patch, and push agents           |
| `runner.py`      | Lightweight agent shell with live tracing                      |
| `llm.py`         | Local LLM wrapper using `llama-cpp-python`                     |
| `rag.py`         | ChromaDB vector store and sentence-transformer embeddings      |
| `.env`           | Configuration for model path, context size, and Slack webhook  |
| `rag_docs/`      | Markdown rulebooks injected into prompts during diagnosis      |


---

## Setup Instructions

### 1. Clone the Repo

git clone https://github.com/yourname/logsense.git
cd logsense

### 2. Set Up Python Environment

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt

### 3. Download the Model (Mistral-7B Instruct v0.2)

mkdir models
aria2c -x 16 -s 16 \
  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  -d models

Ensure the file is saved exactly as:

models/mistral-7b-instruct-v0.2.Q4_K_M.gguf

### 4. Create .env

LOGSENSE_MODEL=models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
LOGSENSE_CONTEXT=4096
LOGSENSE_THREADS=6
LOGSENSE_MAX_NEW_TOKENS=320
LOGSENSE_TEMPERATURE=0.10

LOGSENSE_RAG_DIR=rag_db
LOGSENSE_EMBED_MODEL=all-MiniLM-L6-v2

# Optional Slack push
# SLACK_WEBHOOK=https://hooks.slack.com/...

## Usage

python -m logsense sample_logs/dagrun_2025-05-12.log
- Creates incident_report.md.
- (If SLACK_WEBHOOK is set) posts the headline to Slack.


## Why LogSense?

| Feature                    | ✓ Description                                              |
|---------------------------|------------------------------------------------------------|
| Offline-capable           | Uses local GGUF models — no cloud calls                    |
| RAG-enhanced              | Injects matched business rules into every prompt           |
| Retry ladder              | Semantic retries with temperature decay                    |
| Markdown → JSON fallback | Guarantees valid output on final attempt                   |
| Patch agent               | Auto-fixes minor format issues                             |
| LLM evaluator             | Checks meaning and structure, not just regex               |
| Fast & Lightweight        | Runs on CPU in seconds                                     |


## Example Output

# API Token Missing or Invalid

**Diagnosis**  
The provided API token was missing or invalid.

**Remediation**
- Load secrets (e.g., API tokens) from environment variables.  
- Refresh tokens automatically via the internal `auth` microservice.  
- Ensure `fetch_api_data()` receives a valid JWT.

Traceback (most recent call last):
  ...
  raise ValueError("API token missing or invalid")
ValueError: API token missing or invalid

---

## Slack Notifications (Optional)

Add your webhook in `.env`:

SLACK_WEBHOOK=https://hooks.slack.com/your/webhook/url

## Custom Business Rules

Edit rag_docs/business_rules.md to guide diagnoses and remediation suggestions.
Changes are picked up automatically at run time.

## Powered By
Mistral-7B Instruct v0.2 (GGUF)
llama-cpp-python
ChromaDB
sentence-transformers

## License
MIT

## Contribute
PRs welcome—especially:
- New domain-specific business rules
- Ports to frameworks (CrewAI, OpenAI Agents SDK, LangGraph, …)

Let’s make Airflow troubleshooting painless—together!