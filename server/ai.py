from dataclasses import dataclass
from typing import Protocol


class DraftAIClient(Protocol):
    def draft(self, prompt: str) -> str:
        ...


@dataclass
class RuleBasedDraftAIClient:
    """Local deterministic fallback drafting client for MVP0."""

    max_len: int = 280

    def draft(self, prompt: str) -> str:
        text = " ".join(prompt.strip().split())
        if not text:
            return ""
        if len(text) <= self.max_len:
            return text
        return text[: self.max_len - 1].rstrip() + "…"


@dataclass
class AIDraftService:
    client: DraftAIClient
    max_content_len: int

    def generate_draft(self, prompt: str) -> dict:
        draft = self.client.draft(prompt)
        safe_draft = draft[: self.max_content_len]
        return {
            "draft": safe_draft,
            "guardrails": {
                "can_execute_actions": False,
                "scope": "draft-only",
            },
        }
