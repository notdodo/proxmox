"""Reusable Pulumi components for the Proxmox homelab project."""

from .adguard_config_renderer import (
    AdGuardDnsConfig,
    AdGuardFilteringConfig,
    AdGuardHttpConfig,
    AdGuardLogConfig,
    AdGuardTlsConfig,
    FilterListConfig,
)
from .apt import ProxmoxAptRepositories
from .base import ComponentBase
from .containers import AdGuardContainers, AdGuardInstanceConfig, LxcRuntimeConfig
from .debian_lxc_template import DebianLxcTemplate, DebianLxcTemplateConfig
from .enums import Datastore
from .foundation import HomelabFoundation
from .helpers import format_resource_name
from .lxc import ProxmoxLxc
from .network import ProxmoxNetwork, ProxmoxNodeConfig
from .users import ProxmoxUsers, UserConfig
from .vm import GuestOS, IsoAttachment, ProxmoxVm

__all__ = [
    "AdGuardContainers",
    "AdGuardDnsConfig",
    "AdGuardFilteringConfig",
    "AdGuardHttpConfig",
    "AdGuardInstanceConfig",
    "AdGuardLogConfig",
    "AdGuardTlsConfig",
    "ComponentBase",
    "Datastore",
    "DebianLxcTemplate",
    "DebianLxcTemplateConfig",
    "FilterListConfig",
    "GuestOS",
    "HomelabFoundation",
    "IsoAttachment",
    "LxcRuntimeConfig",
    "ProxmoxAptRepositories",
    "ProxmoxLxc",
    "ProxmoxNetwork",
    "ProxmoxNodeConfig",
    "ProxmoxUsers",
    "ProxmoxVm",
    "UserConfig",
    "format_resource_name",
]
