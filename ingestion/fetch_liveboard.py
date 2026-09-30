"""Fetch one iRail liveboard snapshot and store it as raw JSON in GCS."""
import json
import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

BASE_URL = "https://api.irail.be/v1"
USER_AGENT = (
    "irail-delays-pipeline/0.1 "
    f"(github.com/nkemahjunior/irail-delays-pipeline; {os.environ['IRAIL_CONTACT']})"
)
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCS_BUCKET = os.environ["GCS_BUCKET"]


def fetch_liveboard(station_id: str) -> dict:
    response = requests.get(
        f"{BASE_URL}/liveboard",
        params={"id": station_id, "arrdep": "departure", "format": "json", "lang": "en"},
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def upload_json(data: dict, blob_path: str) -> None:
    client = storage.Client(project=GCP_PROJECT)
    blob = client.bucket(GCS_BUCKET).blob(blob_path)
    blob.upload_from_string(json.dumps(data), content_type="application/json")


def main() -> None:
    station_id = "BE.NMBS.008833001"  # Leuven
    fetched_at = datetime.now(timezone.utc)
    data = fetch_liveboard(station_id)

    blob_path = (
        f"liveboard/fetch_date={fetched_at:%Y-%m-%d}/"
        f"{station_id}_{fetched_at:%Y%m%dT%H%M%SZ}.json"
    )
    upload_json(data, blob_path)

    print(f"Uploaded {len(data['departures']['departure'])} departures to gs://{GCS_BUCKET}/{blob_path}")


if __name__ == "__main__":
    main()