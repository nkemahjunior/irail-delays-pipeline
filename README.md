# iRail Delays Pipeline

A batch data pipeline that tracks delays, cancellations and disruptions on the Belgian railway network. It polls the public [iRail API](https://docs.irail.be/) on a schedule, builds its own history (iRail offers no historical download), and serves the results in a dashboard.

**Status:** in development — infrastructure set up, ingestion next.

## Stack

| Layer | Tool |
| --- | --- |
| Infrastructure as code | Terraform |
| Orchestration | Kestra |
| Data lake | Google Cloud Storage |
| Data warehouse | BigQuery |
| Transformation | dbt |
| Dashboard | Streamlit |

## Scope

**Stations (13):** Brussels-Central, Brussels-South, Brussels-North, Antwerp-Central, Ghent-Sint-Pieters, Liège-Guillemins, Leuven, Bruges, Namur, Charleroi, Hasselt, Genk, Diepenbeek.

**Endpoints:**
- `/v1/liveboard` — upcoming departures per station, with delays, cancellations and platform changes
- `/v1/disturbances` — current network disruptions
- `/v1/stations` — station reference data, loaded once

**Polling:** every 10 minutes, 14 requests per poll, well within iRail's limit of 3 requests per second.

**Grain of the core table:** one row per departure (station + train + service date), holding the last delay observed before departure, cancellation flag, platform change, train type and destination.

**Questions the dashboard answers:**
- Average and median delay by station and hour of day
- Share of on-time departures (under 1 minute late)
- Cancellations and platform changes per station
- Delay by train type (IC, S, P…)
- Disruptions over time

## Data notes

Findings from inspecting real API responses:
- `delay` is in **seconds**, not minutes
- All values arrive as strings and are cast to proper types in dbt staging
- `time` is the scheduled departure as a Unix timestamp (UTC); actual departure = `time + delay`
- The `id` field in each departure is only its position in the list, not an identifier

## Repository layout

```
.devcontainer/   Codespace setup (Python venv, Docker, Terraform)
terraform/       GCS bucket and BigQuery dataset
```