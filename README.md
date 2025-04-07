# ProxmoxVE Configuration

- `$env:SOPS_AGE_KEY=$(op read "op://Private/ProxmoxVE - Main/SOPS AGE/secret-key")`
- `sops --decrypt .\terraform.tfvars.enc > .\terraform.tfvars`
