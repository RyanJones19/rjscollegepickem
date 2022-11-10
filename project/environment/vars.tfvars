# Deploy level environment variables
aws_region             = "us-west-2"
aws_provider_version   = "~> 3.71.0"

# Networking Variables
existing_vpc_id        = "vpc-0023d5818dc90cc16"
existing_subnet_ids    = ["subnet-0f338a8f2bdbf93a7","subnet-0ef21a115094fe723"]
vpc_cidr               = "172.31.0.0/16"
domain_name            = "rjspickem.com"

# Dockerhub details
dockerhub_username     = "your_dockerhub_username"
dockerhub_password     = "your_dockerhub_password"
container_name         = "rjscollegepickem"
container_tag          = "45"


