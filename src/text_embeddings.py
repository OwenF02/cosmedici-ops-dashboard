"""
Sprint 3 — shared text-embedding pipeline for the PyTorch and Keras
expense-classifier comparison.

Both models need the same input representation to make the comparison
fair: a pretrained sentence embedding over (vendor_name + description),
concatenated with the structured features (amount, month, payment_method).
This module is the one place that embedding logic lives, so
train_expense_model_pytorch.py and train_expense_model_keras.py are
comparing model architectures, not different feature pipelines.

Uses sentence-transformers' "all-MiniLM-L6-v2" — small (~80MB), fast on
CPU, and a common, well-supported default for short-text embeddings. Not
fine-tuned on this data; used purely as a fixed feature extractor
(transfer learning), per the Sprint 3 plan.

Usage:
    from text_embeddings import embed_texts, build_feature_matrix
    embeddings = embed_texts(["Square POS fee", "Rent payment"])
    X, feature_names, month_cats, payment_cats, amount_scaler = build_feature_matrix(df)
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

_MODEL_NAME = "all-MiniLM-L6-v2"
_model = None  # lazy-loaded singleton - avoid reloading the model on every call


def _get_model():
    global _model
    if _model is None:
        # Imported lazily so anything that only needs build_feature_matrix's
        # non-text pieces doesn't pay the sentence-transformers import cost.
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a list of strings into a (n_texts, 384) array using the
    shared pretrained model. Empty/whitespace-only strings still get a
    valid embedding (the model handles empty input fine)."""
    model = _get_model()
    texts = [t if isinstance(t, str) else "" for t in texts]
    return model.encode(texts, show_progress_bar=False, convert_to_numpy=True)


def build_feature_matrix(
    df: pd.DataFrame,
    month_categories=None,
    payment_categories=None,
    amount_scaler: StandardScaler = None,
):
    """Build the combined feature matrix (text embeddings + structured
    features) for a dataframe that already has `vendor_name`,
    `description`, `amount`, `month`, and `payment_method` columns
    (see load_and_prepare() in train_expense_model_baseline.py for how
    these get set up from the raw cleaned CSV).

    `amount` is standardized (mean 0, std 1) before being concatenated
    with the embedding and one-hot columns - without this, raw dollar
    amounts (which can run into the thousands) dominate the feature scale
    next to embedding values and 0/1 dummies, which destabilizes neural
    net training (this was a real bug found during Sprint 3 - Keras in
    particular failed to learn the majority category at all until this
    was added).

    month_categories / payment_categories / amount_scaler: pass the
    values fit during training when encoding a test/inference set, so
    columns and scale stay aligned even if the new data doesn't contain
    every category or has a different amount distribution.

    Returns (X, feature_names, month_categories, payment_categories,
    amount_scaler) so callers can reuse the same fitted objects for
    future inference.
    """
    text = (df["vendor_name"].fillna("") + " " + df["description"].fillna("")).str.strip()
    text_embeddings = embed_texts(text.tolist())

    month_dummies = pd.get_dummies(df["month"], prefix="month")
    if month_categories is not None:
        month_dummies = month_dummies.reindex(columns=month_categories, fill_value=0)
    else:
        month_categories = list(month_dummies.columns)

    payment_dummies = pd.get_dummies(df["payment_method"], prefix="payment")
    if payment_categories is not None:
        payment_dummies = payment_dummies.reindex(columns=payment_categories, fill_value=0)
    else:
        payment_categories = list(payment_dummies.columns)

    amount_raw = df[["amount"]].to_numpy(dtype=float)
    if amount_scaler is None:
        amount_scaler = StandardScaler()
        amount_scaled = amount_scaler.fit_transform(amount_raw)
    else:
        amount_scaled = amount_scaler.transform(amount_raw)

    X = np.concatenate(
        [text_embeddings, month_dummies.to_numpy(dtype=float), payment_dummies.to_numpy(dtype=float), amount_scaled],
        axis=1,
    )

    feature_names = (
        [f"embed_{i}" for i in range(text_embeddings.shape[1])]
        + list(month_dummies.columns)
        + list(payment_dummies.columns)
        + ["amount_scaled"]
    )

    return X, feature_names, month_categories, payment_categories, amount_scaler
