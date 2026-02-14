import json
import time
import uuid
from dataclasses import dataclass

from .config import Settings
from .crypto import action_hash, verify_nostr_event_signature
from .nostr_pub import RelayPublisher
from .storage import Storage

PROPOSED = "PROPOSED"
APPROVED = "APPROVED"
EXECUTED = "EXECUTED"
EXPIRED = "EXPIRED"


class ActionError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass
class ActionService:
    storage: Storage
    settings: Settings
    publisher: RelayPublisher

    def _validate_relays(self, relays: list[str]) -> list[str]:
        for relay in relays:
            if relay not in self.settings.relays_allowlist:
                raise ActionError(400, f"Relay not allowlisted: {relay}")
        return relays

    def propose(self, content: str, tags: list | None, relays: list | None, pubkey: str):
        if not content or len(content) > self.settings.max_content_len:
            raise ActionError(400, "Invalid content length")
        created_at = int(time.time())
        action_id = str(uuid.uuid4())
        relay_list = self._validate_relays(relays or self.settings.relays_allowlist)
        payload = {"type": "nostr.publish", "kind": 1, "content": content, "tags": tags or [], "relays": relay_list, "created_at": created_at, "pubkey": pubkey}
        digest = action_hash(payload)
        expires_at = created_at + self.settings.propose_ttl_seconds
        self.storage.create_action({"action_id": action_id, "status": PROPOSED, "action_hash": digest, "payload": payload, "expires_at": expires_at, "pubkey": pubkey, "created_at": created_at})
        self.storage.add_audit(created_at, "ACTION_PROPOSED", action_id, {"action_hash": digest})
        return {"action_id": action_id, "expires_at": expires_at, "preview": f"Publish kind:1 note to {len(relay_list)} relays", "action_payload": payload, "action_hash": digest, "status": PROPOSED}

    def approve(self, action_id: str, approval_event: dict, note_event: dict):
        now = int(time.time())
        action = self.storage.get_action(action_id)
        if not action:
            raise ActionError(404, "Action not found")
        if action["status"] != PROPOSED:
            raise ActionError(400, "Action must be PROPOSED")
        if now > action["expires_at"]:
            self.storage.update_action(action_id, status=EXPIRED)
            raise ActionError(400, "Proposal expired")
        payload = json.loads(action["payload"])
        expected_hash = action_hash(payload)
        content_obj = json.loads(approval_event.get("content", "{}"))
        if content_obj.get("action_id") != action_id or content_obj.get("action_hash") != expected_hash:
            raise ActionError(400, "Approval does not match action")
        if not verify_nostr_event_signature(approval_event):
            raise ActionError(400, "Invalid approval signature")
        if not verify_nostr_event_signature(note_event):
            raise ActionError(400, "Invalid note signature")
        for k in ["kind", "content", "tags", "created_at", "pubkey"]:
            if note_event.get(k) != payload.get(k):
                raise ActionError(400, f"Note event mismatch on {k}")
        approval_expires_at = now + self.settings.approval_ttl_seconds
        self.storage.update_action(action_id, status=APPROVED, approval_expires_at=approval_expires_at, approved_event=approval_event, note_event=note_event)
        self.storage.add_audit(now, "ACTION_APPROVED", action_id, {"approval_expires_at": approval_expires_at})
        return {"status": APPROVED, "approval_expires_at": approval_expires_at}

    async def execute(self, action_id: str):
        now = int(time.time())
        action = self.storage.get_action(action_id)
        if not action:
            raise ActionError(404, "Action not found")
        if action["status"] == EXECUTED:
            raise ActionError(400, "Action already executed")
        if action["status"] != APPROVED:
            raise ActionError(400, "Action must be APPROVED")
        if now > action["approval_expires_at"]:
            self.storage.update_action(action_id, status=EXPIRED)
            raise ActionError(400, "Approval expired")
        payload = json.loads(action["payload"])
        note_event = json.loads(action["note_event"])
        if action_hash(payload) != action["action_hash"]:
            raise ActionError(400, "Payload hash mismatch")
        relay_results = await self.publisher.publish_event(note_event, payload["relays"])
        for r in relay_results:
            self.storage.add_relay_result(action_id, r["relay_url"], r["success"], r.get("error_message"))
        self.storage.update_action(action_id, status=EXECUTED, executed_at=now)
        self.storage.add_audit(now, "ACTION_EXECUTED", action_id, {"relay_results": relay_results})
        return {"status": EXECUTED, "relay_results": relay_results, "event_id": note_event.get("id")}
