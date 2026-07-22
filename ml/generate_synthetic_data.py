"""Generate synthetic training data for all four models.

Writes CSV/parquet files under ml/data/. Uses the physics simulator to make
labels consistent with what the app will actually see.
"""

from __future__ import annotations
import os, math, random
from pathlib import Path
import numpy as np
import pandas as pd

from app.simulation import (
    default_district,
    _shape,
    _hvac_mult,
    SOLAR_SHAPE,
    TRAFFIC_SHAPE,
    run_simulation,
)
from app.schemas import ScenarioParams

random.seed(0)
np.random.seed(0)
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True, parents=True)


def gen_energy(n_days: int = 90) -> pd.DataFrame:
    """Per-building, per-hour energy log with weather + occupancy features."""
    buildings, _ = default_district()
    rows = []
    for _ in range(n_days):
        outdoor = np.random.normal(14, 8)
        occ = np.clip(np.random.normal(100, 15), 30, 130)
        hvac = float(np.random.choice([19, 20, 21, 22, 23, 24]))
        for b in buildings:
            area = b.width * b.depth * b.floors
            daily_base = (
                (b.base_kwh_per_m2 * area / 365)
                * (occ / 100)
                * _hvac_mult(hvac, outdoor)
            )
            shape = _shape(b.type)
            s_sum = sum(shape)
            for h in range(24):
                kw = daily_base * shape[h] / s_sum
                noisy = kw * np.random.normal(1.0, 0.06)
                rows.append(
                    {
                        "building_id": b.id,
                        "building_type": b.type,
                        "floors": b.floors,
                        "area_m2": area,
                        "outdoor_temp_c": outdoor,
                        "occupancy_pct": occ,
                        "hvac_setpoint_c": hvac,
                        "hour": h,
                        "kwh": max(0, noisy),
                    }
                )
    df = pd.DataFrame(rows)
    df.to_parquet(DATA / "energy.parquet", index=False)
    print(f"energy: {len(df)} rows -> {DATA/'energy.parquet'}")
    return df


def gen_traffic(n_days: int = 120) -> pd.DataFrame:
    """Per-road, per-hour vehicle counts. Seasonality + weekday effect + noise."""
    _, roads = default_district()
    rows = []
    for d in range(n_days):
        weekday = d % 7 < 5
        for r in roads:
            for h in range(24):
                base = r.base_vehicles_per_hour * TRAFFIC_SHAPE[h]
                mult = 1.0 if weekday else 0.7
                # weather random dip
                w = 0.9 if np.random.random() < 0.1 else 1.0
                veh = max(0, base * mult * w * np.random.normal(1.0, 0.08))
                rows.append({"day": d, "road_id": r.id, "hour": h, "vehicles": veh})
    df = pd.DataFrame(rows)
    df.to_parquet(DATA / "traffic.parquet", index=False)
    print(f"traffic: {len(df)} rows -> {DATA/'traffic.parquet'}")
    return df


def gen_sensor_anomalies(n: int = 20000) -> pd.DataFrame:
    """Multivariate sensor snapshots. Features: energy_kw, temp, occupancy, congestion.
    Injects ~2% anomalies."""
    rng = np.random.default_rng(42)
    normal = rng.multivariate_normal(
        mean=[300, 14, 100, 0.4],
        cov=[[80**2, 0, 0, 0], [0, 5**2, 0, 0], [0, 0, 12**2, 0], [0, 0, 0, 0.08**2]],
        size=int(n * 0.98),
    )
    anomalies = rng.uniform(
        low=[600, -20, 5, 0.9],
        high=[1200, 45, 200, 1.0],
        size=(int(n * 0.02), 4),
    )
    X = np.vstack([normal, anomalies])
    y = np.array([0] * len(normal) + [1] * len(anomalies))
    df = pd.DataFrame(X, columns=["energy_kw", "temp_c", "occupancy_pct", "congestion"])
    df["is_anomaly"] = y
    df = df.sample(frac=1.0, random_state=0).reset_index(drop=True)
    df.to_parquet(DATA / "sensor.parquet", index=False)
    print(f"sensor: {len(df)} rows -> {DATA/'sensor.parquet'}")
    return df


def gen_scenarios(n: int = 4000) -> pd.DataFrame:
    """Sample scenario params, run the physics simulator, record KPIs.
    This is what the surrogate regressor learns."""
    rng = np.random.default_rng(1)
    rows = []
    for _ in range(n):
        p = ScenarioParams(
            solar_adoption_pct=float(rng.uniform(0, 100)),
            ev_share_pct=float(rng.uniform(0, 100)),
            hvac_setpoint_c=float(rng.uniform(17, 25)),
            signal_timing_pct=float(rng.uniform(60, 140)),
            outdoor_temp_c=float(rng.uniform(-5, 35)),
            occupancy_pct=float(rng.uniform(40, 120)),
        )
        r = run_simulation(p)
        rows.append(
            {
                **p.model_dump(),
                "grid_import_kwh": r.kpis.grid_import_kwh,
                "solar_generation_kwh": r.kpis.solar_generation_kwh,
                "peak_load_kw": r.kpis.peak_load_kw,
                "avg_comfort": r.kpis.avg_comfort,
                "avg_congestion": r.kpis.avg_congestion,
                "co2_kg_per_day": r.kpis.co2_kg_per_day,
                "renewable_share_pct": r.kpis.renewable_share_pct,
            }
        )
    df = pd.DataFrame(rows)
    df.to_parquet(DATA / "scenarios.parquet", index=False)
    print(f"scenarios: {len(df)} rows -> {DATA/'scenarios.parquet'}")
    return df


if __name__ == "__main__":
    gen_energy()
    gen_traffic()
    gen_sensor_anomalies()
    gen_scenarios()
