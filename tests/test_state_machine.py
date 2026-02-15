import time

import pytest

from server.actions import ActionError


def test_expired_proposed_cannot_be_approved(app_client):
    _, _, svc = app_client
    action = svc.create_proposed_action("workspace.write_file", {"path": "a.txt", "content": "x"}, "s")
    svc.storage.update_action(action["action_id"], expires_at=int(time.time()) - 1)
    with pytest.raises(ActionError):
        svc.approve(action["action_id"])


def test_expired_approved_cannot_execute(app_client):
    _, _, svc = app_client
    action = svc.create_proposed_action("workspace.write_file", {"path": "a.txt", "content": "x"}, "s")
    svc.approve(action["action_id"])
    approval = svc.storage.get_latest_approval(action["action_id"])
    svc.storage.update_action(action["action_id"], status="APPROVED")
    with svc.storage.conn() as conn:
        conn.execute("UPDATE approvals SET expires_at=? WHERE id=?", (int(time.time()) - 1, approval["id"]))
    with pytest.raises(ActionError):
        svc.execute(action["action_id"])


def test_approval_hash_mismatch_fails(app_client):
    _, _, svc = app_client
    action = svc.create_proposed_action("workspace.write_file", {"path": "a.txt", "content": "x"}, "s")
    svc.approve(action["action_id"])
    approval = svc.storage.get_latest_approval(action["action_id"])
    with svc.storage.conn() as conn:
        conn.execute("UPDATE approvals SET action_hash='bad' WHERE id=?", (approval["id"],))
    with pytest.raises(ActionError):
        svc.execute(action["action_id"])
