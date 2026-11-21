"""FNC001-FNC004 rules."""

from __future__ import annotations

from dataclasses import dataclass

from .model import is_prod


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str  # HIGH | MEDIUM | LOW
    target: str
    detail: str


def rule_secret_config(apps: tuple) -> list:
    """FNC001 HIGH: secret-looking key with a value in function config."""
    out = []
    for a in apps:
        for f in a.functions:
            keys = f.secret_config_keys()
            if keys:
                out.append(
                    Finding("FNC001", "HIGH", f"{a.name}/{f.name}",
                            f"config records secret-looking key(s) {keys} with values; function config is "
                            f"passed as plaintext env vars - review and move these to OCI Vault if real")
                )
    return out


def rule_default_timeout(apps: tuple) -> list:
    """FNC002 MEDIUM: prod-labeled function with no timeout recorded (30s default)."""
    return [
        Finding("FNC002", "MEDIUM", f"{a.name}/{f.name}",
                "prod-labeled function records no timeout; it silently runs with the 30-second "
                "default - set a value close to what the function needs")
        for a in apps for f in a.functions if is_prod(f.labels) and f.timeout is None
    ]


def rule_default_memory(apps: tuple) -> list:
    """FNC003 MEDIUM: prod-labeled function with no memory recorded (128MB default)."""
    return [
        Finding("FNC003", "MEDIUM", f"{a.name}/{f.name}",
                "prod-labeled function records no memory; it silently runs with the 128 MB default "
                "(Java functions are recommended 256 MB+)")
        for a in apps for f in a.functions if is_prod(f.labels) and f.memory is None
    ]


def rule_empty_application(apps: tuple) -> list:
    """FNC004 LOW: application with zero functions recorded."""
    return [
        Finding("FNC004", "LOW", a.name,
                "application records zero functions; empty scaffolding as far as this export records")
        for a in apps if not a.functions
    ]


ALL_RULES = (
    rule_secret_config,
    rule_default_timeout,
    rule_default_memory,
    rule_empty_application,
)

_SEVERITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def run_all(apps: tuple) -> list:
    findings = []
    for rule in ALL_RULES:
        findings.extend(rule(apps))
    findings.sort(key=lambda x: (_SEVERITY_RANK[x.severity], x.rule, x.target))
    return findings


def exit_code(findings: list) -> int:
    if any(f.severity == "HIGH" for f in findings):
        return 2
    if findings:
        return 1
    return 0
