class RelayPublisher:
    async def publish_event(self, event: dict, relays: list[str]) -> list[dict]:
        # Network-less default implementation; replace with websocket publisher in production.
        return [{"relay_url": relay, "success": False, "error_message": "websocket publisher not installed"} for relay in relays]
