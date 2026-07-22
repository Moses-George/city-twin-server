"""XGBoost hourly kWh forecaster per building.

Features: building type one-hot, floors, area, outdoor temp, occupancy,
HVAC setpoint, hour-of-day (cyclical).
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor 

DATA = Path(__file__).parent / "data" / "energy.parquet"
ART = Path(__file__).parent / "artifacts"
ART.mkdir(exist_ok=True, parents=True)


def main():
    df = pd.read_parquet(DATA)
    # one-hot type
    for t in ("residential", "office", "retail", "industrial"):
        df[f"type_{t}"] = (df["building_type"] == t).astype(float)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    features = [
        "floors",
        "area_m2",
        "outdoor_temp_c",
        "occupancy_pct",
        "hvac_setpoint_c",
        "hour",
        "hour_sin",
        "hour_cos",
        "type_residential",
        "type_office",
        "type_retail",
        "type_industrial",
    ]
    X = df[features].to_numpy()
    y = df["kwh"].to_numpy()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0)
    model = XGBRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.06,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=0,
    )
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    print(f"MAE={mean_absolute_error(yte, pred):.3f}  R²={r2_score(yte, pred):.3f}")
    joblib.dump(model, ART / "energy_xgb.joblib")
    joblib.dump(features, ART / "energy_features.joblib")
    print(f"saved {ART/'energy_xgb.joblib'}")


if __name__ == "__main__":
    main()
