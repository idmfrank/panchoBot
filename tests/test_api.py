import time

from tests.conftest import TEST_SECRET, approval_content, sign_event


def test_ai_draft_uses_fake_deterministic_client(client):
    res = client.post("/ai/draft", json={"prompt": "  ship status update  "})
    assert res.status_code == 200
    body = res.json()
    assert body["draft"] == "DRAFT::SHIP STATUS UPDATE"
    assert body["guardrails"]["can_execute_actions"] is False


def test_http_flow_with_mocked_relay_publisher(client):
    pubkey = sign_event(TEST_SECRET, {"kind": 1, "content": "x"})["pubkey"]

    proposed = client.post("/actions/propose", json={"content": "hello api", "pubkey": pubkey, "tags": []})
    assert proposed.status_code == 200
    p = proposed.json()

    note = sign_event(
        TEST_SECRET,
        {"kind": 1, "created_at": p["action_payload"]["created_at"], "tags": [], "content": "hello api"},
    )
    approval = sign_event(
        TEST_SECRET,
        {
            "kind": 27235,
            "created_at": int(time.time()),
            "tags": [],
            "content": approval_content(p["action_id"], p["action_hash"]),
        },
    )

    approved = client.post(
        "/actions/approve",
        json={"action_id": p["action_id"], "approval_event": approval, "note_event": note},
    )
    assert approved.status_code == 200

    executed = client.post("/actions/execute", json={"action_id": p["action_id"]})
    assert executed.status_code == 200
    relay_results = executed.json()["relay_results"]
    assert all(r["success"] for r in relay_results)
