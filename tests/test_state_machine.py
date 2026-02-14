import time

import pytest

from server.actions import ActionError
from tests.conftest import run, sign_event


def approve_action(service, pubkey="c" * 64):
    p = service.propose("hello", [], None, pubkey)
    note = sign_event(pubkey, {"kind":1,"created_at":p["action_payload"]["created_at"],"tags":[],"content":"hello"})
    approval = sign_event(pubkey, {"kind":27235,"created_at":int(time.time()),"tags":[],"content":f'{{"action_id":"{p["action_id"]}","action_hash":"{p["action_hash"]}"}}'})
    service.approve(p["action_id"], approval, note)
    return p["action_id"]


def test_execute_without_approval_fails(service):
    p = service.propose("hello", [], None, "c" * 64)
    with pytest.raises(ActionError):
        run(service.execute(p["action_id"]))


def test_double_execute_fails(service):
    action_id = approve_action(service)
    run(service.execute(action_id))
    with pytest.raises(ActionError):
        run(service.execute(action_id))


def test_expired_proposal_cannot_be_approved(service):
    service.settings.propose_ttl_seconds = 1
    p = service.propose("hello", [], None, "c" * 64)
    time.sleep(2)
    note = sign_event("c" * 64, {"kind":1,"created_at":p["action_payload"]["created_at"],"tags":[],"content":"hello"})
    approval = sign_event("c" * 64, {"kind":27235,"created_at":int(time.time()),"tags":[],"content":f'{{"action_id":"{p["action_id"]}","action_hash":"{p["action_hash"]}"}}'})
    with pytest.raises(ActionError):
        service.approve(p["action_id"], approval, note)


def test_expired_approval_cannot_execute(service):
    service.settings.approval_ttl_seconds = 1
    action_id = approve_action(service)
    time.sleep(2)
    with pytest.raises(ActionError):
        run(service.execute(action_id))
