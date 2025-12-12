# Homelab Terraform Runbook

## Directory guide
- `homelab/` – entrypoint for plans/applies (`terraform.tfvars[.enc|.example]`, providers, workloads).
- `modules/` – shared modules; keep them free of environment-only files.
- `files/templates/` – cloud-init/user-data and app configs consumed by modules.

## Secrets and vars
- Keep real values in `live/homelab/terraform.tfvars.enc`; decrypt to `terraform.tfvars` before use.
- Use `terraform.tfvars.example` as the canonical shape for new environments; do not commit decrypted secrets.
- Backend settings are defined inline in `homelab/versions.tf` (S3).

## Typical workflow
```powershell
$env:SOPS_AGE_KEY=$(op read "op://Private/ProxmoxVE - Main/SOPS AGE/secret-key")
sops --decrypt .\homelab\terraform.tfvars.enc > .\homelab\terraform.tfvars

task install    # terraform init -chdir=homelab
task validate   # terraform validate -chdir=homelab
terraform -chdir=homelab plan
terraform -chdir=homelab apply
```

## Notes on templates
- AdGuard configs and Portainer cloud-init live in `files/templates/`; modules receive them via variables so they stay environment-agnostic.
- Update these templates instead of editing module internals when changing service bootstrap configuration.
- Portainer node definitions now live in `live/homelab/locals.tf` (`portainer_nodes` map); adjust addresses/gateway/bootstrap flags there.

## QA tooling
- `task format` / `task format-check` – run `terraform fmt -recursive`.
- `task lint` – `tflint` across the repo.
- `task checkov`, `task kics`, `task trivy` – containerized misconfig scanners.
- `task check` – aggregated validation + formatting + security scans.
