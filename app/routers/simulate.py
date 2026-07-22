from fastapi import APIRouter
from ..schemas import ScenarioParams, SimulationResult
from ..simulation import run_simulation

router = APIRouter(prefix="/simulate", tags=["simulate"])


@router.post("", response_model=SimulationResult)
def simulate(params: ScenarioParams) -> SimulationResult:
    return run_simulation(params)