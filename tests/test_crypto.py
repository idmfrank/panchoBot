from server.crypto import action_hash


def test_canonical_hash_deterministic():
    p1 = {"b": 2, "a": 1}
    p2 = {"a": 1, "b": 2}
    assert action_hash(p1) == action_hash(p2)
