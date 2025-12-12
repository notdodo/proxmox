output "root_public_key" {
  description = "`root` user OpenSSH public key to add to the PVE nodes"
  value       = tls_private_key.root_key.public_key_openssh
}
