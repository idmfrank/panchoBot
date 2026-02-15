import json

from .client import AIClient, PlanOutput, ProposedAction


class OpenAIClient(AIClient):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def plan(self, goal: str, tool_names: list[str]) -> PlanOutput:
        prompt = (
            "You are a planner. Return strict JSON with keys plan_summary and proposed_actions. "
            "proposed_actions is a list of {tool_name, args}. Only use these tools: "
            f"{', '.join(tool_names)}. Goal: {goal}"
        )
        response = self.client.responses.create(model=self.model, input=prompt)
        parsed = json.loads(response.output_text)
        actions = [ProposedAction(tool_name=a["tool_name"], args=a.get("args", {})) for a in parsed.get("proposed_actions", [])]
        return PlanOutput(plan_summary=parsed.get("plan_summary", ""), proposed_actions=actions)
