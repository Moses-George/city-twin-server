"""Seeds the buildings/roads tables from the deterministic generator the
first time the API is asked for district data. Keeps `/district` backed by
real persisted rows (so scenarios, sensor readings, and future edits can
reference stable foreign data) instead of regenerating in memory on every
request.
"""

from __future__ import annotations
from sqlalchemy.orm import Session

from . import models
from .simulation import default_district


def ensure_district_seeded(db: Session) -> None:
    if db.query(models.Building).first() is not None:
        return
    buildings, roads = default_district()
    for b in buildings:
        db.add(
            models.Building(
                id=b.id,
                name=b.name,
                type=b.type,
                x=b.x,
                z=b.z,
                width=b.width,
                depth=b.depth,
                floors=b.floors,
                base_kwh_per_m2=b.base_kwh_per_m2,
                has_solar_potential=b.has_solar_potential,
            )
        )
    for r in roads:
        db.add(
            models.Road(
                id=r.id,
                name=r.name,
                from_x=r.from_xz[0],
                from_z=r.from_xz[1],
                to_x=r.to_xz[0],
                to_z=r.to_xz[1],
                lanes=r.lanes,
                base_vehicles_per_hour=r.base_vehicles_per_hour,
                capacity=r.capacity,
                has_signal=r.has_signal,
            )
        )
    db.commit()


def reseed_district(db: Session) -> None:
    db.query(models.Building).delete()
    db.query(models.Road).delete()
    db.commit()
    ensure_district_seeded(db)
