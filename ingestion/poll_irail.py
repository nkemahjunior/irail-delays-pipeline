"""Poll iRail once: liveboards for all tracked stations plus disturbances, stored raw in GCS."""
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from google.cloud import storage
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

BASE_URL = "https://api.irail.be/v1"
USER_AGENT = (
    "irail-delays-pipeline/0.1 "
    f"(github.com/nkemahjunior/irail-delays-pipeline; {os.environ['IRAIL_CONTACT']})"
)
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCS_BUCKET = os.environ["GCS_BUCKET"]
PAUSE_SECONDS = 0.5

STATIONS = {
    "BE.NMBS.008813003": "Brussels-Central",
    "BE.NMBS.008814001": "Brussels-South",
    "BE.NMBS.008812005": "Brussels-North",
    "BE.NMBS.008821006": "Antwerp-Central",
    "BE.NMBS.008892007": "Ghent-Sint-Pieters",
    "BE.NMBS.008841004": "Liège-Guillemins",
    "BE.NMBS.008833001": "Leuven",
    "BE.NMBS.008891009": "Bruges",
    "BE.NMBS.008863008": "Namur",
    "BE.NMBS.008872009": "Charleroi-Central",
    "BE.NMBS.008831005": "Hasselt",
    "BE.NMBS.008831765": "Genk",
    "BE.NMBS.008831112": "Diepenbeek",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def make_session() -> requests.Session:
    retry = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch(session: requests.Session, endpoint: str, params: dict) -> dict:
    response = session.get(
        f"{BASE_URL}/{endpoint}",
        params={**params, "format": "json", "lang": "en"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def upload_json(bucket: storage.Bucket, data: dict, blob_path: str) -> None:
    blob = bucket.blob(blob_path)
    blob.upload_from_string(json.dumps(data), content_type="application/json")


def main() -> int:
    run_ts = datetime.now(timezone.utc)
    date_part = f"fetch_date={run_ts:%Y-%m-%d}"
    ts_part = f"{run_ts:%Y%m%dT%H%M%SZ}"

    session = make_session()
    bucket = storage.Client(project=GCP_PROJECT).bucket(GCS_BUCKET)
    failures = []

    for station_id, name in STATIONS.items():
        try:
            data = fetch(session, "liveboard", {"id": station_id, "arrdep": "departure"})
            upload_json(bucket, data, f"liveboard/{date_part}/{station_id}_{ts_part}.json")
            count = len(data.get("departures", {}).get("departure", []))
            log.info("%s: %d departures", name, count)
        except Exception:
            log.exception("%s (%s) failed", name, station_id)
            failures.append(name)
        time.sleep(PAUSE_SECONDS)

    try:
        data = fetch(session, "disturbances", {})
        upload_json(bucket, data, f"disturbances/{date_part}/disturbances_{ts_part}.json")
        log.info("Disturbances: %d active", len(data.get("disturbance", [])))
    except Exception:
        log.exception("Disturbances failed")
        failures.append("disturbances")

    if failures:
        log.error("Finished with %d failure(s): %s", len(failures), ", ".join(failures))
        return 1
    log.info("All %d requests succeeded", len(STATIONS) + 1)
    return 0


if __name__ == "__main__":
    sys.exit(main())