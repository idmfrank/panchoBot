from dataclasses import dataclass

from .actions import ActionService
from .ai.client import AIClient


@dataclass
class AgentPlanner:
    ai_client: AIClient
    actions: ActionService

    def plan(self, goal: str, session_id: str) -> dict:
        ai_plan = self.ai_client.plan(goal, self.actions.registry.names())
        created_actions = []
        for proposed in ai_plan.proposed_actions:
            created_actions.append(self.actions.create_proposed_action(proposed.tool_name, proposed.args, session_id))
        return {
            "plan_summary": ai_plan.plan_summary,
            "actions": created_actions,
        }
