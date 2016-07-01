
variable "credential_path" {
  description = "Path to credential file"
  default = "/media/USB4/physiq/keys/Joe Test-739488a5114e.json"
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

variable "dataSubscriber_count" {
  default = 1 
}

variable "numInstances" {
  default = {
    "0" = "20"
    "1" = "20"
    "2" = "20"
  }
}

variable "dataSubscriber_ips" {
  default = {
    "0" = "10.218.1.8"
    "1" = "10.218.1.9"
    "2" = "10.218.1.10"
  }
}

variable "dataSubscriber_hostnames" {
  default = {
    "0" = "datasub01.local"
    "1" = "datasub02.local"
    "2" = "datasub03.local"
  }
}

variable "dataSubscriber_names" {
  default = {
    "0" = "datasub01"
    "1" = "datasub02"
    "2" = "datasub03"
  }
}
