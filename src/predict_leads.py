"""
predict_leads.py

Switchable inference for lead prioritization -- mirrors the design of
predict_expenses.py. Today there's only one real option, the rule-based
V1 scorer in lead_scoring.py, because the real intake log doesn't have
enough labeled outcomes yet to train anything on. This wrapper exists so
that when it does (see the retraining milestone in docs/decision_log.md),
a trained model can be dropped in behind the same --model flag without
changing how the rest of the app calls this script.

Usage:
    python src/predict_leads.py
    python src/predict_leads.py --input-csv data/leads_sample.csv --output-csv scored_leads.csv
    python src/predict_leads.py --model trained   # not implemented yet -- see below
"""

import argparse
from pathlib import Path

import pandas as pd

from lead_scoring import score_leads

DEFAULT_INPUT_PATH = Path("data/private/leads.csv")
DEFAULT_OUTPUT_PATH = Path("scored_leads.csv")


def predict_rule_based(df: pd.DataFrame) -> pd.DataFrame:
    return score_leads(df)


def predict_trained(df: pd.DataFrame, model_path: Path | None = None) -> pd.DataFrame:
    """Placeholder for a future trained lead model. Not implemented --
    there isn't enough real labeled outcome data yet (see the retraining
    milestone note in docs/decision_log.md). Once there is, this should
    load a saved model the same way predict_expenses.py does and produce
    the same priority_score/priority_reason columns as the rule-based
    path, so callers don't need to change."""
    raise NotImplementedError(
        "No trained lead model exists yet -- the real intake log doesn't have "
        "enough labeled outcomes to train on. Use --model rule_based (the "
        "default) until the retraining milestone in docs/decision_log.md is reached."
    )


def predict_leads(df: pd.DataFrame, model: str = "rule_based", model_path: Path | None = None) -> pd.DataFrame:
    """Score leads with the selected model. This is the function to
    import if this is ever wired into a Streamlit page instead of run
    from the command line."""
    if model == "rule_based":
        return predict_rule_based(df)
    elif model == "trained":
        return predict_trained(df, model_path)
    else:
        raise ValueError(f"Unknown model choice: {model!r}")


def main():
    parser = argparse.ArgumentParser(description="Score and prioritize leads.")
    parser.add_argument(
        "--model",
        choices=["rule_based", "trained"],
        default="rule_based",
        help="Which scoring approach to use (default: rule_based).",
    )
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    print(f"Loaded {len(df)} leads from {args.input_csv}")
    print(f"Running inference with model: {args.model}")

    result = predict_leads(df, model=args.model)
    result.to_csv(args.output_csv, index=False)

    needs_review = result["priority_reason"].str.startswith("Unrecognized", na=False).sum()
    converted = result["is_converted"].sum()
    open_leads = len(result) - converted

    print(f"\nSaved scored leads to {args.output_csv}")
    print(f"Open leads: {open_leads} | Already booked: {converted} | Needs manual review: {needs_review}")


if __name__ == "__main__":
    main()
