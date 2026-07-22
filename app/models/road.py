from sqlalchemy import String, Float, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel

class Road(BaseModel):
    __tablename__ = "roads"
    name: Mapped[str] = mapped_column(String)
    from_x: Mapped[float] = mapped_column(Float)
    from_z: Mapped[float] = mapped_column(Float)
    to_x: Mapped[float] = mapped_column(Float)
    to_z: Mapped[float] = mapped_column(Float)
    lanes: Mapped[int] = mapped_column(Integer)
    base_vehicles_per_hour: Mapped[int] = mapped_column(Integer)
    capacity: Mapped[int] = mapped_column(Integer)
    has_signal: Mapped[bool] = mapped_column(Boolean)