# PanchoBot MVP 0 — Local Agent Runtime (Security First)

PanchoBot is an OpenClaw-like local runtime where the model provides planning intelligence and the runtime controls execution.

## What this is

- **Planner (AI):** proposes a plan and candidate tool calls.
- **Executor (control plane):** validates tool names and schemas, enforces policy constraints, generates previews, and gates privileged execution behind explicit approval.
- **Local-first:** FastAPI + SQLite + static web UI, no cloud requirement.

## Threat model summary

MVP 0 assumes planner output is untrusted and can be malicious or incorrect. The control plane therefore:

- denies unknown tools,
- validates tool args against schemas,
- enforces workspace path allowlists and shell command allowlists,
- requires explicit approval for privileged actions,
- uses time-based, single-use approvals bound to canonical action payload hashes.

## Security guarantees

- **Least privilege + deny-by-default:** only registered tools can run.
- **Approval gating:** privileged tools (`workspace.write_file`, `shell.run_allowlisted`) require approval before execution.
- **TTL + single-use approvals:** approvals expire and can only be consumed once.
- **Canonical hash binding:** approvals must match `action_hash = sha256(canonical_json(payload))`.
- **Auditability:** action transitions and execution are recorded in `audit_log`.

## Tools in MVP 0

### SAFE
- `agent.explain_plan`
- `workspace.read_file` (workspace allowlist + read size limit)

### PRIVILEGED
- `workspace.write_file` (workspace allowlist)
- `shell.run_allowlisted` (`ls`, `pwd`, `cat`, `pytest`; blocks pipes, redirects, env expansion)

## Run locally (venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server.main:app --host 127.0.0.1 --port 8787
```

Open: `http://127.0.0.1:8787`

## Run with Docker

```bash
cd docker
docker compose up --build
```

## Run tests

```bash
pytest -q
```

## Demo script (2–3 minutes)

1. `docker compose up`
2. Open `http://127.0.0.1:8787`
3. Goal: `Create a README in workspace describing this project`
4. Click **Plan** and inspect proposed preview.
5. Click **Approve**, verify status becomes `APPROVED` and TTL countdown appears.
6. Click **Execute**, verify file is written and status is `EXECUTED`.
7. Try **Execute** again, verify failure (single use).
8. Open action details and inspect audit log entries.
