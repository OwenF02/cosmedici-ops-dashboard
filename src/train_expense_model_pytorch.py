"""
Sprint 3 — PyTorch expense classifier (portfolio comparison).

Uses the same feature pipeline as the Keras version (src/text_embeddings.py:
pretrained sentence embeddings over vendor_name+description, concatenated
with amount/month/payment_method) so the two deep learning approaches are
a fair architecture comparison, not a feature-engineering comparison.

This is one of three candidates compared in Sprint 3 - see
src/train_expense_model_baseline.py for the classical baseline and
src/train_expense_model_keras.py for the Keras version. Whichever wins on
macro F1 becomes the production model; see docs/decision_log.md.

Usage (all flags optional — defaults match the real business paths):
    python src/train_expense_model_pytorch.py
    python src/train_expense_model_pytorch.py --data-path data/expenses_sample.csv --model-out models/public/pytorch_demo_model.pt
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from text_embeddings import build_feature_matrix

TARGET_COL = "category_for_model"
RANDOM_STATE = 42
DEFAULT_DATA_PATH = Path("data/private/cleaned_expenses.csv")
DEFAULT_MODEL_OUT = Path("models/private/expense_pytorch.pt")
DEFAULT_METRICS_OUT = Path("metrics/pytorch_metrics.json")

torch.manual_seed(RANDOM_STATE)


class ExpenseMLP(nn.Module):
    """A small MLP: embedding+structured features -> hidden layers -> category."""

    def __init__(self, input_dim: int, n_classes: int, hidden_sizes=(128, 64), dropout=0.3):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_sizes:
            layers += [nn.Linear(prev_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout)]
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, n_classes))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


def load_and_prepare(data_path: Path) -> pd.DataFrame:
    df = pd.read_csv(data_path, parse_dates=["date"])
    if TARGET_COL not in df.columns:
        df[TARGET_COL] = df["category"]
    df["month"] = df["date"].dt.month.astype(str)
    df["vendor_name"] = df["vendor_name"].fillna("")
    df["description"] = df["description"].fillna("")
    df["payment_method"] = df["payment_method"].fillna("Unknown")
    return df


def train_model(model, X_train, y_train, class_weights, epochs=60, lr=1e-3, batch_size=32):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    dataset = torch.utils.data.TensorDataset(X_train, y_train)
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for xb, yb in loader:
            optimizer.zero_grad()
            output = model(xb)
            loss = criterion(output, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * xb.size(0)
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"  epoch {epoch + 1}/{epochs} - loss: {total_loss / len(dataset):.4f}")

    return model


def evaluate(model, X_test, y_test, label_names) -> dict:
    model.eval()
    with torch.no_grad():
        logits = model(X_test)
        y_pred = torch.argmax(logits, dim=1).numpy()
    y_true = y_test.numpy()

    report = classification_report(
        y_true, y_pred, labels=list(range(len(label_names))),
        target_names=label_names, output_dict=True, zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(label_names))))
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "labels": label_names,
    }


def main():
    parser = argparse.ArgumentParser(description="Train the PyTorch expense classifier.")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--model-out", type=Path, default=DEFAULT_MODEL_OUT)
    parser.add_argument("--metrics-out", type=Path, default=DEFAULT_METRICS_OUT)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--epochs", type=int, default=60)
    args = parser.parse_args()

    if not args.data_path.exists():
        raise FileNotFoundError(
            f"No file found at {args.data_path}. Run this from the project root "
            f"(cd to cosmedici-ops-dashboard first), or pass --data-path explicitly."
        )

    print("Loading data and building embeddings (this downloads the pretrained "
          "sentence-transformers model on first run, and can take a minute)...")
    df = load_and_prepare(args.data_path)

    label_encoder = LabelEncoder()
    y_all = label_encoder.fit_transform(df[TARGET_COL])
    label_names = list(label_encoder.classes_)

    X_all, feature_names, month_categories, payment_categories, amount_scaler = build_feature_matrix(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all, test_size=args.test_size, random_state=RANDOM_STATE, stratify=y_all
    )

    # Inverse-frequency class weights, same rationale as class_weight="balanced"
    # in the classical baseline - don't let common categories drown out rare ones.
    class_counts = np.bincount(y_train, minlength=len(label_names))
    class_weights = torch.tensor(len(y_train) / (len(label_names) * np.maximum(class_counts, 1)), dtype=torch.float32)

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)
    y_test_t = torch.tensor(y_test, dtype=torch.long)

    model = ExpenseMLP(input_dim=X_all.shape[1], n_classes=len(label_names))
    print(f"Training MLP ({X_all.shape[1]} input features -> {len(label_names)} categories)...")
    train_model(model, X_train_t, y_train_t, class_weights, epochs=args.epochs)

    metrics = evaluate(model, X_test_t, y_test_t, label_names)
    print(f"\naccuracy={metrics['accuracy']:.3f}  macro_f1={metrics['macro_f1']:.3f}  weighted_f1={metrics['weighted_f1']:.3f}")
    print("\nPer-category report:")
    for cat, stats in metrics["classification_report"].items():
        if cat in ("accuracy", "macro avg", "weighted avg"):
            continue
        print(f"  {cat}: precision={stats['precision']:.2f} recall={stats['recall']:.2f} f1={stats['f1-score']:.2f} support={int(stats['support'])}")

    args.model_out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "input_dim": X_all.shape[1],
            "n_classes": len(label_names),
            "label_names": label_names,
            "month_categories": month_categories,
            "payment_categories": payment_categories,
            "amount_mean": float(amount_scaler.mean_[0]),
            "amount_scale": float(amount_scaler.scale_[0]),
        },
        args.model_out,
    )
    print(f"\nSaved model -> {args.model_out}")

    if args.metrics_out:
        args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.metrics_out, "w") as f:
            json.dump(
                {"dataset_size": len(df), "n_train": len(X_train), "n_test": len(X_test), "results": metrics},
                f, indent=2, default=str,
            )
        print(f"Saved metrics -> {args.metrics_out}")


if __name__ == "__main__":
    main()
