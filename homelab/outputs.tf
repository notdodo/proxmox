output "root_public_key" {
  description = "`root` user OpenSSH public key to add to the PVE nodes"
  value       = tls_private_key.root_key.public_key_openssh
}

output "acme_certificate_pem" {
  description = "ACME certificate PEM for shared use"
  value       = acme_certificate.thedodo.certificate_pem
  sensitive   = true
}

output "acme_private_key_pem" {
  description = "ACME private key PEM for shared use"
  value       = acme_certificate.thedodo.private_key_pem
  sensitive   = true
}
