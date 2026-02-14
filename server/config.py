import os
from dataclasses import dataclass


@dataclass
class Settings:
    relays_allowlist: list[str]
    propose_ttl_seconds: int = 300
    approval_ttl_seconds: int = 120
    max_content_len: int = 1000
    bind_host: str = "127.0.0.1"
    port: int = 8787
    db_path: str = "./data/pancho.db"



def _parse_relays(value: str | None) -> list[str]:
    if not value:
        return ["wss://relay.damus.io", "wss://nos.lol"]
    return [x.strip() for x in value.split(",") if x.strip()]



def load_settings() -> Settings:
    return Settings(
        relays_allowlist=_parse_relays(os.getenv("RELAYS_ALLOWLIST")),
        propose_ttl_seconds=int(os.getenv("PROPOSE_TTL_SECONDS", "300")),
        approval_ttl_seconds=int(os.getenv("APPROVAL_TTL_SECONDS", "120")),
        max_content_len=int(os.getenv("MAX_CONTENT_LEN", "1000")),
        bind_host=os.getenv("BIND_HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8787")),
        db_path=os.getenv("DB_PATH", "./data/pancho.db"),
    )
