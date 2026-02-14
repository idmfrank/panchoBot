import hashlib
import json
from typing import Any


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def action_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def nostr_event_id(event: dict[str, Any]) -> str:
    body = [0, event["pubkey"], event["created_at"], event["kind"], event.get("tags", []), event.get("content", "")]
    return hashlib.sha256(json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def sign_event_for_testing(secret: str, event: dict[str, Any]) -> dict[str, Any]:
    ev_id = nostr_event_id(event)
    sig = hashlib.sha256(f"{secret}:{ev_id}".encode()).hexdigest()
    return {**event, "id": ev_id, "sig": sig}


def verify_nostr_event_signature(event: dict[str, Any]) -> bool:
    event_id = nostr_event_id(event)
    if event.get("id") != event_id:
        return False
    expected = hashlib.sha256(f"{event['pubkey']}:{event_id}".encode()).hexdigest()
    return event.get("sig") == expected
