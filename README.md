# PanchoBot MVP 0

PanchoBot is a local-first FastAPI service for controlled Nostr publication (`kind:1`) with explicit human approval, TTL windows, and single-use execution.

## Threat model summary
- Payload tampering between preview and publish
- Replay of approvals
- Unauthorized execution
- Relay egress abuse
- Expired approval reuse

## Security guarantees
- Deterministic state machine: `PROPOSED -> APPROVED -> EXECUTED`
- SHA-256 canonical payload hash binding
- Approval must include `action_id` + `action_hash`
- Approval and note signatures verified server-side (Schnorr)
- Single-use execution lock (`EXECUTED` terminal)
- TTL checks at approval and execution
- Relay allowlist enforced
- Audit logging for all transitions
- Binds locally by default (`127.0.0.1`)

## What it does **not** do
- No DMs/reactions/follows/deletes
- No key storage/custody
- No autonomous execution
- No cloud deployment

## Local run (venv)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server.main:app --host 127.0.0.1 --port 8787
```
Open `http://127.0.0.1:8787`.

## Local run (Docker)
```bash
cd docker
docker compose up --build
```

## Run tests
```bash
pytest -q
```

## Example curl commands
```bash
curl -sX POST http://127.0.0.1:8787/actions/propose \
  -H 'content-type: application/json' \
  -d '{"content":"hello from curl","pubkey":"<64-hex-pubkey>","tags":[]}'

curl -sX POST http://127.0.0.1:8787/actions/approve \
  -H 'content-type: application/json' \
  -d '{"action_id":"<id>","approval_event":{...},"note_event":{...}}'

curl -sX POST http://127.0.0.1:8787/actions/execute \
  -H 'content-type: application/json' \
  -d '{"action_id":"<id>"}'
```

## Demo walkthrough
1. Start stack (`docker compose up`).
2. Open `http://127.0.0.1:8787`.
3. Enter `pubkey` and content, click **Propose**.
4. Review preview + hash + expiry.
5. Click **Approve** (NIP-07 prompt).
6. Click **Execute**.
7. Try **Execute** again (fails by design).
8. Check `GET /actions/{action_id}/audit`.

## Configuration
- `RELAYS_ALLOWLIST` (comma-separated)
- `PROPOSE_TTL_SECONDS` (default `300`)
- `APPROVAL_TTL_SECONDS` (default `120`)
- `MAX_CONTENT_LEN` (default `1000`)
- `BIND_HOST` (default `127.0.0.1`)
- `PORT` (default `8787`)
- `DB_PATH` (default `./data/pancho.db`)
