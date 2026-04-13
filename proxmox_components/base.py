"""Base component classes for proxmox_components."""

from __future__ import annotations

import pulumi
from pulumi import ResourceOptions


class ComponentBase(pulumi.ComponentResource):
    """Base class for project-local Pulumi components."""

    type_prefix = "notdodo:proxmox-homelab"

    def __init__(
        self,
        name: str,
        type_suffix: str | None = None,
        opts: ResourceOptions | None = None,
    ) -> None:
        """Initialize the component with the shared type prefix."""
        if type_suffix is None:
            type_suffix = self.__class__.__name__
        super().__init__(f"{self.type_prefix}:{type_suffix}", name, {}, opts)
