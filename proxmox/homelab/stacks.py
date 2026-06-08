"""Pulumi stack routing for the Proxmox homelab project."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pulumi import get_stack


class HomelabEnvironment(StrEnum):
    """Supported homelab deployment environments."""

    PRODUCTION = "production"


@dataclass
class HomelabStack:
    """Logical representation of a Proxmox homelab Pulumi stack."""

    env: HomelabEnvironment


def parse_stack_name(stack: str) -> HomelabStack:
    """Parse a Pulumi stack name into a typed homelab stack."""
    try:
        env = HomelabEnvironment(stack)
    except ValueError as exc:
        allowed = ", ".join(environment.value for environment in HomelabEnvironment)
        msg = f"Invalid stack name '{stack}'. Expected one of: {allowed}."
        raise ValueError(msg) from exc

    return HomelabStack(env=env)


def current_stack() -> HomelabStack:
    """Return the active Pulumi stack as a typed homelab stack."""
    return parse_stack_name(get_stack())
