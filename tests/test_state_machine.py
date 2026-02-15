import time

import pytest

from server.actions import ActionError
from tests.conftest import TEST_SECRET, approval_content, run, sign_event


def approve_action(service):
    pubkey = sign_event(TEST_SECRET, {"kind": 1, "content": "x"})["pubkey"]
    p = service.propose("hello", [], None, pubkey)
    note = sign_event(TEST_SECRET, {"kind": 1, "created_at": p["action_payload"]["created_at"], "tags": [], "content": "hello"})
    approval = sign_event(
        TEST_SECRET,
        {"kind": 27235, "created_at": int(time.time()), "tags": [], "content": approval_content(p["action_id"], p["action_hash"])},
    )
    service.approve(p["action_id"], approval, note)
    return p["action_id"]


def test_execute_without_approval_fails(service):
    pubkey = sign_event(TEST_SECRET, {"kind": 1, "content": "x"})["pubkey"]
    p = service.propose("hello", [], None, pubkey)
    with pytest.raises(ActionError):
        run(service.execute(p["action_id"]))


def test_double_execute_fails(service):
    action_id = approve_action(service)
    run(service.execute(action_id))
    with pytest.raises(ActionError):
        run(service.execute(action_id))


def test_expired_proposal_cannot_be_approved(service):
    service.settings.propose_ttl_seconds = 1
    pubkey = sign_event(TEST_SECRET, {"kind": 1, "content": "x"})["pubkey"]
    p = service.propose("hello", [], None, pubkey)
    time.sleep(2)
    note = sign_event(TEST_SECRET, {"kind": 1, "created_at": p["action_payload"]["created_at"], "tags": [], "content": "hello"})
    approval = sign_event(
        TEST_SECRET,
        {"kind": 27235, "created_at": int(time.time()), "tags": [], "content": approval_content(p["action_id"], p["action_hash"])},
    )
    with pytest.raises(ActionError):
        service.approve(p["action_id"], approval, note)


def test_expired_approval_cannot_execute(service):
    service.settings.approval_ttl_seconds = 1
    action_id = approve_action(service)
    time.sleep(2)
    with pytest.raises(ActionError):
        run(service.execute(action_id))
