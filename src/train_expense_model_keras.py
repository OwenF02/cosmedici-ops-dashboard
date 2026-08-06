"""
Sprint 3 — Keras expense classifier (portfolio comparison).

Uses the same feature pipeline as the PyTorch version (src/text_embeddings.py:
pretrained sentence embeddings over vendor_name+description, concatenated
with amount/month/payment_method) so the two deep learning approaches are
a fair architecture comparison, not a feature-engineering comparison.

This is one of three candidates compared in Sprint 3 - see
src/train_expense_model_baseline.py for the classical baseline and
src/train_expense_model_pytorch.py for the PyTorch version. Whichever
wins on macro F1 becomes the production model; see docs/decision_log.md.

Usage (all flags optional — defaults match the real business paths):
    python src/train_expense_model_keras.py
    python src/train_expense_model_keras.py --data-path data/expenses_sample.csv --model-out models/public/keras_demo_model.keras
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from text_embeddings import build_feature_matrix

TARGET_COL = "category_for_model"
RANDOM_STATE = 42
DEFAULT_DATA_PATH = Path("data/private/cleaned_expenses.csv")
DEFAULT_MODEL_OUT = Path("models/private/expense_keras.keras")
DEFAULT_METRICS_OUT = Path("metrics/keras_metrics.json")
DEFAULT_LABELS_OUT = Path("models/private/expense_keras_labels.json")

tf.random.set_seed(RANDOM_STATE)


def build_model(input_dim: int, n_classes: int) -> tf.keras.Model:
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(input_dim,)),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(n_classes, activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def load_and_prepare(data_path: Path) -> pd.DataFrame:
    df = pd.read_csv(data_path, parse_dates=["date"])
    if TARGET_COL not in df.columns:
        df[TARGET_COL] = df["category"]
    df["month"] = df["date"].dt.month.astype(str)
    df["vendor_name"] = df["vendor_name"].fillna("")
    df["description"] = df["description"].fillna("")
    df["payment_method"] = df["payment_method"].fillna("Unknown")
    return df


def evaluate(model, X_test, y_test, label_names) -> dict:
    probs = model.predict(X_test, verbose=0)
    y_pred = np.argmax(probs, axis=1)

    report = classification_report(
        y_test, y_pred, labels=list(range(len(label_names))),
        target_names=label_names, output_dict=True, zero_division=0,
    )
    cm = confusion_matrix(y_test, y_pred, labels=list(range(len(label_names))))
    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "macro_f1": f1_score(y_test, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_test, y_pred, average="weighted", zero_division=0),
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "labels": label_names,
    }


def main():
    parser = argparse.ArgumentParser(description="Train the Keras expense classifier.")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--model-out", type=Path, default=DEFAULT_MODEL_OUT)
    parser.add_argument("--metrics-out", type=Path, default=DEFAULT_METRICS_OUT)
    parser.add_argument("--labels-out", type=Path, default=DEFAULT_LABELS_OUT)
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

    # Inverse-frequency class weights - same rationale as class_weight="balanced"
    # in the classical baseline and the weighted loss in the PyTorch version.
    class_counts = np.bincount(y_train, minlength=len(label_names))
    class_weight = {
        i: len(y_train) / (len(label_names) * max(count, 1))
        for i, count in enumerate(class_counts)
    }

    model = build_model(input_dim=X_all.shape[1], n_classes=len(label_names))
    print(f"Training MLP ({X_all.shape[1]} input features -> {len(label_names)} categories)...")
    model.fit(
        X_train, y_train,
        epochs=args.epochs,
        batch_size=32,
        class_weight=class_weight,
        verbose=2,
    )

    metrics = evaluate(model, X_test, y_test, label_names)
    print(f"\naccuracy={metrics['accuracy']:.3f}  macro_f1={metrics['macro_f1']:.3f}  weighted_f1={metrics['weighted_f1']:.3f}")
    print("\nPer-category report:")
    for cat, stats in metrics["classification_report"].items():
        if cat in ("accuracy", "macro avg", "weighted avg"):
            continue
        print(f"  {cat}: precision={stats['precision']:.2f} recall={stats['recall']:.2f} f1={stats['f1-score']:.2f} support={int(stats['support'])}")

    args.model_out.parent.mkdir(parents=True, exist_ok=True)
    model.save(args.model_out)
    print(f"\nSaved model -> {args.model_out}")

    args.labels_out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.labels_out, "w") as f:
        json.dump(
            {
                "label_names": label_names,
                "month_categories": month_categories,
                "payment_categories": payment_categories,
                "amount_mean": float(amount_scaler.mean_[0]),
                "amount_scale": float(amount_scaler.scale_[0]),
            },
            f, indent=2,
        )
    print(f"Saved label/feature metadata -> {args.labels_out}")

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
