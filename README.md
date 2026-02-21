## PanchoBot Lite — Python Local Agent Runtime (OpenClaw-style)

PanchoBot Lite is a lightweight, OpenClaw-style local runtime written in Python. The model provides planning intelligence while the runtime remains the control plane for tool execution and policy enforcement.

## What this is

- **Planner (AI):** proposes a plan and candidate tool calls.
- **Executor (control plane):** validates tool names and schemas, enforces policy constraints, generates previews, and gates privileged execution behind explicit approval.
- **Local-first:** FastAPI + SQLite + static web UI, no cloud requirement.


## OpenAI API key via Linux secure storage (recommended)

PanchoBot Lite supports reading your OpenAI API key from the Linux system keyring (Secret Service/libsecret via `keyring`) so you do not need to keep the key in shell history or plaintext dotfiles.

Store the key:

```bash
python -m keyring set panchobot openai
```

Then start the server normally. At runtime the key is resolved in this order:

1. `OPENAI_API_KEY` environment variable (explicit override)
2. Linux keyring entry: service `panchobot`, username `openai`

You can customize keyring lookup with:

- `OPENAI_KEYRING_SERVICE`
- `OPENAI_KEYRING_USERNAME`

If no key is found, PanchoBot Lite falls back to the local `FakeAIClient`.

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

## Run with Podman

```bash
cd podman
podman compose up --build
```

## Run tests

```bash
pytest -q
```

## Demo script (2–3 minutes)

1. `podman compose up`
2. Open `http://127.0.0.1:8787`
3. Goal: `Create a README in workspace describing this project`
4. Click **Plan** and inspect proposed preview.
5. Click **Approve**, verify status becomes `APPROVED` and TTL countdown appears.
6. Click **Execute**, verify file is written and status is `EXECUTED`.
7. Try **Execute** again, verify failure (single use).
8. Open action details and inspect audit log entries.
