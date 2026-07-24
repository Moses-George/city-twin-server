from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud
from ..core.database import get_async_db
from ..seed import ensure_district_seeded, reseed_district
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/district", tags=["district"])


@router.get("")
async def get_district(db: AsyncSession = Depends(get_async_db)):
    ensure_district_seeded(db)
    buildings = await crud.list_buildings(db)
    roads = await crud.list_roads(db)
    return {
        "buildings": [
            {
                "id": b.id,
                "name": b.name,
                "type": b.type,
                "x": b.x,
                "z": b.z,
                "width": b.width,
                "depth": b.depth,
                "floors": b.floors,
                "base_kwh_per_m2": b.base_kwh_per_m2,
                "has_solar_potential": b.has_solar_potential,
            }
            for b in buildings
        ],
        "roads": [
            {
                "id": r.id,
                "name": r.name,
                "from": [r.from_x, r.from_z],
                "to": [r.to_x, r.to_z],
                "lanes": r.lanes,
                "base_vehicles_per_hour": r.base_vehicles_per_hour,
                "capacity": r.capacity,
                "has_signal": r.has_signal,
            }
            for r in roads
        ],
    }


@router.post("/reseed")
async def reseed(db: AsyncSession = Depends(get_async_db)):
    """Wipes and regenerates the district. Use if you change the generator
    seed/layout logic in simulation.py and want persisted rows to catch up."""
    await reseed_district(db)
    return {"status": "reseeded"}
