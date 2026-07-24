# from fastapi import APIRouter
# from ..schemas import (
#     EnergyPredictRequest, TrafficPredictRequest, AnomalyScoreRequest,
#     ScenarioPredictRequest,
# )
# from ..ml_service import ml_service

# router = APIRouter(prefix="/ml", tags=["ml"])


# @router.post("/energy/predict")
# def energy_predict(req: EnergyPredictRequest):
#     feats = req.model_dump()
#     for t in ("residential", "office", "retail", "industrial"):
#         feats[f"type_{t}"] = 1.0 if feats["building_type"] == t else 0.0
#     del feats["building_type"]
#     y = ml_service.energy_predict(feats)
#     return {"model_loaded": y is not None, "predicted_kwh": y}


# @router.post("/traffic/predict")
# def traffic_predict(req: TrafficPredictRequest):
#     y = ml_service.traffic_predict(req.history)
#     return {"model_loaded": y is not None, "next_hour_vehicles": y}


# @router.post("/anomaly/score")
# def anomaly_score(req: AnomalyScoreRequest):
#     y = ml_service.anomaly_score(req.features)
#     return {"model_loaded": y is not None, "anomaly_score": y,
#             "is_anomaly": (y is not None and y > 0.65)}


# @router.post("/scenario/predict")
# def scenario_predict(req: ScenarioPredictRequest):
#     feats = [req.solar_adoption_pct, req.ev_share_pct, req.hvac_setpoint_c,
#              req.signal_timing_pct, req.outdoor_temp_c, req.occupancy_pct]
#     y = ml_service.scenario_predict(feats)
#     keys = ["grid_import_kwh", "solar_generation_kwh", "peak_load_kw",
#             "avg_comfort", "avg_congestion", "co2_kg_per_day", "renewable_share_pct"]
#     return {"model_loaded": y is not None,
#             "kpis": dict(zip(keys, y)) if y else None}


from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_async_db
from ..schemas import (
    EnergyPredictRequest,
    TrafficPredictRequest,
    AnomalyScoreRequest,
    ScenarioPredictRequest,
    AnomalyBySourceResult,
)
from ..ml_service import ml_service
from .. import crud
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/ml", tags=["ml"])

ANOMALY_FEATURE_KINDS = ["energy_kw", "temp_c", "occupancy_pct", "congestion"]


@router.post("/energy/predict")
async def energy_predict(req: EnergyPredictRequest):
    feats = req.model_dump()
    for t in ("residential", "office", "retail", "industrial"):
        feats[f"type_{t}"] = 1.0 if feats["building_type"] == t else 0.0
    del feats["building_type"]
    y = ml_service.energy_predict(feats)
    return {"model_loaded": y is not None, "predicted_kwh": y}


@router.post("/traffic/predict")
async def traffic_predict(req: TrafficPredictRequest):
    if len(req.history) < 1:
        raise HTTPException(
            status_code=422, detail="history must have at least 1 point"
        )
    y = ml_service.traffic_predict(req.history)
    return {"model_loaded": y is not None, "next_hour_vehicles": y}


@router.post("/traffic/predict/{road_id}")
async def traffic_predict_from_history(road_id: str, db: AsyncSession = Depends(get_async_db)):
    """Same as /traffic/predict but pulls the last 24 stored readings for
    this road instead of requiring the caller to pass history explicitly."""
    rows = await crud.latest_readings_for_source(db, road_id, n=24)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No stored readings for {road_id}")
    history = [r.value for r in rows]
    y = ml_service.traffic_predict(history)
    return {
        "model_loaded": y is not None,
        "n_readings": len(history),
        "next_hour_vehicles": y,
    }


@router.post("/anomaly/score")
async def anomaly_score(req: AnomalyScoreRequest):
    y = await ml_service.anomaly_score(req.features)
    return {
        "model_loaded": y is not None,
        "anomaly_score": y,
        "is_anomaly": (y is not None and y > 0.65),
    }


@router.get("/anomaly/live", response_model=AnomalyBySourceResult)
async def anomaly_live(source_id: str = "district", db: AsyncSession = Depends(get_async_db)):
    """Builds the [energy_kw, temp_c, occupancy_pct, congestion] feature
    vector the Isolation Forest was trained on from the most recent stored
    reading of each kind for `source_id`, then scores it. Feed real values
    in via POST /sensors using these four `kind` values to make this live."""
    feats = []
    latest_value: Optional[float] = None
    for kind in ANOMALY_FEATURE_KINDS:
        rows = await crud.list_sensor_readings(db, source_id=source_id, kind=kind, limit=1)
        if not rows:
            return AnomalyBySourceResult(
                source_id=source_id,
                kind="+".join(ANOMALY_FEATURE_KINDS),
                n_readings=0,
                model_loaded=ml_service.anomaly is not None,
            )
        feats.append(rows[0].value)
        if kind == "energy_kw":
            latest_value = rows[0].value
    y = ml_service.anomaly_score(feats)
    return AnomalyBySourceResult(
        source_id=source_id,
        kind="+".join(ANOMALY_FEATURE_KINDS),
        n_readings=len(feats),
        model_loaded=y is not None,
        anomaly_score=y,
        is_anomaly=(y is not None and y > 0.65),
        latest_value=latest_value,
    )


@router.post("/scenario/predict")
async def scenario_predict(req: ScenarioPredictRequest):
    feats = [
        req.solar_adoption_pct,
        req.ev_share_pct,
        req.hvac_setpoint_c,
        req.signal_timing_pct,
        req.outdoor_temp_c,
        req.occupancy_pct,
    ]
    y = ml_service.scenario_predict(feats)
    keys = [
        "grid_import_kwh",
        "solar_generation_kwh",
        "peak_load_kw",
        "avg_comfort",
        "avg_congestion",
        "co2_kg_per_day",
        "renewable_share_pct",
    ]
    return {"model_loaded": y is not None, "kpis": dict(zip(keys, y)) if y else None}
