from pathlib import Path

from fastapi import FastAPI, Header
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from .actions import ActionError, ActionService
from .agent import AgentPlanner
from .ai.fake_client import FakeAIClient
from .ai.openai_client import OpenAIClient
from .config import ensure_directories, load_settings
from .registry import RiskTier, Tool, ToolRegistry
from .secrets import resolve_openai_api_key
from .storage import Storage
from .tools.shell import ShellArgs, ShellPolicy, ShellTool
from .tools.workspace import ReadFileArgs, WorkspacePolicy, WorkspaceTools, WriteFileArgs, read_file_preview, write_file_preview

settings = load_settings()
ensure_directories(settings)
storage = Storage(settings.db_path)
registry = ToolRegistry()
workspace_tools = WorkspaceTools(WorkspacePolicy(settings.workspace_dir, settings.max_read_bytes))
shell_tool = ShellTool(ShellPolicy(settings.workspace_dir, settings.allowed_shell_commands))


class ExplainPlanArgs(BaseModel):
    plan: str


def explain_plan_preview(args: ExplainPlanArgs) -> str:
    return f"Explain plan text: {args.plan[:120]}"


def explain_plan_execute(args: ExplainPlanArgs) -> dict:
    return {"summary": f"Plan: {args.plan}"}


registry.register(
    Tool(
        name="agent.explain_plan",
        description="Explain planner output in concise human language",
        input_schema=ExplainPlanArgs,
        risk_tier=RiskTier.SAFE,
        preview=explain_plan_preview,
        execute=explain_plan_execute,
    )
)
registry.register(
    Tool(
        name="workspace.read_file",
        description="Read text file inside local workspace",
        input_schema=ReadFileArgs,
        risk_tier=RiskTier.SAFE,
        preview=read_file_preview,
        execute=workspace_tools.read_file,
    )
)
registry.register(
    Tool(
        name="workspace.write_file",
        description="Write text file inside local workspace",
        input_schema=WriteFileArgs,
        risk_tier=RiskTier.PRIVILEGED,
        preview=write_file_preview,
        execute=workspace_tools.write_file,
    )
)
registry.register(
    Tool(
        name="shell.run_allowlisted",
        description="Run allowlisted shell command in workspace",
        input_schema=ShellArgs,
        risk_tier=RiskTier.PRIVILEGED,
        preview=shell_tool.preview,
        execute=shell_tool.execute,
    )
)

action_service = ActionService(storage, registry, settings.action_ttl_seconds, settings.approval_ttl_seconds)
openai_api_key = resolve_openai_api_key(settings)
ai_client = OpenAIClient(openai_api_key, settings.openai_model) if openai_api_key else FakeAIClient()
planner = AgentPlanner(ai_client, action_service)

app = FastAPI(title="PanchoBot MVP 0")


@app.exception_handler(ActionError)
def action_error_handler(_, exc: ActionError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


class PlanRequest(BaseModel):
    goal: str = Field(min_length=1)


class ApproveRequest(BaseModel):
    action_id: str


class ExecuteRequest(BaseModel):
    action_id: str


@app.post("/agent/plan")
def agent_plan(req: PlanRequest, x_session_id: str = Header(default="local-session")):
    return planner.plan(req.goal, x_session_id)


@app.post("/actions/approve")
def approve(req: ApproveRequest):
    return action_service.approve(req.action_id)


@app.post("/actions/execute")
def execute(req: ExecuteRequest):
    return action_service.execute(req.action_id)


@app.get("/actions/{action_id}")
def action_detail(action_id: str):
    return action_service.get_action_detail(action_id)


web_dir = Path(__file__).resolve().parent.parent / "web"


@app.get("/")
def index():
    return FileResponse(web_dir / "index.html")


@app.get("/app.js")
def app_js():
    return FileResponse(web_dir / "app.js")
