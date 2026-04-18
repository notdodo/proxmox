# Proxmox Homelab

Pulumi-based Proxmox homelab infrastructure in Python.

The project is organized as a small internal library plus one production stack composition root. First-class Proxmox resources such as bridges, pools, downloaded images, templates, and generic VMs are defined in one inventory file and then consumed by higher-level workload components.

## Current Stack Model

The stack entrypoint is [__main__.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/__main__.py).

It currently provisions:

- a Proxmox provider configured from Pulumi config
- foundation resources for one Proxmox node
- first-class downloaded images
- first-class pools
- a reusable Debian LXC template
- a wildcard ACME certificate for `*.thedodo.xyz`
- AdGuard LXCs cloned from the shared Debian template
- a Portainer VM bootstrapped from an Ubuntu cloud image
- a generic Win11 VM

## Inventory-Driven Resources

The main operator UX is [stack_inventory.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/stack_inventory.py).

This is the file to edit when you want to:

- add or change bridges
- add or change pools
- add or change downloaded images
- add or change reusable LXC templates
- add or change generic VMs
- wire first-class resources into workload components

## Component Layout

Reusable components live in [proxmox_components/](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components).

Important modules:

- [foundation.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/foundation.py): node-level resources only
- [network.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/network.py): Linux bridges
- [users.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/users.py): Proxmox role and users
- [debian_lxc_template.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/debian_lxc_template.py): reusable Debian LXC template
- [lxc.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/lxc.py): generic LXC primitive
- [vm.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/vm.py): generic VM primitives, including cloud-init VMs
- [containers.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/containers.py): AdGuard workload
- [portainer.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/portainer.py): Portainer workload
- [adguard_config_renderer.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/adguard_config_renderer.py): AdGuard config serialization

## Foundation Resources

[HomelabFoundation](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/foundation.py) currently manages:

- Linux bridge resources on the Proxmox node
- APT repository toggles
- the `operations-automation` user and shared `Operations` role

The foundation component exports:

- the default bridge name used by workloads
- generated passwords for managed Proxmox users

## Downloaded Images

Downloaded datastore files are first-class resources created directly in the stack.

Current image inventory:

- Ubuntu 24.04 cloud image
- Win11 install ISO
- VirtIO driver ISO
- Debian 13 LXC template tarball

Important implementation detail:

- the Ubuntu cloud image is downloaded from the upstream `.img` URL
- the datastore filename is intentionally `ubuntu-24.04-server-cloudimg-amd64.qcow2`
- this is required by the Proxmox provider for `content_type="import"` and avoids the filename validation failure you hit when using the `.img` extension as the stored filename

## Debian LXC Template

The reusable Debian template is defined as a first-class template resource and consumed by AdGuard.

Current behavior:

- Debian 13 template image
- VMID `8000`
- hostname `debian-template`
- unprivileged LXC
- nesting enabled
- stopped by default
- SSH bootstrap material generated inside the component

The component exports:

- the template VMID
- the private SSH key used by dependent workloads

## AdGuard Workload

[AdGuardContainers](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/containers.py) is a higher-level workload component.

It currently:

- clones from the shared Debian template
- creates the AdGuard LXCs
- generates the AdGuard admin password internally
- renders a reviewable base `AdGuardHome.yaml`
- writes TLS certificate and private key as separate files referenced by path
- patches the bcrypt password hash separately so previews stay useful
- installs AdGuard Home over SSH
- restarts AdGuard when the rendered configuration changes
- reboots the guest only if Debian signals `/var/run/reboot-required`

The workload consumes:

- the shared Debian template VMID
- the template SSH private key
- the wildcard ACME certificate
- the default foundation bridge

The AdGuard component intentionally keeps the admin password internal to the workload instead of pushing that concern to the stack entrypoint.

## Portainer Workload

[PortainerVm](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/portainer.py) provisions a dedicated Ubuntu cloud-init VM and bootstraps Portainer inside it.

Current behavior:

- Ubuntu 24.04 cloud image VM
- Portainer CE running in Docker
- direct HTTPS on port `9443`
- Portainer admin user initialized via the local Portainer API
- Docker Compose used for Portainer deployment from a managed compose file

Implementation details:

- cloud-init user data comes from [files/templates/portainer-cloud-init.yml](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/files/templates/portainer-cloud-init.yml)
- the Portainer Compose file comes from [files/templates/portainer-compose.yml](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/files/templates/portainer-compose.yml)
- the Portainer VM component generates its own SSH key and admin password internally

Important current state:

- the stack does not currently export the Portainer URL, username, or password
- those values exist as component outputs inside `PortainerVm`, but they are not re-exported from [__main__.py](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/__main__.py)

## TLS and ACME

The stack uses [pulumiverse_acme](https://www.pulumi.com/registry/packages/acme/) against Let’s Encrypt.

Current certificate flow:

- ACME account registration with Let’s Encrypt
- DNS-01 validation through Cloudflare
- wildcard certificate for `*.thedodo.xyz`

Cloudflare is only the DNS challenge provider. It is not the certificate authority.

Operational consequence:

- certificate renewal happens when you run Pulumi
- if you want the Portainer and AdGuard certificate material renewed before expiry, you need scheduled stack runs such as periodic `pulumi up --yes`

## Generic VM Model

[ProxmoxVm](/Users/dodo/Desktop/Projects/Homelab/proxmox/proxmox/proxmox_components/vm.py) is the generic first-class VM primitive.

Current defaults:

- OVMF BIOS
- `pc-q35-10.1`
- OS-specific CPU/scsi defaults
- EFI disk enabled
- Win11 uses `x86-64-v2-AES`
- Linux guests use `host`

Known provider quirk:

- the code currently uses `ignore_changes` for VM disk speed fields because the Proxmox provider normalizes those values inconsistently and otherwise causes perpetual drift

This is a deliberate compatibility workaround in the generic VM component.

## Validation

Current validation workflow:

```bash
task format check type-check
pulumi preview --diff
```
