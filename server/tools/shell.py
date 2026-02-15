import shlex
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field


class ShellArgs(BaseModel):
    command: str = Field(min_length=1)


FORBIDDEN_TOKENS = {"|", ">", "<", ">>", "&&", ";", "$", "`"}


class ShellPolicy:
    def __init__(self, workspace_dir: str, allowlisted_commands: list[str]):
        self.workspace = Path(workspace_dir).resolve()
        self.allowlisted_commands = set(allowlisted_commands)


class ShellTool:
    def __init__(self, policy: ShellPolicy):
        self.policy = policy

    def preview(self, args: ShellArgs) -> str:
        return f"Run shell command in workspace: {args.command}"

    def _validate(self, command: str) -> list[str]:
        if any(token in command for token in FORBIDDEN_TOKENS):
            raise ValueError("Command contains forbidden shell operators")
        parts = shlex.split(command)
        if not parts:
            raise ValueError("Command is empty")
        if parts[0] not in self.policy.allowlisted_commands:
            raise ValueError("Command not allowlisted")
        if parts[0] == "cat":
            for arg in parts[1:]:
                if arg.startswith("-"):
                    continue
                target = (self.policy.workspace / arg).resolve()
                if self.policy.workspace not in target.parents and target != self.policy.workspace:
                    raise ValueError("cat can only read files inside workspace")
        return parts

    def execute(self, args: ShellArgs) -> dict:
        parts = self._validate(args.command)
        proc = subprocess.run(parts, cwd=self.policy.workspace, capture_output=True, text=True, check=False)
        return {
            "command": args.command,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
