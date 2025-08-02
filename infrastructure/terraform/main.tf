# AWS Stock Monitor - Terraform Configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "from_email" {
  description = "Sender email address"
  type        = string
}

variable "to_email" {
  description = "Recipient email address"
  type        = string
}

variable "schedule_expression" {
  description = "CloudWatch Events schedule expression"
  type        = string
  default     = "cron(0 9,15 * * MON-FRI)"
}

# Provider
provider "aws" {
  region = var.region
}

# Data sources
data "aws_caller_identity" "current" {}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "StockMonitorLambdaRole-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "StockMonitorPolicy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail",
          "ses:GetIdentityVerificationAttributes"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish",
          "sns:CreateTopic",
          "sns:Subscribe",
          "sns:ListSubscriptionsByTopic"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/stock-monitor/*"
      }
    ]
  })
}

# Attach basic execution role to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function
resource "aws_lambda_function" "stock_monitor" {
  function_name = "stock-monitor-${var.environment}"
  role         = aws_iam_role.lambda_role.arn
  handler      = "src.lambda_function.lambda_handler"
  runtime      = "python3.9"
  timeout      = 300
  memory_size  = 512

  # Placeholder code - will be updated via deployment script
  filename = "lambda-deployment-package.zip"

  environment {
    variables = {
      STAGE      = var.environment
      FROM_EMAIL = var.from_email
      TO_EMAIL   = var.to_email
      SES_REGION = var.region
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_cloudwatch_log_group.lambda_logs,
  ]
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/stock-monitor-${var.environment}"
  retention_in_days = 30
}

# CloudWatch Events Rule
resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "stock-monitor-schedule-${var.environment}"
  description         = "Trigger stock monitor Lambda function"
  schedule_expression = var.schedule_expression
}

# CloudWatch Events Target
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "StockMonitorTarget"
  arn       = aws_lambda_function.stock_monitor.arn
}

# Permission for CloudWatch Events to invoke Lambda
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stock_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}

# SNS Topic
resource "aws_sns_topic" "alerts" {
  name = "stock-monitor-alerts-${var.environment}"
}

# SNS Subscription
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.to_email
}

# Systems Manager Parameters
resource "aws_ssm_parameter" "from_email" {
  name  = "/stock-monitor/${var.environment}/from-email"
  type  = "String"
  value = var.from_email
}

resource "aws_ssm_parameter" "to_email" {
  name  = "/stock-monitor/${var.environment}/to-email"
  type  = "String"
  value = var.to_email
}

resource "aws_ssm_parameter" "sns_topic_arn" {
  name  = "/stock-monitor/${var.environment}/sns-topic-arn"
  type  = "String"
  value = aws_sns_topic.alerts.arn
}

# Outputs
output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.stock_monitor.arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic"
  value       = aws_sns_topic.alerts.arn
}

output "cloudwatch_rule_arn" {
  description = "ARN of the CloudWatch Events rule"
  value       = aws_cloudwatch_event_rule.schedule.arn
}

output "log_group_name" {
  description = "Name of the CloudWatch Log Group"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}
