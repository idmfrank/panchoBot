from __future__ import annotations

from .config import Settings


def resolve_openai_api_key(settings: Settings) -> str | None:
    if settings.openai_api_key:
        return settings.openai_api_key
    return _read_keyring_secret(settings.openai_keyring_service, settings.openai_keyring_username)


def _read_keyring_secret(service_name: str, username: str) -> str | None:
    try:
        import keyring
    except Exception:
        return None

    try:
        secret = keyring.get_password(service_name, username)
    except Exception:
        return None

    return secret or None
