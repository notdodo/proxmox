variable "users" {
  description = "List of Users with roles"
  type = list(object(
    {
      username    = string
      role_id     = string
      pam_enabled = bool
    }
  ))
}
