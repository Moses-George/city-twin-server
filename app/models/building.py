from sqlalchemy import String, Float, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel

class Building(BaseModel):
    __tablename__ = "buildings"
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    x: Mapped[float] = mapped_column(Float)
    z: Mapped[float] = mapped_column(Float)
    width: Mapped[float] = mapped_column(Float)
    depth: Mapped[float] = mapped_column(Float)
    floors: Mapped[int] = mapped_column(Integer)
    base_kwh_per_m2: Mapped[float] = mapped_column(Float)
    has_solar_potential: Mapped[bool] = mapped_column(Boolean)