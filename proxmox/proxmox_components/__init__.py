"""Reusable Pulumi components for the Proxmox homelab project."""

from .adguard_config_renderer import (
    AdGuardAllowRule,
    AdGuardDnsConfig,
    AdGuardFilteringConfig,
    AdGuardHttpConfig,
    AdGuardHttpDohConfig,
    AdGuardLogConfig,
    AdGuardTlsConfig,
    FilterListConfig,
)
from .apt import ProxmoxAptRepositories
from .base import ComponentBase
from .containers import (
    AdGuardConfig,
    AdGuardContainers,
    AdGuardInstanceConfig,
    LxcRuntimeConfig,
)
from .debian_lxc_template import DebianLxcTemplate, DebianLxcTemplateConfig
from .enums import Datastore
from .foundation import HomelabFoundation
from .helpers import format_resource_name
from .lxc import ProxmoxLxc
from .network import BridgeConfig, ProxmoxNetwork, ProxmoxNodeConfig
from .portainer import PortainerVm, PortainerVmConfig
from .users import ProxmoxUsers, UserConfig
from .vm import (
    CloudInitNetworkConfig,
    GuestOS,
    IsoAttachment,
    ProxmoxCloudInitVm,
    ProxmoxVm,
)

__all__ = [
    "AdGuardAllowRule",
    "AdGuardConfig",
    "AdGuardContainers",
    "AdGuardDnsConfig",
    "AdGuardFilteringConfig",
    "AdGuardHttpConfig",
    "AdGuardHttpDohConfig",
    "AdGuardInstanceConfig",
    "AdGuardLogConfig",
    "AdGuardTlsConfig",
    "BridgeConfig",
    "CloudInitNetworkConfig",
    "ComponentBase",
    "Datastore",
    "DebianLxcTemplate",
    "DebianLxcTemplateConfig",
    "FilterListConfig",
    "GuestOS",
    "HomelabFoundation",
    "IsoAttachment",
    "LxcRuntimeConfig",
    "PortainerVm",
    "PortainerVmConfig",
    "ProxmoxAptRepositories",
    "ProxmoxCloudInitVm",
    "ProxmoxLxc",
    "ProxmoxNetwork",
    "ProxmoxNodeConfig",
    "ProxmoxUsers",
    "ProxmoxVm",
    "UserConfig",
    "format_resource_name",
]
