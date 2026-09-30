variable "project_id" {
  description = "GCP project ID"
  default     = "my-project-de-502211"
}

variable "region" {
  description = "Region for all resources"
  default     = "europe-west1"
}

variable "bucket_name" {
  description = "Globally unique name for the raw data bucket"
  default     = "my-project-de-502211-irail-raw"
}