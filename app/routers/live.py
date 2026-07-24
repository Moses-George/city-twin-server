"""WebSocket live-playback: the client sends a ScenarioParams JSON payload
once connected (and again any time it changes params), and the server
streams one HourlyPoint per tick so the 3D scene's clock and this can stay
in sync with server-computed KPIs instead of only the in-browser engine.
"""

from __future__ import annotations
import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ..schemas import ScenarioParams
from ..simulation import run_simulation

router = APIRouter(tags=["live"])

TICK_SECONDS = 1.5


@router.websocket("/ws/simulate")
async def ws_simulate(ws: WebSocket):
    await ws.accept()
    params = ScenarioParams()
    hour = 0
    try:
        while True:
            try:
                raw = await asyncio.wait_for(ws.receive_text(), timeout=TICK_SECONDS)
                payload = json.loads(raw)
                params = ScenarioParams(**payload)
                hour = 0  # restart the clock when the scenario changes
            except asyncio.TimeoutError:
                pass
            except (ValidationError, json.JSONDecodeError) as e:
                await ws.send_json({"error": str(e)})
                continue

            result = run_simulation(params)
            point = result.hourly[hour % 24]
            await ws.send_json(
                {
                    "hour": point.hour,
                    "demand_kw": point.demand_kw,
                    "solar_kw": point.solar_kw,
                    "net_kw": point.net_kw,
                    "traffic_veh": point.traffic_veh,
                    "kpis": result.kpis.model_dump(),
                }
            )
            hour += 1
    except WebSocketDisconnect:
        pass
