"""
predict_expenses.py

Model-switchable inference for the expense classifier. Supports three
interchangeable trained models:

  - baseline  (default) -- classical TF-IDF + Logistic/RandomForest pipeline
  - pytorch              -- ExpenseMLP over sentence-transformer embeddings
  - keras                -- Keras Sequential MLP over the same embeddings

All three were trained on the same feature contract (vendor_name,
description, amount, month, payment_method -> category_for_model), so
switching models does not change how you call this script -- only which
saved artifact gets loaded.

Usage:
    python src/predict_expenses.py
    python src/predict_expenses.py --model pytorch
    python src/predict_expenses.py --model keras --input-csv data/private/new_expenses.csv
    python src/predict_expenses.py --model baseline --output-csv predictions.csv

Output is a CSV with the original rows plus two new columns:
    predicted_category, confidence  (confidence = model's own probability
    for the predicted class, 0-1)
"""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from text_embeddings import build_feature_matrix

# --- Default locations (all point at real, private, gitignored artifacts) ---
DEFAULT_INPUT_PATH = Path("data/private/cleaned_expenses.csv")
DEFAULT_OUTPUT_PATH = Path("predictions_output.csv")

DEFAULT_BASELINE_MODEL = Path("models/private/expense_baseline.pkl")
DEFAULT_PYTORCH_MODEL = Path("models/private/expense_pytorch.pt")
DEFAULT_KERAS_MODEL = Path("models/private/expense_keras.keras")
DEFAULT_KERAS_LABELS = Path("models/private/expense_keras_labels.json")

FEATURE_COLS = ["text_features", "amount", "month", "payment_method"]


def prepare_input_df(input_path: Path) -> pd.DataFrame:
    """Load a CSV and make sure it has the columns every model needs."""
    df = pd.read_csv(input_path)

    if "month" not in df.columns:
        if "date" not in df.columns:
            raise ValueError(
                "Input CSV needs either a 'month' column or a 'date' column "
                "(month is derived from date if missing)."
            )
        df["month"] = pd.to_datetime(df["date"]).dt.month

    # Trained encoders learned month as plain string categories ('1'..'12',
    # no zero-padding) -- normalize to that exact format regardless of
    # whether month came from the CSV as int or was just derived above.
    df["month"] = df["month"].astype(int).astype(str)

    # vendor_name/description feed the TF-IDF text column, where a blank
    # string is a valid, harmless input.
    for col in ["vendor_name", "description"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")

    # payment_method is genuinely blank on some real rows, and the trained
    # OneHotEncoder learned NaN as one of its own categories -- filling it
    # with "" here would not match what the model was fit on and breaks
    # its category-matching at transform time. Leave real blanks as NaN.
    if "payment_method" not in df.columns:
        df["payment_method"] = np.nan

    if "amount" not in df.columns:
        raise ValueError("Input CSV must have an 'amount' column.")

    # The baseline pipeline was trained on a single combined text column
    # (vendor_name + description) rather than two separate raw columns.
    df["text_features"] = (
        df["vendor_name"].fillna("") + " " + df["description"].fillna("")
    ).str.strip()

    return df


def _rebuild_amount_scaler(mean: float, scale: float) -> StandardScaler:
    """Reconstruct a fitted StandardScaler from saved mean/scale, so
    build_feature_matrix() scales new amounts exactly like it did at
    training time -- without needing to refit on new data."""
    scaler = StandardScaler()
    scaler.mean_ = np.array([mean])
    scaler.scale_ = np.array([scale])
    scaler.var_ = np.array([scale**2])
    scaler.n_features_in_ = 1
    return scaler


def predict_baseline(df: pd.DataFrame, model_path: Path) -> pd.DataFrame:
    artifact = joblib.load(model_path)
    pipeline = artifact["pipeline"]

    X = df[FEATURE_COLS]
    proba = pipeline.predict_proba(X)
    labels = getattr(pipeline, "classes_", np.array(artifact["labels"]))

    best_idx = proba.argmax(axis=1)
    predicted = labels[best_idx]
    confidence = proba[np.arange(len(df)), best_idx]

    out = df.copy()
    out["predicted_category"] = predicted
    out["confidence"] = confidence
    return out


def predict_pytorch(df: pd.DataFrame, model_path: Path) -> pd.DataFrame:
    import torch

    from train_expense_model_pytorch import ExpenseMLP

    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)

    amount_scaler = _rebuild_amount_scaler(
        checkpoint["amount_mean"], checkpoint["amount_scale"]
    )
    X, _, _, _, _ = build_feature_matrix(
        df,
        month_categories=checkpoint["month_categories"],
        payment_categories=checkpoint["payment_categories"],
        amount_scaler=amount_scaler,
    )

    model = ExpenseMLP(checkpoint["input_dim"], checkpoint["n_classes"])
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    with torch.no_grad():
        logits = model(torch.tensor(X, dtype=torch.float32))
        proba = torch.softmax(logits, dim=1).numpy()

    label_names = np.array(checkpoint["label_names"])
    best_idx = proba.argmax(axis=1)
    predicted = label_names[best_idx]
    confidence = proba[np.arange(len(df)), best_idx]

    out = df.copy()
    out["predicted_category"] = predicted
    out["confidence"] = confidence
    return out


