import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    approval_ttl_seconds: int = 120
    action_ttl_seconds: int = 300
    bind_host: str = "0.0.0.0"
    port: int = 8787
    db_path: str = "./data/pancho.db"
    workspace_dir: str = "./workspace"
    max_read_bytes: int = 65536
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    allowed_shell_commands: list[str] = field(default_factory=lambda: ["ls", "pwd", "cat", "pytest"])



def load_settings() -> Settings:
    return Settings(
        approval_ttl_seconds=int(os.getenv("APPROVAL_TTL_SECONDS", "120")),
        action_ttl_seconds=int(os.getenv("ACTION_TTL_SECONDS", "300")),
        bind_host=os.getenv("BIND_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8787")),
        db_path=os.getenv("DB_PATH", "./data/pancho.db"),
        workspace_dir=os.getenv("WORKSPACE_DIR", "./workspace"),
        max_read_bytes=int(os.getenv("MAX_READ_BYTES", "65536")),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )



def ensure_directories(settings: Settings) -> None:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.workspace_dir).mkdir(parents=True, exist_ok=True)
