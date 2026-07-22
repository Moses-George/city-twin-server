"""Multi-output Gradient Boosting surrogate mapping the 6 scenario levers to
7 KPIs. Replaces the physics simulator for very fast what-if sweeps."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

DATA = Path(__file__).parent / "data" / "scenarios.parquet"
ART = Path(__file__).parent / "artifacts"
ART.mkdir(exist_ok=True, parents=True)

FEATURES = ["solar_adoption_pct", "ev_share_pct", "hvac_setpoint_c",
            "signal_timing_pct", "outdoor_temp_c", "occupancy_pct"]
TARGETS = ["grid_import_kwh", "solar_generation_kwh", "peak_load_kw",
           "avg_comfort", "avg_congestion", "co2_kg_per_day", "renewable_share_pct"]


def main():
    df = pd.read_parquet(DATA)
    X = df[FEATURES].to_numpy()
    Y = df[TARGETS].to_numpy()
    Xtr, Xte, Ytr, Yte = train_test_split(X, Y, test_size=0.2, random_state=0)
    model = MultiOutputRegressor(
        GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, random_state=0)
    )
    model.fit(Xtr, Ytr)
    pred = model.predict(Xte)
    for i, t in enumerate(TARGETS):
        print(f"{t:24s}  MAE={mean_absolute_error(Yte[:, i], pred[:, i]):.3f}  "
              f"R²={r2_score(Yte[:, i], pred[:, i]):.3f}")
    joblib.dump(model, ART / "scenario_gbr.joblib")
    print(f"saved {ART/'scenario_gbr.joblib'}")


if __name__ == "__main__":
    main()