locals {
  apis = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudscheduler.googleapis.com",
    "iam.googleapis.com"
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.apis)
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "images" {
  repository_id = "irail"
  location      = var.region
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

resource "google_service_account" "poller" {
  account_id   = "irail-poller"
  display_name = "iRail poller (Cloud Run job)"
  depends_on   = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "poller_writes_raw" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.poller.email}"
}

output "image_repo" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

locals {
  image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}/irail-ingestion:${var.image_tag}"
}

resource "google_cloud_run_v2_job" "poller" {
  name                = "irail-poller"
  location            = var.region
  deletion_protection = false
  depends_on          = [google_project_service.apis]

  template {
    task_count = 1
    template {
      service_account = google_service_account.poller.email
      timeout         = "300s"
      max_retries     = 1
      containers {
        image = local.image
        env {
          name  = "IRAIL_CONTACT"
          value = var.irail_contact
        }
        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }
        env {
          name  = "GCS_BUCKET"
          value = google_storage_bucket.raw.name
        }
        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }
    }
  }
}

resource "google_service_account" "scheduler" {
  account_id   = "irail-scheduler"
  display_name = "Triggers the iRail poller job"
  depends_on   = [google_project_service.apis]
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_runs_poller" {
  name     = google_cloud_run_v2_job.poller.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "poll_every_10_min" {
  name      = "irail-poll-every-10-min"
  region    = var.region
  schedule  = "*/10 * * * *"
  time_zone = "Europe/Brussels"

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.poller.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }
}