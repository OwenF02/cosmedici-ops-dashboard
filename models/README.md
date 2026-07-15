# Models

Model files are split by what data trained them — the same principle applied to `data/`.

- **`public/synthetic_demo_model.pkl`** — trained entirely on `data/expenses_sample.csv` (synthetic data). This is the only model file in this repository that is ever committed to GitHub. It's what powers the public Streamlit demo.
- **`private/`** — git-ignored. Holds the real, Cosmedici-data-trained models (classical baseline, PyTorch, Keras) produced in Sprint 3, and whichever one is selected as the production model for the private business version of the app. Never committed, never published.

A model trained on real data can encode real vendor names, category patterns, and financial ranges in its weights even without a data file sitting next to it — so it gets the same privacy treatment as the raw data itself.
