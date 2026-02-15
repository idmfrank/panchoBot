import asyncio
import json
import time

import pytest
from fastapi.testclient import TestClient

from server.actions import ActionService
from server.ai import AIDraftService
from server.config import Settings
from server.crypto import sign_event_for_testing
from server.main import app
from server.nostr_pub import RelayPublisher
from server.storage import Storage

TEST_SECRET = "1" * 64
ALT_SECRET = "2" * 64


class MockPublisher(RelayPublisher):
    async def publish_event(self, event, relays):
        return [{"relay_url": r, "success": True, "response": "ok"} for r in relays]


class DeterministicAIClient:
    def draft(self, prompt: str) -> str:
        return f"DRAFT::{prompt.strip().upper()}"


@pytest.fixture
def service(tmp_path):
    settings = Settings(relays_allowlist=["wss://relay.damus.io", "wss://nos.lol"], db_path=str(tmp_path / "test.db"))
    return ActionService(Storage(settings.db_path), settings, MockPublisher())


@pytest.fixture
def client(tmp_path):
    from server import main

    settings = Settings(relays_allowlist=["wss://relay.damus.io", "wss://nos.lol"], db_path=str(tmp_path / "api.db"))
    main.settings = settings
    main.storage = Storage(settings.db_path)
    main.publisher = MockPublisher()
    main.service = ActionService(main.storage, settings, main.publisher)
    main.ai_service = AIDraftService(DeterministicAIClient(), settings.max_content_len)
    return TestClient(app)


def sign_event(secret_hex: str, event: dict):
    base = {"tags": [], "created_at": int(time.time()), **event}
    return sign_event_for_testing(secret_hex, base)


def approval_content(action_id: str, action_hash: str) -> str:
    return json.dumps({"action_id": action_id, "action_hash": action_hash}, separators=(",", ":"))


def run(coro):
    return asyncio.run(coro)
