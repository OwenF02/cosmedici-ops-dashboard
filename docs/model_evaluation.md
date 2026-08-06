# Model Evaluation: Expense Classifier

Documents how the expense classifier's three candidate models were built and compared, and how the winner is selected. Real per-category metrics from the private business dataset are not reproduced here (see `docs/decision_log.md` for that decision) — the public demo model in `models/public/` is trained and evaluated on synthetic data only.

## Task

Classify each expense row into one of the business's spending categories (`category_for_model`) using the fields available at data-entry time: vendor name, description, amount, month, and payment method.

## Candidate Models

Three approaches are trained on identical train/test splits and compared honestly, rather than defaulting to whichever framework sounds most impressive:

| Model | Approach |
|---|---|
| Classical baseline | TF-IDF over combined vendor name + description text, one-hot encoded month and payment method, passthrough amount, feeding a scikit-learn classifier (logistic regression and random forest are both tried; the better of the two by macro F1 is kept as "the baseline"). |
| PyTorch | A small MLP (128 → 64 → n_classes, ReLU activations, dropout) trained on pretrained sentence-transformer embeddings (`all-MiniLM-L6-v2`) of the same text, concatenated with one-hot month/payment method and a standardized amount feature. |
| Keras | The same architecture and feature pipeline as the PyTorch model, implemented in TensorFlow/Keras, to compare the two major deep learning frameworks directly rather than picking one arbitrarily. |

The two neural network models deliberately reuse pretrained text embeddings rather than training embeddings from scratch — the dataset is far too small (roughly 1,000 rows) to learn useful representations on its own. This is a legitimate use of transfer learning, not deep learning applied just to say it was used.

## Feature Engineering Notes

- **Text**: vendor name and description are concatenated into a single text field before vectorization/embedding, since description is blank on most rows and vendor name alone often carries the strongest signal.
- **Amount**: for the neural network models, raw dollar amounts are standardized (zero mean, unit variance) before being concatenated with embedding values. Skipping this step let a single large-magnitude feature destabilize training — both networks converged to a degenerate solution that never predicted the majority category correctly until the fix was applied. This is documented in `docs/decision_log.md`.
- **Categorical fields**: month and payment method are one-hot encoded with unseen categories at inference time ignored rather than erroring, since new data will inevitably include a typo or unlisted value.
- **Class imbalance**: every model uses class weighting (inverse frequency) rather than resampling, since the smallest categories have too few real examples to safely oversample or synthesize.

## Evaluation Metrics

Three metrics are reported for every candidate, because any one alone is misleading on an imbalanced category distribution:

- **Accuracy** — fraction of all predictions correct. Dominated by the largest category, so a model that only ever predicts "Payroll & Labor" still scores deceptively well.
- **Macro F1** — F1 score computed per category, then averaged with equal weight per category regardless of size. This is the primary model-selection metric, since it penalizes a model that ignores small categories.
- **Weighted F1** — F1 per category, averaged proportional to category size. Reflects the accuracy a user would actually notice day-to-day, since it's dominated by the same large categories a person encounters most often.

## Model Selection

The candidate with the highest macro F1 on the held-out test set is selected as the production default. Model choice, and the reasoning behind it, is logged in `docs/decision_log.md` rather than assumed to always favor the most sophisticated architecture.

Because all three models are trained on the same feature contract, `src/predict_expenses.py` supports running inference with any of them interchangeably via a `--model {baseline,pytorch,keras}` flag, defaulting to the current best performer. This keeps the classifier both production-ready (always defaulting to whichever model tests best) and useful for demonstrating applied PyTorch/TensorFlow work, without shipping an underperforming model just to use a particular framework.

## Retraining Milestones

Real expense data accumulates slowly (roughly 1,000 labeled rows as of this writing). The three-model comparison is re-run periodically as more data comes in, rather than once at launch, since:

- A model that wins on ~1,000 rows may not still win on 2,000+, particularly the neural network candidates, which tend to benefit more from additional data than the classical baseline does.
- Categories that are currently too sparse to evaluate reliably (a handful of real examples) become statistically meaningful to assess as more months of data are recorded.

Each retraining pass is logged as its own entry in `docs/decision_log.md`, including whether the production model changed and why.

## What's Public vs. Private

- Public: this methodology, the model architectures, the feature engineering approach, and the synthetic demo model shipped in `models/public/`.
- Private: real per-category accuracy/F1 numbers (`metrics/*.json`), the real-data-trained model weights (`models/private/`), and the underlying business data itself. Model weights and evaluation metrics can indirectly reveal real vendor names, category patterns, and spending ranges even without the raw data file present, so they're excluded from the public repo entirely — not just the raw CSVs.
