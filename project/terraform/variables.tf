variable dockerhub_username {
  type = string
}

variable dockerhub_password {
  type = string
}

variable "domain_name" {
  type = string
}

variable "existing_vpc_id" {
  type = string
}

variable "existing_subnet_ids" {
  type = list(string)
}

variable "aws_region" {
  type = string
}

variable "container_name" {
  type = string
}

variable "container_tag" {
  type = string
}