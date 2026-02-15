import json
import time
import uuid
from dataclasses import dataclass

from .crypto import action_hash, canonical_json
from .registry import RiskTier, ToolRegistry
from .storage import Storage

PROPOSED = "PROPOSED"
APPROVED = "APPROVED"
EXECUTED = "EXECUTED"
EXPIRED = "EXPIRED"
REJECTED = "REJECTED"


class ActionError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass
class ActionService:
    storage: Storage
    registry: ToolRegistry
    action_ttl_seconds: int
    approval_ttl_seconds: int

    def _now(self) -> int:
        return int(time.time())

    def _expire_if_needed(self, action: dict, phase: str) -> dict:
        now = self._now()
        if action["status"] in {EXECUTED, EXPIRED, REJECTED}:
            return action
        if now > action["expires_at"]:
            self.storage.update_action(action["action_id"], status=EXPIRED)
            self.storage.add_audit(action["action_id"], "ACTION_EXPIRED", now, {"phase": phase})
            action["status"] = EXPIRED
        return action

    def _canonical_payload(self, tool_name: str, args: dict, created_at: int, requested_by: str) -> dict:
        return {
            "tool_name": tool_name,
            "args": json.loads(canonical_json(args)),
            "created_at": created_at,
            "requested_by": requested_by,
        }

    def create_proposed_action(self, tool_name: str, args: dict, requested_by: str) -> dict:
        tool = self.registry.get(tool_name)
        if not tool:
            raise ActionError(400, f"Unknown tool: {tool_name}")
        parsed_args = tool.input_schema.model_validate(args)
        now = self._now()
        payload = self._canonical_payload(tool_name, parsed_args.model_dump(), now, requested_by)
        digest = action_hash(payload)
        action_id = str(uuid.uuid4())
        expires_at = now + self.action_ttl_seconds
        self.storage.create_action(
            {
                "action_id": action_id,
                "tool_name": tool_name,
                "args": parsed_args.model_dump(),
                "requested_by": requested_by,
                "created_at": now,
                "expires_at": expires_at,
                "action_hash": digest,
                "status": PROPOSED,
            }
        )
        self.storage.add_audit(action_id, "ACTION_PROPOSED", now, {"tool_name": tool_name, "action_hash": digest})
        return self.get_action_detail(action_id)

    def approve(self, action_id: str) -> dict:
        action = self.storage.get_action(action_id)
        if not action:
            raise ActionError(404, "Action not found")
        action = self._expire_if_needed(action, "approve")
        if action["status"] != PROPOSED:
            raise ActionError(400, "Action must be PROPOSED")
        now = self._now()
        approval_expires_at = now + self.approval_ttl_seconds
        self.storage.create_approval(
            {
                "action_id": action_id,
                "action_hash": action["action_hash"],
                "approved_at": now,
                "expires_at": approval_expires_at,
            }
        )
        self.storage.update_action(action_id, status=APPROVED, approval_expires_at=approval_expires_at)
        self.storage.add_audit(action_id, "ACTION_APPROVED", now, {"approval_expires_at": approval_expires_at})
        return self.get_action_detail(action_id)

    def execute(self, action_id: str) -> dict:
        action = self.storage.get_action(action_id)
        if not action:
            raise ActionError(404, "Action not found")
        action = self._expire_if_needed(action, "execute")
        now = self._now()
        tool = self.registry.get(action["tool_name"])
        if not tool:
            raise ActionError(500, "Tool missing from registry")

        if tool.risk_tier == RiskTier.PRIVILEGED:
            if action["status"] != APPROVED:
                raise ActionError(400, "Action must be APPROVED")
            approval = self.storage.get_latest_approval(action_id)
            if not approval:
                raise ActionError(400, "Missing approval")
            if approval["used"]:
                raise ActionError(400, "Approval already used")
            if approval["action_hash"] != action["action_hash"]:
                raise ActionError(400, "Approval hash mismatch")
            if now > approval["expires_at"]:
                self.storage.update_action(action_id, status=EXPIRED)
                self.storage.add_audit(action_id, "ACTION_EXPIRED", now, {"phase": "approval_expired"})
                raise ActionError(400, "Approval expired")
        else:
            if action["status"] != PROPOSED:
                raise ActionError(400, "Safe actions must be PROPOSED")

        if not tool:
            raise ActionError(500, "Tool missing from registry")
        parsed_args = tool.input_schema.model_validate(json.loads(action["args_json"]))

        result = tool.execute(parsed_args)
        if tool.risk_tier == RiskTier.PRIVILEGED:
            self.storage.mark_approval_used(approval["id"])
        self.storage.update_action(action_id, status=EXECUTED)
        self.storage.save_tool_result(action_id, result, now)
        self.storage.add_audit(action_id, "ACTION_EXECUTED", now, {"result": result})
        return {"action": self.get_action_detail(action_id), "result": result}

    def get_action_detail(self, action_id: str) -> dict:
        action = self.storage.get_action(action_id)
        if not action:
            raise ActionError(404, "Action not found")
        tool = self.registry.get(action["tool_name"])
        parsed_args = json.loads(action["args_json"])
        preview = tool.preview(tool.input_schema.model_validate(parsed_args)) if tool else ""
        return {
            "action_id": action["action_id"],
            "tool_name": action["tool_name"],
            "args": parsed_args,
            "status": action["status"],
            "expires_at": action["expires_at"],
            "approval_expires_at": action["approval_expires_at"],
            "action_hash": action["action_hash"],
            "preview": preview,
            "risk_tier": tool.risk_tier.value if tool else None,
            "audit": self.storage.list_audit(action_id),
        }
