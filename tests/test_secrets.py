from server.config import Settings
from server.secrets import resolve_openai_api_key


class StubKeyring:
    def __init__(self, value):
        self.value = value

    def get_password(self, service_name, username):
        assert service_name == "svc"
        assert username == "user"
        return self.value


def test_resolve_openai_api_key_prefers_explicit_env():
    settings = Settings(openai_api_key="env-key", openai_keyring_service="svc", openai_keyring_username="user")
    assert resolve_openai_api_key(settings) == "env-key"


def test_resolve_openai_api_key_uses_keyring(monkeypatch):
    settings = Settings(openai_api_key=None, openai_keyring_service="svc", openai_keyring_username="user")
    monkeypatch.setitem(__import__("sys").modules, "keyring", StubKeyring("keyring-key"))
    assert resolve_openai_api_key(settings) == "keyring-key"
