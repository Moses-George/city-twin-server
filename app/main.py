from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import district, live, ml, scenarios, sensors, simulate
from core.config import settings

app = FastAPI(
    title="CityTwin API",
    version="0.1.0",
    description="Integrated smart-city digital twin — energy, traffic, buildings.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(district.router)
app.include_router(simulate.router)
app.include_router(scenarios.router)
app.include_router(ml.router)
app.include_router(sensors.router)
app.include_router(live.router)


@app.get("/")
def root():
    return {"name": "CityTwin API", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}
