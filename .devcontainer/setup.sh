#!/usr/bin/env bash
set -e
sudo apt-get update
sudo apt-get install -y python3-pip python3.12-venv
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
[ -n "$SECRET_GCP_CREDS" ] && echo "$SECRET_GCP_CREDS" | base64 -d > gcp-service-account.json
chmod 600 gcp-service-account.json
