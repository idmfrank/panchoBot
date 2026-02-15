from .client import AIClient, PlanOutput, ProposedAction


class FakeAIClient(AIClient):
    def plan(self, goal: str, tool_names: list[str]) -> PlanOutput:
        lowered = goal.lower()
        if "readme" in lowered:
            action = ProposedAction(
                tool_name="workspace.write_file",
                args={"path": "README.generated.md", "content": f"# Generated\n\n{goal}\n"},
            )
            return PlanOutput(plan_summary="Create a README file in workspace.", proposed_actions=[action])
        action = ProposedAction(tool_name="agent.explain_plan", args={"plan": goal})
        return PlanOutput(plan_summary="Summarize the user goal.", proposed_actions=[action])
