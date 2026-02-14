import asyncio
import time

import pytest

from server.actions import ActionService
from server.config import Settings
from server.crypto import sign_event_for_testing
from server.nostr_pub import RelayPublisher
from server.storage import Storage


class MockPublisher(RelayPublisher):
    async def publish_event(self, event, relays):
        return [{"relay_url": r, "success": True, "response": "ok"} for r in relays]


@pytest.fixture
def service(tmp_path):
    settings = Settings(relays_allowlist=["wss://relay.damus.io", "wss://nos.lol"], db_path=str(tmp_path / "test.db"))
    return ActionService(Storage(settings.db_path), settings, MockPublisher())


def sign_event(pubkey: str, event: dict):
    return sign_event_for_testing(pubkey, {**event, "pubkey": pubkey})


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)
