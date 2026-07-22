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
from sqlalchemy.orm import Session
from sqlalchemy import delete
from . import models, schemas


def list_scenarios(db: Session):
    return db.query(models.Scenario).order_by(models.Scenario.created_at.desc()).all()


def get_scenario(db: Session, scenario_id: int) -> Optional[models.Scenario]:
    return db.get(models.Scenario, scenario_id)


def create_scenario(db: Session, s: schemas.ScenarioCreate) -> models.Scenario:
    row = models.Scenario(**s.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row


def delete_scenario(db: Session, scenario_id: int) -> bool:
    row = db.get(models.Scenario, scenario_id)
    if row is None:
        return False
    db.delete(row); db.commit()
    return True


def list_buildings(db: Session):
    return db.query(models.Building).all()


def list_roads(db: Session):
    return db.query(models.Road).all()


def create_sensor_reading(db: Session, r: schemas.SensorReadingCreate) -> models.SensorReading:
    row = models.SensorReading(
        source_id=r.source_id, kind=r.kind,
        ts=r.ts or datetime.utcnow(), value=r.value,
    )
    db.add(row); db.commit(); db.refresh(row)
    return row


def list_sensor_readings(
    db: Session, source_id: Optional[str] = None, kind: Optional[str] = None,
    limit: int = 200,
):
    q = db.query(models.SensorReading)
    if source_id:
        q = q.filter(models.SensorReading.source_id == source_id)
    if kind:
        q = q.filter(models.SensorReading.kind == kind)
    return q.order_by(models.SensorReading.ts.desc()).limit(limit).all()


def latest_readings_for_source(db: Session, source_id: str, n: int = 24):
    rows = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.source_id == source_id)
        .order_by(models.SensorReading.ts.desc())
        .limit(n)
        .all()
    )
    return list(reversed(rows))


def prune_sensor_readings(db: Session, older_than_days: int = 90) -> int:
    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    result = db.execute(
        delete(models.SensorReading).where(models.SensorReading.ts < cutoff)
    )
    db.commit()
    return result.rowcount or 0