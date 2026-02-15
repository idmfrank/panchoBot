import pytest

from server.tools.workspace import ReadFileArgs, WorkspacePolicy, WorkspaceTools, WriteFileArgs


def test_workspace_allowlist_enforced(tmp_path):
    tools = WorkspaceTools(WorkspacePolicy(str(tmp_path / "workspace")))
    with pytest.raises(ValueError):
        tools.write_file(WriteFileArgs(path="../evil.txt", content="no"))


def test_workspace_read_write_roundtrip(tmp_path):
    tools = WorkspaceTools(WorkspacePolicy(str(tmp_path / "workspace")))
    tools.write_file(WriteFileArgs(path="ok.txt", content="hello"))
    result = tools.read_file(ReadFileArgs(path="ok.txt"))
    assert result["content"] == "hello"
