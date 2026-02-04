# ProxmoxVE Configuration

Terraform configuration for the homelab ProxmoxVE cluster. Environment state is in `homelab/`, reusable modules live in `modules/`, and templates are in `files/templates/`.

## Layout
- `homelab/` – Proxmox infra + ACME certs (S3 backend in `homelab/versions.tf`).
- `adguard/` – AdGuard Home configuration (S3 backend in `adguard/versions.tf`).
- `modules/` – reusable Proxmox/infra modules.
- `files/templates/` – cloud-init and service config templates used by modules.

## Secrets
- Decrypted secrets live in `homelab/terraform.tfvars` and `adguard/terraform.tfvars`.
- Encrypted copies are `homelab/terraform.tfvars.enc` and `adguard/terraform.tfvars.enc`.
- Update encrypted files with SOPS after editing plaintext:
  ```powershell
  sops --encrypt .\homelab\terraform.tfvars > .\homelab\terraform.tfvars.enc
  sops --encrypt .\adguard\terraform.tfvars > .\adguard\terraform.tfvars.enc
  ```

## Quickstart
1. Export your SOPS key (example for 1Password):
   ```powershell
   $env:SOPS_AGE_KEY=$(op read "op://Private/ProxmoxVE - Main/SOPS AGE/secret-key")
   ```
2. Decrypt secrets:
   ```powershell
   sops --decrypt .\homelab\terraform.tfvars.enc > .\homelab\terraform.tfvars
   sops --decrypt .\adguard\terraform.tfvars.enc > .\adguard\terraform.tfvars
   ```
3. Apply everything in order:
   ```powershell
   task up
   ```

## AdGuard Notes
- AdGuard bootstrap config (admin + TLS) is rendered from `modules/proxmox_containers/templates/adguard-bootstrap.yaml.tftpl`.
- AdGuard configuration is applied from `adguard/`, which reads ACME cert outputs from `homelab` via `terraform_remote_state`.
- Run the AdGuard apply only when AdGuard is reachable.

## Notes on Templates
- Portainer cloud-init lives in `files/templates/`.
- Portainer node definitions live in `homelab/workloads.tf` (`local.portainer_nodes`).

## QA Tooling
- `task format` / `task format-check` – run `terraform fmt -recursive`.
- `task lint` – `tflint` across the repo.
- `task checkov`, `task kics`, `task trivy` – containerized misconfig scanners.
- `task check` – aggregated validation + formatting + security scans.
