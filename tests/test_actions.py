import time

import pytest

from server.actions import ActionError
from tests.conftest import sign_event


def test_propose_creates_state(service):
    p = service.propose("hello", [], None, "a" * 64)
    assert p["status"] == "PROPOSED"


def test_relay_allowlist_enforced(service):
    with pytest.raises(ActionError):
        service.propose("hello", [], ["wss://evil.example"], "a" * 64)


def test_approve_valid_moves_approved(service):
    pubkey = "b" * 64
    p = service.propose("hello", [], None, pubkey)
    note = sign_event(pubkey, {"kind":1,"created_at":p["action_payload"]["created_at"],"tags":[],"content":"hello"})
    approval = sign_event(pubkey, {"kind":27235,"created_at":int(time.time()),"tags":[],"content":f'{{"action_id":"{p["action_id"]}","action_hash":"{p["action_hash"]}"}}'})
    r = service.approve(p["action_id"], approval, note)
    assert r["status"] == "APPROVED"


def test_approve_wrong_hash_rejected(service):
    pubkey = "b" * 64
    p = service.propose("hello", [], None, pubkey)
    note = sign_event(pubkey, {"kind":1,"created_at":p["action_payload"]["created_at"],"tags":[],"content":"hello"})
    approval = sign_event(pubkey, {"kind":27235,"created_at":int(time.time()),"tags":[],"content":f'{{"action_id":"{p["action_id"]}","action_hash":"bad"}}'})
    with pytest.raises(ActionError):
        service.approve(p["action_id"], approval, note)
