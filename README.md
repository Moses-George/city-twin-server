# CityTwin Server

The Python API and simulation service for CityTwin. It exposes district
simulation, scenario storage, sensor-ingestion, ML-prediction, and WebSocket
endpoints for the [CityTwin Web dashboard](../city-twin-web/README.md).

## Features

- FastAPI service with interactive OpenAPI documentation.
- A 24-hour district simulation covering building energy, rooftop solar,
  traffic, comfort, and emissions.
- PostgreSQL-backed district, saved-scenario, and sensor-reading data.
- Optional energy, traffic, anomaly-detection, and scenario-surrogate models.
- WebSocket stream at `/ws/simulate` for hourly simulation updates.

## Requirements

- Python 3.11 or later.
- PostgreSQL.
- The packages listed in `requirements.txt`.

The dashboard can run its local simulator without this service. Start the
server when you need database-backed features, API simulation, or live and ML
features.

## Local setup

Run commands from this directory.

### 1. Create a virtual environment and install dependencies

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS/Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure the database and application

Create a PostgreSQL database, then create a `.env` file in this directory:

```dotenv
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/<database>
SECRET_KEY=<replace-with-a-long-random-secret>
FRONTEND_URL=http://localhost:5173
cors_origins=http://localhost:5173,http://localhost:8080
ml_artifacts_dir=ml/artifacts
```

`DATABASE_URL`, `SECRET_KEY`, and `FRONTEND_URL` are required by the
application. The CORS origins and ML artifacts directory have defaults and
can be adjusted as needed. Do not commit real credentials or secret keys.

Alembic reads its database URL from `alembic.ini`, separately from the
application's `.env`. Before migrating, make sure the `sqlalchemy.url` setting
in `alembic.ini` points to the same database as `DATABASE_URL`. Apply the
schema from this directory:

```sh
alembic upgrade head
```

### 3. Start the API

```sh
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API is available at `http://localhost:8000`. Check `http://localhost:8000/health`
for a health response and open `http://localhost:8000/docs` for interactive
API documentation.

## API overview

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | API name and status |
| `GET` | `/health` | Health check |
| `GET` | `/district` | District buildings and roads |
| `POST` | `/district/reseed` | Rebuild persisted district data |
| `POST` | `/simulate` | Calculate a 24-hour scenario |
| `GET`, `POST` | `/scenarios` | List or save named scenarios |
| `GET`, `DELETE` | `/scenarios/{scenario_id}` | Retrieve or delete a scenario |
| `POST`, `GET` | `/sensors` | Ingest or query sensor readings |
| `POST` | `/sensors/batch` | Ingest multiple readings |
| `GET` | `/sensors/{source_id}/latest` | Read a source's latest readings |
| `POST` | `/ml/energy/predict` | Predict building energy use |
| `POST` | `/ml/traffic/predict` | Predict traffic from supplied history |
| `POST` | `/ml/traffic/predict/{road_id}` | Predict from stored road readings |
| `POST` | `/ml/anomaly/score` | Score a sensor feature vector |
| `GET` | `/ml/anomaly/live` | Score latest readings for a source |
| `POST` | `/ml/scenario/predict` | Predict scenario KPIs with the surrogate |
| WebSocket | `/ws/simulate` | Stream hourly simulation data |

Scenario inputs are `solar_adoption_pct` (0–100), `ev_share_pct` (0–100),
`hvac_setpoint_c` (16–26), `signal_timing_pct` (50–150), `outdoor_temp_c`
(-5–35), and `occupancy_pct` (30–120). See `/docs` for request and response
schemas.

Example simulation request:

```json
{
  "solar_adoption_pct": 80,
  "ev_share_pct": 60,
  "hvac_setpoint_c": 22,
  "signal_timing_pct": 130,
  "outdoor_temp_c": 16,
  "occupancy_pct": 100
}
```

The live anomaly endpoint needs a recent reading for each of these kinds for
the same `source_id`: `energy_kw`, `temp_c`, `occupancy_pct`, and `congestion`.
Use `POST /sensors` to ingest readings.

## Optional ML models

Pre-trained artifacts are stored in `ml/artifacts/`. If you want to regenerate
training data or train the models, install the additional packages used by
those scripts:

```sh
pip install pyarrow xgboost torch
```

Then run from this directory:

```sh
python ml/generate_synthetic_data.py
python ml/train_energy_forecast.py
python ml/train_traffic_lstm.py
python ml/train_anomaly_detector.py
python ml/train_scenario_regressor.py
```

The data generator writes Parquet files under `ml/data/`; each training script
stores its model under `ml/artifacts/`. Model endpoints indicate whether the
corresponding artifact is loaded, so the API can still run when optional
artifacts are unavailable.

## Project layout

```text
app/
  core/           Settings and database connections
  models/         SQLAlchemy models
  routers/        District, simulation, scenario, sensor, ML, and live routes
  main.py         FastAPI application
  simulation.py   District generator and simulation engine
  ml_service.py   Optional model loading and inference
alembic/          Database migrations
ml/
  data/           Generated training datasets
  artifacts/      Serialized trained models
  *.py            Data generation and training scripts
requirements.txt  Python runtime dependencies
```
