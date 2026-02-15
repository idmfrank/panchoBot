from pathlib import Path

from pydantic import BaseModel, Field


class ReadFileArgs(BaseModel):
    path: str = Field(min_length=1)


class WriteFileArgs(BaseModel):
    path: str = Field(min_length=1)
    content: str


class WorkspacePolicy:
    def __init__(self, workspace_dir: str, max_read_bytes: int = 65536):
        self.workspace = Path(workspace_dir).resolve()
        self.max_read_bytes = max_read_bytes

    def resolve(self, relative_path: str) -> Path:
        target = (self.workspace / relative_path).resolve()
        if self.workspace not in target.parents and target != self.workspace:
            raise ValueError("Path is outside workspace allowlist")
        return target


def read_file_preview(args: ReadFileArgs) -> str:
    return f"Read file from workspace: {args.path}"


def write_file_preview(args: WriteFileArgs) -> str:
    lines = args.content.splitlines()
    diff_preview = "\n".join(f"+ {line}" for line in lines[:20])
    if len(lines) > 20:
        diff_preview += "\n+ ..."
    return f"Write file in workspace: {args.path}\n{diff_preview}"


class WorkspaceTools:
    def __init__(self, policy: WorkspacePolicy):
        self.policy = policy

    def read_file(self, args: ReadFileArgs) -> dict:
        path = self.policy.resolve(args.path)
        if not path.exists() or not path.is_file():
            raise ValueError("File not found")
        data = path.read_text(encoding="utf-8")
        limited = data[: self.policy.max_read_bytes]
        return {"path": args.path, "content": limited, "truncated": len(limited) != len(data)}

    def write_file(self, args: WriteFileArgs) -> dict:
        path = self.policy.resolve(args.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args.content, encoding="utf-8")
        return {"path": args.path, "bytes_written": len(args.content.encode("utf-8"))}
