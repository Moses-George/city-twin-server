"""Isolation Forest on 4-D sensor snapshots. Reports precision/recall on
injected anomalies (unsupervised — labels used only for evaluation)."""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report

DATA = Path(__file__).parent / "data" / "sensor.parquet"
ART = Path(__file__).parent / "artifacts"
ART.mkdir(exist_ok=True, parents=True)


def main():
    df = pd.read_parquet(DATA)
    X = df[["energy_kw", "temp_c", "occupancy_pct", "congestion"]].to_numpy()
    y = df["is_anomaly"].to_numpy()
    model = IsolationForest(
        n_estimators=200, contamination=0.02, random_state=0, n_jobs=-1,
    )
    model.fit(X)
    pred = (model.predict(X) == -1).astype(int)
    print(classification_report(y, pred, target_names=["normal", "anomaly"]))
    joblib.dump(model, ART / "anomaly_iforest.joblib")
    print(f"saved {ART/'anomaly_iforest.joblib'}")


if __name__ == "__main__":
    main()