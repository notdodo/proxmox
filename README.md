# Proxmox Homelab

Infrastructure as Code for a Proxmox homelab using Pulumi and Python.

## What it manages

- **Node configuration**: networking (Linux bridges), APT repositories, users and roles
- **LXC templates**: Debian base template with SSH bootstrap (keys + password)
- **Containers**: AdGuard Home DNS instances cloned from the base template, with automated install, config rendering, and TLS via ACME
- **Virtual machines**: OS-aware VM provisioning with sane defaults per guest OS (Windows, Debian, Ubuntu)
- **Certificates**: Wildcard TLS via Let's Encrypt with Cloudflare DNS validation

## Stacks

- `production`: single Proxmox node with networking, users, ACME certificates, AdGuard containers, and VMs

## QA

- `task format` / `task format-check`
- `task lint`
- `task check`
