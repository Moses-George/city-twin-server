from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ScenarioParams(BaseModel):
    solar_adoption_pct: float = Field(25, ge=0, le=100)
    ev_share_pct: float = Field(15, ge=0, le=100)
    hvac_setpoint_c: float = Field(21, ge=16, le=26)
    signal_timing_pct: float = Field(100, ge=50, le=150)
    outdoor_temp_c: float = Field(14, ge=-5, le=35)
    occupancy_pct: float = Field(100, ge=30, le=120)


class ScenarioCreate(ScenarioParams):
    name: str


class ScenarioOut(ScenarioCreate):
    id: int

    class Config:
        from_attributes = True


class BuildingResult(BaseModel):
    id: str
    daily_kwh: float
    solar_kwh: float
    net_kwh: float
    comfort_score: float
    peak_load_kw: float


class RoadResult(BaseModel):
    id: str
    demand: float
    throughput: float
    congestion: float
    co2_kg_per_hour: float


class HourlyPoint(BaseModel):
    hour: int
    demand_kw: float
    solar_kw: float
    net_kw: float
    traffic_veh: float


class DistrictKpis(BaseModel):
    total_energy_kwh: float
    grid_import_kwh: float
    solar_generation_kwh: float
    peak_load_kw: float
    avg_comfort: float
    avg_congestion: float
    co2_kg_per_day: float
    ev_grid_load_kwh: float
    renewable_share_pct: float


class SimulationResult(BaseModel):
    buildings: List[BuildingResult]
    roads: List[RoadResult]
    kpis: DistrictKpis
    hourly: List[HourlyPoint]


class EnergyPredictRequest(BaseModel):
    building_type: str
    floors: int
    area_m2: float
    outdoor_temp_c: float
    occupancy_pct: float
    hvac_setpoint_c: float
    hour: int


class TrafficPredictRequest(BaseModel):
    road_id: str
    history: List[float] = Field(..., description="Last 24 hourly vehicle counts")


class AnomalyScoreRequest(BaseModel):
    features: List[float]


class ScenarioPredictRequest(ScenarioParams):
    pass


class SensorReadingCreate(BaseModel):
    source_id: str = Field(..., description="Building or road id, e.g. B3 or R5")
    kind: str = Field(..., description="e.g. 'energy_kwh', 'traffic_count', 'temp_c'")
    value: float
    ts: Optional[datetime] = None


class SensorReadingOut(SensorReadingCreate):
    id: int
    ts: datetime

    class Config:
        from_attributes = True


class AnomalyBySourceResult(BaseModel):
    source_id: str
    kind: str
    n_readings: int
    model_loaded: bool
    anomaly_score: Optional[float] = None
    is_anomaly: Optional[bool] = None
    latest_value: Optional[float] = None