def predict_keras(df: pd.DataFrame, model_path: Path, labels_path: Path) -> pd.DataFrame:
    from tensorflow import keras

    with open(labels_path) as f:
        meta = json.load(f)

    amount_scaler = _rebuild_amount_scaler(meta["amount_mean"], meta["amount_scale"])
    X, _, _, _, _ = build_feature_matrix(
        df,
        month_categories=meta["month_categories"],
        payment_categories=meta["payment_categories"],
        amount_scaler=amount_scaler,
    )

    model = keras.models.load_model(model_path)
    proba = model.predict(X, verbose=0)

    label_names = np.array(meta["label_names"])
    best_idx = proba.argmax(axis=1)
    predicted = label_names[best_idx]
    confidence = proba[np.arange(len(df)), best_idx]

    out = df.copy()
    out["predicted_category"] = predicted
    out["confidence"] = confidence
    return out


def predict_expenses(
    df: pd.DataFrame,
    model: str = "baseline",
    baseline_model_path: Path = DEFAULT_BASELINE_MODEL,
    pytorch_model_path: Path = DEFAULT_PYTORCH_MODEL,
    keras_model_path: Path = DEFAULT_KERAS_MODEL,
    keras_labels_path: Path = DEFAULT_KERAS_LABELS,
) -> pd.DataFrame:
    """Run inference with any of the three trained models. This is the
    function to import if predict_expenses.py is ever wired into a
    Streamlit page instead of run from the command line."""
    if model == "baseline":
        return predict_baseline(df, baseline_model_path)
    elif model == "pytorch":
        return predict_pytorch(df, pytorch_model_path)
    elif model == "keras":
        return predict_keras(df, keras_model_path, keras_labels_path)
    else:
        raise ValueError(f"Unknown model choice: {model!r}")


def main():
    parser = argparse.ArgumentParser(description="Predict expense categories.")
    parser.add_argument(
        "--model",
        choices=["baseline", "pytorch", "keras"],
        default="baseline",
        help="Which trained model to use (default: baseline).",
    )
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--baseline-model", type=Path, default=DEFAULT_BASELINE_MODEL)
    parser.add_argument("--pytorch-model", type=Path, default=DEFAULT_PYTORCH_MODEL)
    parser.add_argument("--keras-model", type=Path, default=DEFAULT_KERAS_MODEL)
    parser.add_argument("--keras-labels", type=Path, default=DEFAULT_KERAS_LABELS)
    args = parser.parse_args()

    df = prepare_input_df(args.input_csv)

    print(f"Loaded {len(df)} rows from {args.input_csv}")
    print(f"Running inference with model: {args.model}")

    result = predict_expenses(
        df,
        model=args.model,
        baseline_model_path=args.baseline_model,
        pytorch_model_path=args.pytorch_model,
        keras_model_path=args.keras_model,
        keras_labels_path=args.keras_labels,
    )

    result.to_csv(args.output_csv, index=False)

    print(f"\nSaved predictions to {args.output_csv}")
    print("\nPredicted category distribution:")
    print(result["predicted_category"].value_counts())
    print(f"\nAverage confidence: {result['confidence'].mean():.3f}")
    print(f"Rows below 0.5 confidence: {(result['confidence'] < 0.5).sum()}")


if __name__ == "__main__":
    main()
