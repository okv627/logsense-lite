# Airflow DAG Business Rules

- **Secret Management**: All DAGs must load secrets (e.g., API tokens) from environment variables. Hardcoding is not allowed.

- **Failure Thresholds**: If a task fails more than 2 times in a row, a Slack alert must be triggered immediately.

- **Token Format**: The `fetch_api_data()` function is reused across DAGs. It expects a valid JWT as the API token.

- **Token Expiry**: API tokens expire after 30 days. Tasks must refresh them automatically using the internal `auth` microservice.

- **HTTP 401 Handling**: If an external API returns a `401 Unauthorized`, do not retry. Escalate the failure to the data platform team.
