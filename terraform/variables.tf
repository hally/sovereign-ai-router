variable "project_name" {
  type        = string
  description = "Project name prefix"
  default     = "sovereign-ai-router"
}

variable "aws_region" {
  type        = string
  description = "AWS region for deployment"
  default     = "us-east-1"
}

variable "lambda_zip_path" {
  type        = string
  description = "Path to the Lambda zip file"
  default     = "../build/router.zip"
}