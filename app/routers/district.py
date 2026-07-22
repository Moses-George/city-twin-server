from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud
from core.database import get_db
from ..seed import ensure_district_seeded, reseed_district

router = APIRouter(prefix="/district", tags=["district"])


@router.get("")
def get_district(db: Session = Depends(get_db)):
    ensure_district_seeded(db)
    buildings = crud.list_buildings(db)
    roads = crud.list_roads(db)
    return {
        "buildings": [
            {
                "id": b.id, "name": b.name, "type": b.type,
                "x": b.x, "z": b.z, "width": b.width, "depth": b.depth,
                "floors": b.floors, "base_kwh_per_m2": b.base_kwh_per_m2,
                "has_solar_potential": b.has_solar_potential,
            }
            for b in buildings
        ],
        "roads": [
            {
                "id": r.id, "name": r.name,
                "from": [r.from_x, r.from_z], "to": [r.to_x, r.to_z],
                "lanes": r.lanes, "base_vehicles_per_hour": r.base_vehicles_per_hour,
                "capacity": r.capacity, "has_signal": r.has_signal,
            }
            for r in roads
        ],
    }


@router.post("/reseed")
def reseed(db: Session = Depends(get_db)):
    """Wipes and regenerates the district. Use if you change the generator
    seed/layout logic in simulation.py and want persisted rows to catch up."""
    reseed_district(db)
    return {"status": "reseeded"}