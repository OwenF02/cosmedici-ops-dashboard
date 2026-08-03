"""
Sprint 3 — classical baseline expense classifier.

Trains on real data/private/cleaned_expenses.csv (BUSINESS_MODE) or a
synthetic sample like data/expenses_sample.csv (DEMO_MODE) — same script,
different input, per the public/private architecture.

Predicts `category_for_model` (the 11-category scheme used for modeling —
see docs/data_dictionary.md "Sparse category rule": Professional Services
and Licensing & Compliance are folded into Other/Non-Operating for
training purposes only; the real `category` column is untouched for
bookkeeping/reporting).

Two candidate models are compared (Logistic Regression, Random Forest) on
the same feature pipeline; whichever wins on macro F1 is saved as the
baseline. Macro F1 (not accuracy) is the selection metric because accuracy
alone would reward ignoring the smaller categories entirely — Payroll &
Labor is ~37% of rows, so a model that always predicts it would still
score respectably on plain accuracy.

Features:
    - TF-IDF over vendor_name + description (combined text field)
    - amount (numeric, passthrough)
    - month (categorical, one-hot, extracted from date)
    - payment_method (categorical, one-hot)

Usage (all flags are optional — defaults match the real business paths):
    python src/train_expense_model_baseline.py
    python src/train_expense_model_baseline.py --data-path data/expenses_sample.csv --model-out models/public/synthetic_demo_model.pkl
"""

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

TARGET_COL = "category_for_model"
TEXT_COL = "text_features"
RANDOM_STATE = 42

DEFAULT_DATA_PATH = Path("data/private/cleaned_expenses.csv")
DEFAULT_MODEL_OUT = Path("models/private/expense_baseline.pkl")
DEFAULT_METRICS_OUT = Path("metrics/baseline_metrics.json")


def load_and_prepare(data_path: Path) -> pd.DataFrame:
    df = pd.read_csv(data_path, parse_dates=["date"])

    if TARGET_COL not in df.columns:
        # Synthetic sample files only have a single `category` column (no
        # sparse categories to merge in fabricated data) - treat it as
        # already being the model target.
        df[TARGET_COL] = df["category"]

    df["month"] = df["date"].dt.month.astype(str)
    df["vendor_name"] = df["vendor_name"].fillna("")
    df["description"] = df["description"].fillna("")
    df["payment_method"] = df["payment_method"].fillna("Unknown")
    df[TEXT_COL] = (df["vendor_name"] + " " + df["description"]).str.strip()

    return df


def build_pipeline(classifier) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("text", TfidfVectorizer(max_features=500, ngram_range=(1, 2)), TEXT_COL),
            ("month", OneHotEncoder(handle_unknown="ignore"), ["month"]),
            ("payment_method", OneHotEncoder(handle_unknown="ignore"), ["payment_method"]),
            ("amount", "passthrough", ["amount"]),
        ]
    )
    return Pipeline(steps=[("preprocess", preprocessor), ("classify", classifier)])


CANDIDATES = {
    "logistic_regression": LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE),
    "random_forest": RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=RANDOM_STATE),
}


def evaluate(pipeline: Pipeline, X_test, y_test, labels) -> dict:
    y_pred = pipeline.predict(X_test)
    report = classification_report(y_test, y_pred, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "macro_f1": f1_score(y_test, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_test, y_pred, average="weighted", zero_division=0),
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "labels": labels,
    }


def main():
    parser = argparse.ArgumentParser(description="Train the classical baseline expense classifier.")
    parser.add_argument(
        "--data-path", type=Path, default=DEFAULT_DATA_PATH,
        help=f"CSV to train on (default: {DEFAULT_DATA_PATH})",
    )
    parser.add_argument(
        "--model-out", type=Path, default=DEFAULT_MODEL_OUT,
        help=f"Where to save the trained model (default: {DEFAULT_MODEL_OUT})",
    )
    parser.add_argument(
        "--metrics-out", type=Path, default=DEFAULT_METRICS_OUT,
        help=f"Where to save metrics JSON (default: {DEFAULT_METRICS_OUT})",
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    if not args.data_path.exists():
        raise FileNotFoundError(
            f"No file found at {args.data_path}. Run this from the project root "
            f"(cd to cosmedici-ops-dashboard first), or pass --data-path explicitly."
        )

    df = load_and_prepare(args.data_path)
    labels = sorted(df[TARGET_COL].unique())

    feature_cols = [TEXT_COL, "month", "payment_method", "amount"]
    X = df[feature_cols]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=RANDOM_STATE, stratify=y
    )

    results = {}
    fitted_pipelines = {}
    for name, classifier in CANDIDATES.items():
        pipeline = build_pipeline(classifier)
        pipeline.fit(X_train, y_train)
        metrics = evaluate(pipeline, X_test, y_test, labels)
        results[name] = metrics
        fitted_pipelines[name] = pipeline
        print(f"{name}: accuracy={metrics['accuracy']:.3f}  macro_f1={metrics['macro_f1']:.3f}  weighted_f1={metrics['weighted_f1']:.3f}")

    winner = max(results, key=lambda n: results[n]["macro_f1"])
    print(f"\nSelected baseline: {winner} (highest macro F1)")
    print("\nPer-category report for the winner:")
    for cat, stats in results[winner]["classification_report"].items():
        if cat in ("accuracy", "macro avg", "weighted avg"):
            continue
        print(f"  {cat}: precision={stats['precision']:.2f} recall={stats['recall']:.2f} f1={stats['f1-score']:.2f} support={int(stats['support'])}")

    args.model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"pipeline": fitted_pipelines[winner], "labels": labels, "model_name": winner, "target_col": TARGET_COL},
        args.model_out,
    )
    print(f"\nSaved model -> {args.model_out}")

    if args.metrics_out:
        args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.metrics_out, "w") as f:
            json.dump(
                {"dataset_size": len(df), "n_train": len(X_train), "n_test": len(X_test), "winner": winner, "results": results},
                f,
                indent=2,
                default=str,
            )
        print(f"Saved metrics -> {args.metrics_out}")


if __name__ == "__main__":
    main()
