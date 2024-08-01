#!/bin/bash


# Pull and set environment variables to build terraform backend providers file
echo "Setting TF backend variables..."
export AWS_REGION=$(python3 ../scripts/file_lookup.py ../environment/vars.tfvars aws_region | jq '.aws_region' | tr -d '"')
export AWS_PROVIDER_VERSION=$(python3 ../scripts/file_lookup.py ../environment/vars.tfvars aws_provider_version | jq '.aws_provider_version' | tr -d '"')

# Build Terraform Backend Provider file
echo "Building provider file..."
cd ../terraform_backend
j2 ./templates/providers.tf.j2 -o ./providers.tf

echo "Terraform Init..."
terraform init
echo "Checking if backend already exists..."
terraform import -var-file=../environment/state-s3.tfvars aws_s3_bucket.terraform_state rjscollegepickem
BUCKET_STATUS=$(echo $?)

# If bucket doesnt exist build it
if [ $BUCKET_STATUS != 0 ]
then
  echo "Found no backend, building one..."
  terraform plan -var-file=../environment/state-s3.tfvars -out='./terraformplan.out'
  terraform apply -auto-approve -lock=true './terraformplan.out'
  rm -rf ./terraformplan.out
else
  echo "An existing remote backend has been detected successfully."
  echo "Re-initializing using the detected remote backend."
fi
rm -rf ./terraform.tfstate
rm -rf ./providers.tf

# Initialize terraform after initializing or creating a backend
cd ../terraform
j2 ./templates/providers.tf.j2 -o ./providers.tf
terraform init -backend-config=../environment/state-s3.tfvars
terraform plan -var-file=../environment/vars.tfvars -out='./terraformplan.out'
terraform apply -auto-approve -lock=true './terraformplan.out'
rm -rf ./terraformplan.out
rm -rf ./providers.tf

# uncomment deploy to destroy the resources
# terraform destroy -var-file=../environment/vars.tfvars -auto-approve -lock=true
