
variable "credential_path" {
  description = "Path to credential file"
  default = "<path to credentials file>"
}

variable "project_name" {
  description = "Name of the project on Google Compute Engine"
  default = "physiq-joe-test"
}

variable "image" {
  description = "Google VM image to use"
  default = "ubuntu-1510-wily-v20160315"
}

variable "ssh_pub_key" {
  description = "The public ssh key"
  default = "/media/USB4/physiq/keys/riak_rsa.pub"
}

variable "dataPublisher_count" {
  default = 1
}

variable "dataPublisher_ips" {
  default = {
    "0" = "10.240.0.5"
  }
}

variable "dataPublisher_hostnames" {
  default = {
    "0" = "datapub01.local"
  }
}

variable "dataPublisher_names" {
  default = {
    "0" = "datapub01"
  }
}
