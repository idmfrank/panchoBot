import time

import pytest

from server.actions import ActionError
from tests.conftest import TEST_SECRET, ALT_SECRET, approval_content, sign_event


def test_propose_creates_state(service):
    p = service.propose("hello", [], None, sign_event(TEST_SECRET, {"kind": 1, "content": "x"})["pubkey"])
    assert p["status"] == "PROPOSED"


def test_relay_allowlist_enforced(service):
    pubkey = sign_event(TEST_SECRET, {"kind": 1, "content": "x"})["pubkey"]
    with pytest.raises(ActionError):
        service.propose("hello", [], ["wss://evil.example"], pubkey)


def test_approve_valid_moves_approved(service):
    pubkey = sign_event(TEST_SECRET, {"kind": 1, "content": "x"})["pubkey"]
    p = service.propose("hello", [], None, pubkey)
    note = sign_event(TEST_SECRET, {"kind": 1, "created_at": p["action_payload"]["created_at"], "tags": [], "content": "hello"})
    approval = sign_event(
        TEST_SECRET,
        {"kind": 27235, "tags": [], "content": approval_content(p["action_id"], p["action_hash"]), "created_at": int(time.time())},
    )
    r = service.approve(p["action_id"], approval, note)
    assert r["status"] == "APPROVED"


def test_approve_wrong_hash_rejected(service):
    pubkey = sign_event(TEST_SECRET, {"kind": 1, "content": "x"})["pubkey"]
    p = service.propose("hello", [], None, pubkey)
    note = sign_event(TEST_SECRET, {"kind": 1, "created_at": p["action_payload"]["created_at"], "tags": [], "content": "hello"})
    approval = sign_event(
        TEST_SECRET,
        {"kind": 27235, "tags": [], "content": approval_content(p["action_id"], "bad"), "created_at": int(time.time())},
    )
    with pytest.raises(ActionError):
        service.approve(p["action_id"], approval, note)


def test_approval_pubkey_mismatch_rejected(service):
    pubkey = sign_event(TEST_SECRET, {"kind": 1, "content": "x"})["pubkey"]
    p = service.propose("hello", [], None, pubkey)
    note = sign_event(TEST_SECRET, {"kind": 1, "created_at": p["action_payload"]["created_at"], "tags": [], "content": "hello"})
    approval = sign_event(
        ALT_SECRET,
        {"kind": 27235, "tags": [], "content": approval_content(p["action_id"], p["action_hash"]), "created_at": int(time.time())},
    )
    with pytest.raises(ActionError):
        service.approve(p["action_id"], approval, note)
