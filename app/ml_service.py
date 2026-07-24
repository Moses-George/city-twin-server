"""Loads trained ML artifacts if present. Endpoints degrade gracefully."""

from __future__ import annotations
from pathlib import Path
from typing import Optional
import joblib
import numpy as np
from .core.config import settings


class MLService:
    def __init__(self):
        self.artifacts_dir = Path(settings.ml_artifacts_dir)
        self.energy = self._try_load("energy_xgb.joblib")
        self.energy_features = self._try_load("energy_features.joblib")
        self.anomaly = self._try_load("anomaly_iforest.joblib")
        self.scenario_reg = self._try_load("scenario_gbr.joblib")
        self._traffic = None

    def _try_load(self, name: str):
        p = self.artifacts_dir / name
        if p.exists():
            try:
                return joblib.load(p)
            except Exception:
                return None
        return None

    def energy_predict(self, features: dict) -> Optional[float]:
        if not self.energy or not self.energy_features:
            return None
        row = [features.get(k, 0.0) for k in self.energy_features]
        return float(self.energy.predict(np.array([row]))[0])

    def anomaly_score(self, feats: list[float]) -> Optional[float]:
        if not self.anomaly:
            return None
        s = float(self.anomaly.score_samples(np.array([feats]))[0])
        return -s

    def scenario_predict(self, feats: list[float]) -> Optional[list[float]]:
        if not self.scenario_reg:
            return None
        pred = self.scenario_reg.predict(np.array([feats]))[0]
        return [float(x) for x in np.atleast_1d(pred)]

    def traffic_predict(self, history: list[float]) -> Optional[float]:
        try:
            import torch

            if self._traffic is None:
                p = self.artifacts_dir / "traffic_lstm.pt"
                if not p.exists():
                    return None
                self._traffic = torch.jit.load(str(p))
                self._traffic.eval()
            x = torch.tensor(history, dtype=torch.float32).view(1, len(history), 1)
            with torch.no_grad():
                y = self._traffic(x).item()
            return float(y)
        except Exception:
            return None


ml_service = MLService()
