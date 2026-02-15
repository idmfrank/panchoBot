from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProposedAction:
    tool_name: str
    args: dict


@dataclass
class PlanOutput:
    plan_summary: str
    proposed_actions: list[ProposedAction]


class AIClient(Protocol):
    def plan(self, goal: str, tool_names: list[str]) -> PlanOutput:
        ...
