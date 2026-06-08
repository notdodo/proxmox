"""Pulumi entrypoint for the Proxmox homelab project."""

from homelab import deploy_current_stack

deploy_current_stack()
