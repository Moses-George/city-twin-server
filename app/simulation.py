"""Python mirror of the TypeScript simulation engine (src/twin/simulation.ts)."""

from __future__ import annotations
import math, random
from dataclasses import dataclass
from typing import List

from .schemas import (
    ScenarioParams,
    SimulationResult,
    BuildingResult,
    RoadResult,
    HourlyPoint,
    DistrictKpis,
)


@dataclass
class Building:
    id: str
    name: str
    type: str
    x: float
    z: float
    width: float
    depth: float
    floors: int
    base_kwh_per_m2: float
    has_solar_potential: bool


@dataclass
class Road:
    id: str
    name: str
    from_xz: tuple
    to_xz: tuple
    lanes: int
    base_vehicles_per_hour: int
    capacity: int
    has_signal: bool


INTENSITY = {"residential": 110, "office": 180, "retail": 220, "industrial": 320}
OFFICE_SHAPE = [
    0.2,
    0.2,
    0.2,
    0.2,
    0.2,
    0.3,
    0.5,
    0.8,
    1.0,
    1.0,
    1.0,
    0.95,
    0.9,
    1.0,
    1.0,
    1.0,
    0.9,
    0.7,
    0.4,
    0.3,
    0.25,
    0.22,
    0.2,
    0.2,
]
RESIDENTIAL_SHAPE = [
    0.4,
    0.35,
    0.32,
    0.3,
    0.3,
    0.4,
    0.7,
    0.9,
    0.7,
    0.55,
    0.5,
    0.5,
    0.55,
    0.55,
    0.55,
    0.6,
    0.75,
    0.95,
    1.0,
    1.0,
    0.9,
    0.75,
    0.6,
    0.5,
]
RETAIL_SHAPE = [
    0.15,
    0.1,
    0.1,
    0.1,
    0.1,
    0.15,
    0.25,
    0.4,
    0.6,
    0.85,
    1.0,
    1.0,
    1.0,
    1.0,
    1.0,
    1.0,
    0.95,
    0.85,
    0.7,
    0.5,
    0.3,
    0.2,
    0.18,
    0.15,
]
INDUSTRIAL_SHAPE = [
    0.6,
    0.55,
    0.5,
    0.5,
    0.55,
    0.7,
    0.9,
    1.0,
    1.0,
    1.0,
    1.0,
    1.0,
    0.95,
    1.0,
    1.0,
    1.0,
    0.9,
    0.75,
    0.65,
    0.6,
    0.6,
    0.6,
    0.6,
    0.6,
]
TRAFFIC_SHAPE = [
    0.15,
    0.1,
    0.08,
    0.07,
    0.08,
    0.15,
    0.35,
    0.7,
    1.0,
    0.85,
    0.65,
    0.6,
    0.65,
    0.7,
    0.72,
    0.75,
    0.85,
    1.0,
    0.9,
    0.65,
    0.45,
    0.35,
    0.25,
    0.18,
]
SOLAR_SHAPE = [max(0.0, math.exp(-(((h - 13) / 5) ** 2))) for h in range(24)]


def _shape(t: str):
    return {
        "office": OFFICE_SHAPE,
        "residential": RESIDENTIAL_SHAPE,
        "retail": RETAIL_SHAPE,
        "industrial": INDUSTRIAL_SHAPE,
    }[t]


def _hvac_mult(sp: float, out: float) -> float:
    return 1 + ((abs(sp - out) / 12) ** 2) * 0.6


def _comfort(sp: float, out: float) -> float:
    f1 = 1 - min(1.0, abs(sp - 21.5) / 5)
    f2 = 1 - min(1.0, abs(sp - out) / 25)
    return max(0.0, min(1.0, 0.5 * f1 + 0.5 * f2))


def _hash_rank(s: str) -> float:
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return (h % 1000) / 1000


def default_district():
    rng = random.Random(42)
    types = ["residential", "office", "retail", "industrial"]
    cols, rows, spacing = 5, 4, 40
    ox = -((cols - 1) * spacing) / 2
    oz = -((rows - 1) * spacing) / 2
    buildings: List[Building] = []
    idx = 0
    for r in range(rows):
        for c in range(cols):
            t = types[rng.randrange(len(types))]
            floors = (
                (1 + rng.randrange(2))
                if t == "industrial"
                else (
                    3 + rng.randrange(6) if t == "residential" else 2 + rng.randrange(8)
                )
            )
            buildings.append(
                Building(
                    id=f"B{idx+1}",
                    name=f"Block {chr(65+r)}{c+1}",
                    type=t,
                    x=ox + c * spacing,
                    z=oz + r * spacing,
                    width=26 if t == "industrial" else 18 + rng.random() * 6,
                    depth=22 if t == "industrial" else 16 + rng.random() * 6,
                    floors=floors,
                    base_kwh_per_m2=INTENSITY[t] * (0.9 + rng.random() * 0.2),
                    has_solar_potential=(
                        (rng.random() > 0.15)
                        if t != "industrial"
                        else (rng.random() > 0.5)
                    ),
                )
            )
            idx += 1
    hw = ((cols - 1) * spacing) / 2 + spacing
    hh = ((rows - 1) * spacing) / 2 + spacing
    roads = [
        Road("R1", "North Ave", (-hw, -hh), (hw, -hh), 2, 900, 1400, True),
        Road("R2", "South Ave", (-hw, hh), (hw, hh), 2, 1100, 1400, True),
        Road("R3", "West Blvd", (-hw, -hh), (-hw, hh), 2, 800, 1400, True),
        Road("R4", "East Blvd", (hw, -hh), (hw, hh), 2, 850, 1400, True),
        Road("R5", "Central St", (0, -hh), (0, hh), 1, 600, 900, False),
        Road("R6", "Cross A", (-hw, -20), (hw, -20), 1, 500, 900, False),
        Road("R7", "Cross B", (-hw, 20), (hw, 20), 1, 550, 900, False),
        Road("R8", "Link N", (-40, -hh), (-40, 0), 1, 350, 800, False),
        Road("R9", "Link S", (40, 0), (40, hh), 1, 380, 800, False),
        Road("R10", "Ring", (-hw, 0), (hw, 0), 1, 700, 1100, True),
    ]
    return buildings, roads


