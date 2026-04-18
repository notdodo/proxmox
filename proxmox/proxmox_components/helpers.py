"""Helper functions for the Pulumi component library."""

from __future__ import annotations

import re
from typing import NoReturn

from pulumi import Resource, error, warn

VALIDATING_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+$")


def pulumi_error(message: str, resource: Resource | None = None) -> NoReturn:
    """Raise a ``ValueError`` after emitting a Pulumi error diagnostic."""
    error(message, resource)
    raise ValueError(message)


def pulumi_warning(message: str, resource: Resource | None = None) -> None:
    """Emit a Pulumi warning diagnostic."""
    warn(message, resource)


def host_from_cidr(address: str) -> str:
    """Extract the host IP from a CIDR notation address (e.g. '10.0.0.1/24' → '10.0.0.1')."""
    return address.split("/", maxsplit=1)[0]


def format_resource_name(name: str, resource: Resource | None = None) -> str:
    """Format a string to be used safely as a Pulumi resource name."""
    if VALIDATING_REGEX.match(name):
        return name.lower().replace("_", "-")
    pulumi_error(
        f"Invalid resource name {name}. Only alphanumeric, '.', '-' and '_' are allowed.",
        resource,
    )
