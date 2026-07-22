"""LSTM (PyTorch) predicting next-hour vehicles per road segment from last 24h.

Trains one shared model across roads. TorchScript-exported for fast serving.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

DATA = Path(__file__).parent / "data" / "traffic.parquet"
ART = Path(__file__).parent / "artifacts"
ART.mkdir(exist_ok=True, parents=True)

WINDOW = 24


def make_windows(df: pd.DataFrame):
    X, y = [], []
    for road, g in df.groupby("road_id"):
        g = g.sort_values(["day", "hour"])
        v = g["vehicles"].to_numpy(dtype=np.float32)
        for i in range(WINDOW, len(v)):
            X.append(v[i - WINDOW:i]); y.append(v[i])
    return np.stack(X)[:, :, None], np.array(y, dtype=np.float32)


class TrafficLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=32, num_layers=1, batch_first=True)
        self.head = nn.Linear(32, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :]).squeeze(-1)


def main():
    df = pd.read_parquet(DATA)
    X, y = make_windows(df)
    # normalize
    scale = float(y.max())
    X = X / scale; y = y / scale
    Xt = torch.tensor(X); yt = torch.tensor(y)
    n = len(Xt); ntr = int(n * 0.8)
    ds = TensorDataset(Xt[:ntr], yt[:ntr])
    dl = DataLoader(ds, batch_size=256, shuffle=True)
    model = TrafficLSTM()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.SmoothL1Loss()
    for epoch in range(8):
        total = 0.0
        for xb, yb in dl:
            opt.zero_grad()
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward(); opt.step()
            total += loss.item() * len(xb)
        print(f"epoch {epoch+1}  train_loss={total/ntr:.5f}")
    model.eval()
    with torch.no_grad():
        pred = model(Xt[ntr:]).numpy() * scale
    truth = yt[ntr:].numpy() * scale
    mae = float(np.mean(np.abs(pred - truth)))
    print(f"val MAE (vehicles/hour): {mae:.2f}")
    # Wrap so serving multiplies by scale internally
    class Serve(nn.Module):
        def __init__(self, m, s):
            super().__init__(); self.m = m; self.s = s
        def forward(self, x):
            return self.m(x / self.s) * self.s
    served = torch.jit.script(Serve(model, scale))
    served.save(str(ART / "traffic_lstm.pt"))
    print(f"saved {ART/'traffic_lstm.pt'} (scale={scale:.1f})")


if __name__ == "__main__":
    main()