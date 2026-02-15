from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel


class RiskTier(str, Enum):
    SAFE = "SAFE"
    PRIVILEGED = "PRIVILEGED"


@dataclass
class Tool:
    name: str
    description: str
    input_schema: type[BaseModel]
    risk_tier: RiskTier
    preview: Callable[[BaseModel], str]
    execute: Callable[[BaseModel], Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools.keys())
