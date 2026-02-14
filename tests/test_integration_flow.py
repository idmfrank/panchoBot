import time

from tests.conftest import run, sign_event


def test_full_flow_and_audit(service):
    pubkey = "d" * 64
    p = service.propose("integration", [], None, pubkey)
    note = sign_event(pubkey, {"kind":1,"created_at":p["action_payload"]["created_at"],"tags":[],"content":"integration"})
    approval = sign_event(pubkey, {"kind":27235,"created_at":int(time.time()),"tags":[],"content":f'{{"action_id":"{p["action_id"]}","action_hash":"{p["action_hash"]}"}}'})
    service.approve(p["action_id"], approval, note)
    res = run(service.execute(p["action_id"]))
    assert res["status"] == "EXECUTED"
    audit = service.storage.list_audit(p["action_id"])
    assert [x["event_type"] for x in audit] == ["ACTION_PROPOSED", "ACTION_APPROVED", "ACTION_EXECUTED"]
