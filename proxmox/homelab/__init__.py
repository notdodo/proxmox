"""Stack composition helpers for the Proxmox homelab project."""

from .production import deploy_current_stack, deploy_production
from .provider import create_proxmox_provider, create_proxmox_provider_options
from .stacks import HomelabEnvironment, HomelabStack, current_stack, parse_stack_name

__all__ = [
    "HomelabEnvironment",
    "HomelabStack",
    "create_proxmox_provider",
    "create_proxmox_provider_options",
    "current_stack",
    "deploy_current_stack",
    "deploy_production",
    "parse_stack_name",
]
