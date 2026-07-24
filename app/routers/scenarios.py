from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_async_db
from ..schemas import ScenarioCreate, ScenarioOut
from .. import crud
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=List[ScenarioOut])
async def list_(db: Session = Depends(get_async_db)):
    return await crud.list_scenarios(db)


@router.get("/{scenario_id}", response_model=ScenarioOut)
async def get_one(scenario_id: str, db: AsyncSession = Depends(get_async_db)):
    row = await crud.get_scenario(db, scenario_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return row


@router.post("", response_model=ScenarioOut)
async def create(s: ScenarioCreate, db: AsyncSession = Depends(get_async_db)):
    # Query for existing scenario with the same name
    result = await db.execute(
        select(crud.models.Scenario).filter(crud.models.Scenario.name == s.name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=409, 
            detail="A scenario with this name already exists"
        )
    
    return await crud.create_scenario(db, s)


@router.delete("/{scenario_id}", status_code=204)
async def delete(scenario_id: str, db: AsyncSession = Depends(get_async_db)):
    ok = await crud.delete_scenario(db, scenario_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return None
