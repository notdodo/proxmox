"""Provider-level performance knobs for Proxmox guests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VmPerformanceConfig:
    """Optional VM tuning values that should be set per workload."""

    cpu_limit: float | None = None
    cpu_units: int | None = None
    disk_aio: str | None = "io_uring"
    disk_backup: bool | None = None
    disk_cache: str | None = "none"
    disk_replicate: bool | None = None
    network_mtu: int | None = None
    network_queues: int | None = None


@dataclass(frozen=True)
class LxcPerformanceConfig:
    """Optional LXC tuning values that should be set per workload."""

    cpu_limit: float | None = None
    cpu_units: int | None = 1024
    network_mtu: int | None = None
    rootfs_replicate: bool | None = None
