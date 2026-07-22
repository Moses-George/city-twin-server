from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from ..schemas import ScenarioCreate, ScenarioOut
from .. import crud

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=List[ScenarioOut])
def list_(db: Session = Depends(get_db)):
    return crud.list_scenarios(db)


@router.post("", response_model=ScenarioOut)
def create(s: ScenarioCreate, db: Session = Depends(get_db)):
    return crud.create_scenario(db, s)