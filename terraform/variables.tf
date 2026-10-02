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

variable "image_tag" {
  description = "Tag of the irail-ingestion image to run (git commit ID)"
  default     = "41f5021"
}

variable "irail_contact" {
  description = "Contact email sent to iRail in the User-Agent header"
}