"""Data model + export loading for the functions config audit."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional


class ExportError(ValueError):
    """Raised when an export file is malformed."""


SECRET_LIKE_TOKENS = ("PASSWORD", "SECRET", "TOKEN", "API_KEY", "APIKEY", "PRIVATE_KEY")
PROD_LABELS = ("prod", "production")


def is_secret_like(name: str) -> bool:
    upper = name.upper()
    return any(tok in upper for tok in SECRET_LIKE_TOKENS)


def is_prod(labels: tuple) -> bool:
    return any(c in x.lower() for x in labels for c in PROD_LABELS)


@dataclass(frozen=True)
class Function:
    name: str
    labels: tuple
    timeout: Optional[int] = None   # seconds; None = not recorded (service default 30s)
    memory: Optional[int] = None    # MB; None = not recorded (service default 128MB)
    config: tuple = ()              # (key, value) pairs as recorded

    def secret_config_keys(self) -> list:
        return [k for k, v in self.config if is_secret_like(k) and v]


@dataclass(frozen=True)
class Application:
    name: str
    functions: tuple = ()


def load_export(path: str) -> tuple:
    with open(path, "r", encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ExportError(f"{path}: not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("applications"), list):
        raise ExportError(f"{path}: top level must be an object with an 'applications' list")
    out = []
    for i, a in enumerate(raw["applications"]):
        where = f"applications[{i}]"
        if "name" not in a:
            raise ExportError(f"{where}: missing required field 'name'")
        functions = []
        for j, f in enumerate(a.get("functions", [])):
            fwhere = f"{where}.functions[{j}]"
            if "name" not in f:
                raise ExportError(f"{fwhere}: missing required field 'name'")
            for numfield in ("timeout", "memory"):
                v = f.get(numfield)
                if v is not None and (not isinstance(v, int) or v <= 0):
                    raise ExportError(f"{fwhere}.{numfield}: must be a positive integer when present")
            config = f.get("config", {})
            if not isinstance(config, dict):
                raise ExportError(f"{fwhere}.config: must be an object of key:value pairs")
            functions.append(Function(
                name=f["name"],
                labels=tuple(f.get("labels", [])),
                timeout=f.get("timeout"),
                memory=f.get("memory"),
                config=tuple(config.items()),
            ))
        out.append(Application(name=a["name"], functions=tuple(functions)))
    return tuple(out)
