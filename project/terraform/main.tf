terraform {
  backend "s3" {
  }
}

// Create a secret for ECS to use to authenticate to Dockerhub to pull down the image
resource "aws_secretsmanager_secret" "dockerhub_secret" {
  name                    = "dockerhub-pickem"
  description             = "Dockerhub private registry credentials"
  recovery_window_in_days = 0
}

// Create a secret to store credentials to dockerhub for use by ECS
resource "aws_secretsmanager_secret_version" "ecs_credentials" {
  secret_id     = aws_secretsmanager_secret.dockerhub_secret.id
  secret_string = jsonencode({"username"="${var.dockerhub_username}","password"="${var.dockerhub_password}"})
}

// Create a security group to allow traffic over 443
resource "aws_security_group" "rjscollegepickem_sg" {
  name        = "rjscollegepickem-sg"
  vpc_id      = var.existing_vpc_id
  description = "LB security group"
}

resource "aws_security_group_rule" "lb_ingress_traffic" {
  type              = "ingress"
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.rjscollegepickem_sg.id
  description       = "HTTP ingress"
  from_port         = 443
  to_port           = 443
}

resource "aws_security_group_rule" "lb_egress_traffic" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.rjscollegepickem_sg.id
  description       = "HTTP egress"
}

// Create an ECS cluster
resource "aws_ecs_cluster" "ecs_cluster" {
  name = "rjscollegepickem"
}

// Create an r53 hosted zone
resource "aws_route53_zone" "public_zone" {
  name = var.domain_name
}

// Create the cert to bind to the ALB to allow https
resource "aws_acm_certificate" "rjscollege_cert" {
  domain_name       = var.domain_name
  validation_method = "DNS"
}

// Create hosted zone records to validate cert with domain name
resource "aws_route53_record" "r53_records" {
  for_each = {
    for dvo in aws_acm_certificate.rjscollege_cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.public_zone.zone_id
}

resource "aws_acm_certificate_validation" "rjscollege_validation" {
  certificate_arn         = aws_acm_certificate.rjscollege_cert.arn
  validation_record_fqdns = [for record in aws_route53_record.r53_records : record.fqdn]
}

// Create ALB to set as the A record in r53
resource "aws_lb" "rjscollegepickem_lb" {
  name                       = "rjscollegepickem-alb"
  internal                   = false
  load_balancer_type         = "application"
  subnets                    = var.existing_subnet_ids
  security_groups            = [aws_security_group.rjscollegepickem_sg.id]
  enable_deletion_protection = false
  drop_invalid_header_fields = false
}

resource "aws_lb_target_group" "tcp_rjscollegepickem_ip" {
  name        = "rjscollegepickem-lb-tg"
  port        = 443
  protocol    = "HTTPS"
  target_type = "ip"
  vpc_id      = var.existing_vpc_id
}

// Create load balancer listener
resource "aws_lb_listener" "rjscollegepickem_alb_listener" {
  load_balancer_arn = aws_lb.rjscollegepickem_lb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate_validation.rjscollege_validation.certificate_arn
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tcp_rjscollegepickem_ip.arn
  }
}

// Create role needed for ECS task execution
data "aws_iam_policy_document" "pickem_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com", "secretsmanager.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecsPickemTaskExecutionRole" {
  name                = "ecsPickemExecutionRole"
  assume_role_policy  = data.aws_iam_policy_document.pickem_assume_role_policy.json
  managed_policy_arns = ["arn:aws:iam::aws:policy/SecretsManagerReadWrite", "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"]
}

// Create the container definition
module "ecs-container-definition" {
  source  = "cloudposse/ecs-container-definition/aws"
  version = "0.58.1"

  command = ["flask","run","-h","0.0.0.0","-p","443","--cert=./app/certs/pickem.crt","--key=./app/certs/pickem.key"]

  container_image = "ryanaj9393/${var.container_name}:${var.container_tag}"
  container_name  = var.container_name
  essential       = true
  privileged      = false

  repository_credentials = {
    credentialsParameter = aws_secretsmanager_secret.dockerhub_secret.arn
  }

  port_mappings = [
    {
      containerPort = 443
      hostPort      = 443
      protocol      = "tcp"
    }
  ]
}

# Define the task based on the container
resource "aws_ecs_task_definition" "rjscollegepickem_task" {
  family                   = "rjscollegepickem"
  network_mode             = "awsvpc"
  container_definitions    = jsonencode([module.ecs-container-definition.json_map_object])
  execution_role_arn       = aws_iam_role.ecsPickemTaskExecutionRole.arn
  cpu                      = 1024
  memory                   = 4096
  requires_compatibilities = ["FARGATE"]
}

resource "aws_ecs_service" "rjscollegepickem_service" {
  name            = "rjscollegepickem-service"
  cluster         = aws_ecs_cluster.ecs_cluster.id
  task_definition = aws_ecs_task_definition.rjscollegepickem_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.existing_subnet_ids
    security_groups  = [aws_security_group.rjscollegepickem_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.tcp_rjscollegepickem_ip.arn
    container_name   = var.container_name
    container_port   = 443
  }

  depends_on = [aws_lb_listener.rjscollegepickem_alb_listener]
}

resource "aws_route53_record" "arecord" {
  allow_overwrite = true
  zone_id = aws_route53_zone.public_zone.zone_id
  name    = ""
  type    = "A"
  alias {
    evaluate_target_health = true
    name                   = aws_lb.rjscollegepickem_lb.dns_name
    zone_id                = aws_lb.rjscollegepickem_lb.zone_id
  }
}