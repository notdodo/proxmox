# ProxmoxVE Configuration

Terraform configuration for the homelab ProxmoxVE cluster. Live state sits under `homelab/`, reusable modules stay in `modules/`, and supporting templates live in `files/templates/`.

## Layout
- `homelab/` – environment config, backend settings, and tfvars (encrypted + example).
- `modules/` – reusable Proxmox/infra modules.
- `files/templates/` – cloud-init and service config templates used by modules.
- `docs/` – extended usage notes and operational steps.
- `homelab/locals.tf` – environment-only constants such as ACME endpoints and `portainer_nodes` map.

## Quickstart
1. Export your SOPS key (example for 1Password):\
   ```powershell
   $env:SOPS_AGE_KEY=$(op read "op://Private/ProxmoxVE - Main/SOPS AGE/secret-key")
   ```
2. Decrypt secrets:\
   ```powershell
   sops --decrypt .\homelab\terraform.tfvars.enc > .\homelab\terraform.tfvars
   ```
3. Initialise and validate:\
   ```powershell
   task install
   task validate
   ```
4. Plan/apply from `homelab`:\
   ```powershell
   terraform -chdir=homelab plan
   terraform -chdir=homelab apply
   ```

See `docs/README.md` for more detailed workflows.
