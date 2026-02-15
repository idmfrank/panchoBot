# PanchoBot MVP 0

PanchoBot is a **local-only FastAPI service** that publishes **Nostr kind 1 notes** using a strict human-controlled workflow:

`PROPOSED -> APPROVED -> EXECUTED`

It includes:
- AI-assisted drafting (`POST /ai/draft`) with strict draft-only guardrails
- Canonical JSON hashing (SHA-256)
- TTL enforcement at proposal and approval stages
- NIP-07/Nostr Schnorr signature verification for approval and note events
- Relay allowlist enforcement
- Audit log trail for transitions

## Security model

### Allowed capability
- Publish Nostr **kind 1** text notes only.

### Explicitly disallowed
- Autonomous execution
- Non-note actions (DMs, deletes, follows, reactions)
- Key custody
- Cloud-first behavior

### Workflow guarantees
1. **Propose** creates immutable payload + hash and `PROPOSED` state.
2. **Approve** requires signed approval event (`kind 27235`) binding `{action_id, action_hash}` and signed note event matching the proposed payload.
3. **Execute** publishes only approved note event to allowlisted relays.

State transitions are strict and terminal (`EXECUTED` / `EXPIRED`).

## API

### `POST /ai/draft`
Generate a draft only. This endpoint cannot execute actions.

Request:
```json
{"prompt": "write a short update about shipping MVP 0"}
```

Response:
```json
{
  "draft": "...",
  "guardrails": {
    "can_execute_actions": false,
    "scope": "draft-only"
  }
}
```

### `POST /actions/propose`
Create a proposed publish action.

### `POST /actions/approve`
Approve a proposed action with Nostr-signed approval + note event.

### `POST /actions/execute`
Publish an approved action once.

### `GET /actions/{action_id}/audit`
Return audit entries for the action.

## Local run (Ubuntu / venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server.main:app --host 127.0.0.1 --port 8787
```

Open `http://127.0.0.1:8787`.

## Docker

```bash
cd docker
docker compose up --build
```

Service is available on `http://127.0.0.1:8787` from the host.

## Configuration

- `RELAYS_ALLOWLIST` (comma-separated relay URLs)
- `PROPOSE_TTL_SECONDS` (default `300`)
- `APPROVAL_TTL_SECONDS` (default `120`)
- `MAX_CONTENT_LEN` (default `1000`)
- `BIND_HOST` (default `127.0.0.1`)
- `PORT` (default `8787`)
- `DB_PATH` (default `./data/pancho.db`)

## Tests

```bash
pytest -q
```

Test suite includes:
- canonical hash and Schnorr verification tests
- strict state machine tests
- AI draft tests with deterministic fake AI client
- integration flow with mocked relay publisher

