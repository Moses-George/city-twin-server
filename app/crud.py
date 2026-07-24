# from sqlalchemy.orm import Session
# from . import models, schemas


# def list_scenarios(db: Session):
#     return db.query(models.Scenario).order_by(models.Scenario.created_at.desc()).all()


# def create_scenario(db: Session, s: schemas.ScenarioCreate) -> models.Scenario:
#     row = models.Scenario(**s.model_dump())
#     db.add(row); db.commit(); db.refresh(row)
#     return row


# def list_buildings(db: Session):
#     return db.query(models.Building).all()


# def list_roads(db: Session):
#     return db.query(models.Road).all()

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import delete
from . import models, schemas


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from sqlalchemy.orm import selectinload


async def list_scenarios(db: AsyncSession):
    result = await db.execute(
        select(models.Scenario).order_by(desc(models.Scenario.created_at))
    )
    return result.scalars().all()


async def get_scenario(db: AsyncSession, scenario_id: str) -> Optional[models.Scenario]:
    result = await db.execute(
        select(models.Scenario).filter(models.Scenario.id == scenario_id)
    )
    return result.scalar_one_or_none()


async def create_scenario(
    db: AsyncSession, s: schemas.ScenarioCreate
) -> models.Scenario:
    row = models.Scenario(**s.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_scenario(db: AsyncSession, scenario_id: str) -> bool:
    result = await db.execute(
        delete(models.Scenario).where(models.Scenario.id == scenario_id)
    )
    await db.commit()
    return result.rowcount > 0


async def list_buildings(db: AsyncSession):
    result = await db.execute(select(models.Building))
    return result.scalars().all()


async def list_roads(db: AsyncSession):
    result = await db.execute(select(models.Road))
    return result.scalars().all()


async def create_sensor_reading(
    db: AsyncSession, r: schemas.SensorReadingCreate
) -> models.SensorReading:
    row = models.SensorReading(
        source_id=r.source_id,
        kind=r.kind,
        ts=r.ts or datetime.utcnow(),
        value=r.value,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_sensor_readings(
    db: AsyncSession,
    source_id: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = 200,
):
    query = select(models.SensorReading)
    if source_id:
        query = query.filter(models.SensorReading.source_id == source_id)
    if kind:
        query = query.filter(models.SensorReading.kind == kind)
    query = query.order_by(desc(models.SensorReading.ts)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def latest_readings_for_source(db: AsyncSession, source_id: str, n: int = 24):
    query = (
        select(models.SensorReading)
        .filter(models.SensorReading.source_id == source_id)
        .order_by(desc(models.SensorReading.ts))
        .limit(n)
    )
    result = await db.execute(query)
    rows = result.scalars().all()
    return list(reversed(rows))


async def prune_sensor_readings(db: AsyncSession, older_than_days: int = 90) -> int:
    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    result = await db.execute(
        delete(models.SensorReading).where(models.SensorReading.ts < cutoff)
    )
    await db.commit()
    return result.rowcount or 0
