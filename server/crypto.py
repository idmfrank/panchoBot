import hashlib
import json
from typing import Any

from coincurve import PrivateKey, PublicKeyXOnly


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def action_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def nostr_event_id(event: dict[str, Any]) -> str:
    body = [
        0,
        event["pubkey"],
        event["created_at"],
        event["kind"],
        event.get("tags", []),
        event.get("content", ""),
    ]
    encoded = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sign_event_for_testing(secret_key_hex: str, event: dict[str, Any]) -> dict[str, Any]:
    private_key = PrivateKey(bytes.fromhex(secret_key_hex))
    pubkey = private_key.public_key_xonly.format().hex()
    signed_event = {**event, "pubkey": event.get("pubkey", pubkey)}
    event_id = nostr_event_id(signed_event)
    sig = private_key.sign_schnorr(bytes.fromhex(event_id), None)
    return {**signed_event, "id": event_id, "sig": sig.hex()}


def verify_nostr_event_signature(event: dict[str, Any]) -> bool:
    try:
        event_id = nostr_event_id(event)
        if event.get("id") != event_id:
            return False
        pubkey = bytes.fromhex(event["pubkey"])
        sig = bytes.fromhex(event["sig"])
        return PublicKeyXOnly(pubkey).verify(sig, bytes.fromhex(event_id))
    except Exception:
        return False
