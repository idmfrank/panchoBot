from server.crypto import action_hash, canonical_json


def test_canonical_json_is_deterministic():
    a = {"b": 1, "a": {"z": 2, "x": 1}}
    b = {"a": {"x": 1, "z": 2}, "b": 1}
    assert canonical_json(a) == canonical_json(b)
    assert action_hash(a) == action_hash(b)
