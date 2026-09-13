# PlanOS Infrastructure

AWS-ready Terraform configuration for deploying PlanOS.

## Architecture

```
Internet → ALB → ECS/Fargate (API) → RDS PostgreSQL
                                  → ElastiCache Redis
         → ECS/Fargate (Worker)
```

## Usage

```bash
cd infrastructure/terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply
```

## Resources

- VPC with public/private subnets
- Application Load Balancer
- ECS Cluster with Fargate services
- RDS PostgreSQL
- ElastiCache Redis
- Security Groups
- IAM Roles
