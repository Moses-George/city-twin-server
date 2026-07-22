from datetime import datetime
from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class Scenario(BaseModel):
    __tablename__ = "scenarios"
    name: Mapped[str] = mapped_column(String, unique=True)
    solar_adoption_pct: Mapped[float] = mapped_column(Float)
    ev_share_pct: Mapped[float] = mapped_column(Float)
    hvac_setpoint_c: Mapped[float] = mapped_column(Float)
    signal_timing_pct: Mapped[float] = mapped_column(Float)
    outdoor_temp_c: Mapped[float] = mapped_column(Float)
    occupancy_pct: Mapped[float] = mapped_column(Float)