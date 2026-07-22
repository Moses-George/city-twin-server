from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from ..schemas import SensorReadingCreate, SensorReadingOut
from .. import crud

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post("", response_model=SensorReadingOut)
def ingest(reading: SensorReadingCreate, db: Session = Depends(get_db)):
    """Ingest one real (or simulated-as-real) sensor reading. This is the
    on-ramp for real data: point actual building meters / traffic counters /
    weather stations here, or replay a historical CSV through it, and the
    anomaly + forecasting endpoints start working against real history."""
    return crud.create_sensor_reading(db, reading)


@router.post("/batch", response_model=List[SensorReadingOut])
def ingest_batch(readings: List[SensorReadingCreate], db: Session = Depends(get_db)):
    return [crud.create_sensor_reading(db, r) for r in readings]


@router.get("", response_model=List[SensorReadingOut])
def list_readings(
    source_id: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = Query(200, le=2000),
    db: Session = Depends(get_db),
):
    return crud.list_sensor_readings(db, source_id=source_id, kind=kind, limit=limit)


@router.get("/{source_id}/latest", response_model=List[SensorReadingOut])
def latest_for_source(
    source_id: str, n: int = Query(24, le=500), db: Session = Depends(get_db)
):
    return crud.latest_readings_for_source(db, source_id, n)
