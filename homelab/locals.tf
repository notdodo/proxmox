locals {
  acme_directory = "https://acme-v02.api.letsencrypt.org/directory"
  acme_tos_url   = "https://letsencrypt.org/documents/LE-SA-v1.5-February-24-2025.pdf"

  portainer_nodes = {
    portainer-node-1 = {
      lan_ip          = "192.168.178.100/24"
      lan_gateway     = "192.168.178.1"
      cluster_ip      = "10.0.100.1/24"
      cluster_gateway = "10.0.100.1"
      bootstrap       = true
    }
    portainer-node-2 = {
      lan_ip          = "192.168.178.101/24"
      lan_gateway     = "192.168.178.1"
      cluster_ip      = "10.0.100.2/24"
      cluster_gateway = "10.0.100.1"
      bootstrap       = false
    }
    portainer-node-3 = {
      lan_ip          = "192.168.178.102/24"
      lan_gateway     = "192.168.178.1"
      cluster_ip      = "10.0.100.3/24"
      cluster_gateway = "10.0.100.1"
      bootstrap       = false
    }
  }
}