def run_simulation(p: ScenarioParams) -> SimulationResult:
    buildings, roads = default_district()
    b_results: List[BuildingResult] = []
    for b in buildings:
        area = b.width * b.depth * b.floors
        daily_base = (
            (b.base_kwh_per_m2 * area / 365)
            * (p.occupancy_pct / 100)
            * _hvac_mult(p.hvac_setpoint_c, p.outdoor_temp_c)
        )
        shape = _shape(b.type)
        s_sum = sum(shape)
        solar_active = (
            b.has_solar_potential and _hash_rank(b.id) < p.solar_adoption_pct / 100
        )
        solar_peak = area * 0.12 * 0.18 if solar_active else 0.0
        dk = sk = pk = 0.0
        for h in range(24):
            kw = daily_base * shape[h] / s_sum
            dk += kw
            sk += solar_peak * SOLAR_SHAPE[h]
            pk = max(pk, kw)
        b_results.append(
            BuildingResult(
                id=b.id,
                daily_kwh=dk,
                solar_kwh=sk,
                net_kwh=max(0.0, dk - sk),
                comfort_score=_comfort(p.hvac_setpoint_c, p.outdoor_temp_c),
                peak_load_kw=pk,
            )
        )
    r_results: List[RoadResult] = []
    for r in roads:
        demand = r.base_vehicles_per_hour * (p.occupancy_pct / 100)
        eff = r.capacity * (p.signal_timing_pct / 100 if r.has_signal else 1)
        throughput = min(demand, eff)
        r_results.append(
            RoadResult(
                id=r.id,
                demand=demand,
                throughput=throughput,
                congestion=min(1.0, demand / max(1.0, eff)),
                co2_kg_per_hour=throughput * 0.3 * 0.22 * (1 - p.ev_share_pct / 100),
            )
        )
    hourly: List[HourlyPoint] = []
    for h in range(24):
        demand_kw = 0.0
        solar_kw = 0.0
        for i, b in enumerate(buildings):
            area = b.width * b.depth * b.floors
            daily_base = (
                (b.base_kwh_per_m2 * area / 365)
                * (p.occupancy_pct / 100)
                * _hvac_mult(p.hvac_setpoint_c, p.outdoor_temp_c)
            )
            shape = _shape(b.type)
            s_sum = sum(shape)
            demand_kw += daily_base * shape[h] / s_sum
            br = b_results[i]
            sp = br.solar_kwh / sum(SOLAR_SHAPE) if br.solar_kwh > 0 else 0
            solar_kw += sp * SOLAR_SHAPE[h]
        traffic = sum(
            r.base_vehicles_per_hour * (p.occupancy_pct / 100) * TRAFFIC_SHAPE[h]
            for r in roads
        )
        hourly.append(
            HourlyPoint(
                hour=h,
                demand_kw=demand_kw,
                solar_kw=solar_kw,
                net_kw=max(0.0, demand_kw - solar_kw),
                traffic_veh=traffic,
            )
        )
    total = sum(x.daily_kwh for x in b_results)
    solar = sum(x.solar_kwh for x in b_results)
    grid = sum(x.net_kwh for x in b_results)
    peak = max(pp.net_kw for pp in hourly)
    kpis = DistrictKpis(
        total_energy_kwh=total,
        grid_import_kwh=grid,
        solar_generation_kwh=solar,
        peak_load_kw=peak,
        avg_comfort=sum(x.comfort_score for x in b_results) / len(b_results),
        avg_congestion=sum(x.congestion for x in r_results) / len(r_results),
        co2_kg_per_day=sum(x.co2_kg_per_hour for x in r_results) * 12 + grid * 0.25,
        ev_grid_load_kwh=(p.ev_share_pct / 100)
        * sum(x.throughput for x in r_results)
        * 0.06,
        renewable_share_pct=min(100.0, (solar / total * 100) if total > 0 else 0),
    )
    return SimulationResult(
        buildings=b_results, roads=r_results, kpis=kpis, hourly=hourly
    )
