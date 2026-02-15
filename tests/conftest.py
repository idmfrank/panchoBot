from fastapi.testclient import TestClient
import pytest

from server import main
from server.actions import ActionService
from server.agent import AgentPlanner
from server.ai.fake_client import FakeAIClient
from server.config import Settings, ensure_directories
from server.registry import RiskTier, Tool, ToolRegistry
from server.storage import Storage
from server.tools.shell import ShellArgs, ShellPolicy, ShellTool
from server.tools.workspace import ReadFileArgs, WorkspacePolicy, WorkspaceTools, WriteFileArgs, read_file_preview, write_file_preview


class ExplainPlanArgs(main.ExplainPlanArgs):
    pass


@pytest.fixture
def app_client(tmp_path):
    settings = Settings(db_path=str(tmp_path / "test.db"), workspace_dir=str(tmp_path / "workspace"), action_ttl_seconds=5, approval_ttl_seconds=5)
    ensure_directories(settings)
    storage = Storage(settings.db_path)
    registry = ToolRegistry()
    ws = WorkspaceTools(WorkspacePolicy(settings.workspace_dir, settings.max_read_bytes))
    sh = ShellTool(ShellPolicy(settings.workspace_dir, settings.allowed_shell_commands))

    registry.register(Tool("agent.explain_plan", "", ExplainPlanArgs, RiskTier.SAFE, main.explain_plan_preview, main.explain_plan_execute))
    registry.register(Tool("workspace.read_file", "", ReadFileArgs, RiskTier.SAFE, read_file_preview, ws.read_file))
    registry.register(Tool("workspace.write_file", "", WriteFileArgs, RiskTier.PRIVILEGED, write_file_preview, ws.write_file))
    registry.register(Tool("shell.run_allowlisted", "", ShellArgs, RiskTier.PRIVILEGED, sh.preview, sh.execute))

    main.settings = settings
    main.storage = storage
    main.registry = registry
    main.action_service = ActionService(storage, registry, settings.action_ttl_seconds, settings.approval_ttl_seconds)
    main.planner = AgentPlanner(FakeAIClient(), main.action_service)
    client = TestClient(main.app)
    return client, settings, main.action_service
