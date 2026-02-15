def test_agent_plan_returns_structured_plan(app_client):
    client, _, _ = app_client
    response = client.post("/agent/plan", json={"goal": "Create a README in workspace describing this project"})
    assert response.status_code == 200
    body = response.json()
    assert body["plan_summary"]
    assert body["actions"]
    assert body["actions"][0]["tool_name"] == "workspace.write_file"


def test_unknown_tool_rejected(app_client):
    _, _, svc = app_client
    try:
        svc.create_proposed_action("unknown.tool", {}, "session")
        assert False
    except Exception as exc:
        assert "Unknown tool" in str(exc)
