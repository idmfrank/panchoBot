import time

from tests.conftest import TEST_SECRET, approval_content, run, sign_event


def test_full_flow_and_audit(service):
    pubkey = sign_event(TEST_SECRET, {"kind": 1, "content": "x"})["pubkey"]
    p = service.propose("integration", [], None, pubkey)
    note = sign_event(TEST_SECRET, {"kind": 1, "created_at": p["action_payload"]["created_at"], "tags": [], "content": "integration"})
    approval = sign_event(
        TEST_SECRET,
        {"kind": 27235, "created_at": int(time.time()), "tags": [], "content": approval_content(p["action_id"], p["action_hash"])},
    )
    service.approve(p["action_id"], approval, note)
    res = run(service.execute(p["action_id"]))
    assert res["status"] == "EXECUTED"
    audit = service.storage.list_audit(p["action_id"])
    assert [x["event_type"] for x in audit] == ["ACTION_PROPOSED", "ACTION_APPROVED", "ACTION_EXECUTED"]
