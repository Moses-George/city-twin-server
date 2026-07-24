from typing import List, Optional
from fastapi import APIRouter, Depends, Query
# from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_async_db
from ..schemas import SensorReadingCreate, SensorReadingOut
from .. import crud

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post("", response_model=SensorReadingOut)
async def ingest(reading: SensorReadingCreate, db: AsyncSession = Depends(get_async_db)):
    """Ingest one real (or simulated-as-real) sensor reading. This is the
    on-ramp for real data: point actual building meters / traffic counters /
    weather stations here, or replay a historical CSV through it, and the
    anomaly + forecasting endpoints start working against real history."""
    return await crud.create_sensor_reading(db, reading)


@router.post("/batch", response_model=List[SensorReadingOut])
async def ingest_batch(
    readings: List[SensorReadingCreate], db: AsyncSession = Depends(get_async_db)
):
    return [await crud.create_sensor_reading(db, r) for r in readings]


@router.get("", response_model=List[SensorReadingOut])
async def list_readings(
    source_id: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = Query(200, le=2000),
    db: AsyncSession = Depends(get_async_db),
):
    return await crud.list_sensor_readings(db, source_id=source_id, kind=kind, limit=limit)


@router.get("/{source_id}/latest", response_model=List[SensorReadingOut])
async def latest_for_source(
    source_id: str, n: int = Query(24, le=500), db: AsyncSession = Depends(get_async_db)
):
    return await crud.latest_readings_for_source(db, source_id, n)
