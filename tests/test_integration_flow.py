def test_full_flow_plan_approve_execute(app_client):
    client, settings, _ = app_client
    resp = client.post("/agent/plan", json={"goal": "Create a README in workspace describing this project"})
    assert resp.status_code == 200
    action = resp.json()["actions"][0]

    approve = client.post("/actions/approve", json={"action_id": action["action_id"]})
    assert approve.status_code == 200
    assert approve.json()["status"] == "APPROVED"

    execute = client.post("/actions/execute", json={"action_id": action["action_id"]})
    assert execute.status_code == 200
    assert execute.json()["action"]["status"] == "EXECUTED"

    again = client.post("/actions/execute", json={"action_id": action["action_id"]})
    assert again.status_code == 400

    detail = client.get(f"/actions/{action['action_id']}")
    assert detail.status_code == 200
    events = [e["event_type"] for e in detail.json()["audit"]]
    assert "ACTION_PROPOSED" in events
    assert "ACTION_APPROVED" in events
    assert "ACTION_EXECUTED" in events

    generated = (settings.workspace_dir + "/README.generated.md")
    with open(generated, "r", encoding="utf-8") as f:
        assert "Create a README" in f.read()
