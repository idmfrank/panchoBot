import pytest

from server.tools.shell import ShellArgs, ShellPolicy, ShellTool


def test_shell_blocks_pipes_and_redirects(tmp_path):
    shell = ShellTool(ShellPolicy(str(tmp_path), ["ls", "pwd", "cat", "pytest"]))
    with pytest.raises(ValueError):
        shell.execute(ShellArgs(command="ls | cat"))
    with pytest.raises(ValueError):
        shell.execute(ShellArgs(command="ls > out.txt"))


def test_shell_blocks_non_allowlisted(tmp_path):
    shell = ShellTool(ShellPolicy(str(tmp_path), ["ls", "pwd", "cat", "pytest"]))
    with pytest.raises(ValueError):
        shell.execute(ShellArgs(command="rm -rf /"))
