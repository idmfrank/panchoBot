from server.crypto import action_hash, sign_event_for_testing, verify_nostr_event_signature


def test_canonical_hash_deterministic():
    p1 = {"b": 2, "a": 1}
    p2 = {"a": 1, "b": 2}
    assert action_hash(p1) == action_hash(p2)


def test_nip07_style_signature_verification():
    event = sign_event_for_testing("1" * 64, {"kind": 1, "created_at": 1720000000, "tags": [], "content": "hello"})
    assert verify_nostr_event_signature(event)

    tampered = {**event, "content": "tampered"}
    assert not verify_nostr_event_signature(tampered)
