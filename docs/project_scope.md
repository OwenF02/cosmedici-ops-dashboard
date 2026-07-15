# Project Scope

## Business Problem

Cosmedici Laser (a laser aesthetics and med spa business) currently has no systematic way to:

1. Prioritize follow-up on incoming leads — inquiries come in through Fresha, Meta/Instagram DMs, and the website contact form, with no consistent tracking of which ones convert.
2. Categorize business expenses — expense/revenue records exist (real data from August 2025–June 2026) but aren't consistently classified into a usable set of operating categories.

This project builds a small operations dashboard that addresses both, while also serving as a public portfolio piece for AI/ML/data analyst internship applications.

## The Two Modules

### Module 1: Expense Classifier

The real machine learning component at launch. Cosmedici has ~11 months of real expense/revenue history — enough to train a genuine classifier. Revenue and expense records are kept as separate datasets/tables, not combined.

**Final categories:** Payroll, Rent, Software, Marketing, Supplies, Equipment, Contractors, Insurance, Utilities, Other.

Approach: a classical baseline (Logistic Regression / Random Forest / XGBoost) compared against a PyTorch MLP and a Keras MLP, both using a shared pretrained sentence-embedding pipeline on vendor name + description text. Best model (by performance, simplicity, and deployment reliability) wins production. All real-data-trained models stay private (`models/private/`); a separately trained synthetic-data model powers the public demo (`models/public/`).

### Module 2: Lead Priority Scorer

**Not** launched as a real ML model — Cosmedici doesn't yet have a reliable dataset of both converted and non-converted leads (Fresha tracks bookings/no-shows, but inquiries that never converted aren't captured anywhere consistent).

Launches instead as a transparent, rule-based priority scorer, paired with a live lead intake log that starts capturing real labeled outcomes from Sprint 2 onward. The ML upgrade path is designed and documented, with a concrete retraining milestone (~3 months of real intake-log data, target: early October 2026) rather than left open-ended.

**Conversion label definition** (for future ML training):

| Raw outcome | Conversion label |
|---|---|
| booked | converted |
| no_show | converted (no-show is a separate downstream metric, not a lead-gen failure) |
| declined | not converted |
| no_response | not converted |
| pending | excluded (auto-resolves to no_response after 30 days) |

## Public vs. Private Architecture

The project ships as two versions from a single codebase:

- **Public Demo Version** — synthetic data, synthetic-trained model only, deployed to Streamlit Community Cloud. Safe to share with recruiters.
- **Private Business Version** — real Cosmedici data, real-trained production model, local SQLite database (lead log + expense corrections). Runs locally or on the local business network. Never deployed publicly.

Enforced structurally, not by convention: `data/private/`, `models/private/`, and `backups/` are all git-ignored (`folder/*` + `!folder/.gitkeep` pattern); a `DEMO_MODE` / `BUSINESS_MODE` config flag controls which data and model files the app reads.

## MVP vs. Portfolio Enhancements

**MVP (required):** clean expense dataset, expense category model, expense upload/prediction flow, manual correction logging, lead intake log, rule-based lead scoring, Streamlit dashboard, both app modes, README + docs, public-repo safety check, staff test run.

**Portfolio enhancements (cut first if behind schedule):** baseline vs. PyTorch vs. Keras comparison, synthetic lead demo model, demo GIF, LinkedIn post, extra polish.

## Timeline

| Week | Sprint | Outcome |
|---|---|---|
| 1 | Sprint 0 | Repo, structure, data safety, scope |
| 2 | Sprint 1 | Schemas, scoring rubric, wireframes |
| 3 | Sprint 2 | Clean expense data, synthetic samples, live lead log |
| 4 | Sprint 3 | Expense model, model comparison, lead scorer |
| 5 | Sprint 4 | Streamlit dashboard, both modes, deployment tested |
| 6 | Sprint 5 | QA, staff feedback, repo safety |
| 7 | Sprint 6 | Docs, deploy, GitHub, resume/LinkedIn |

## Portfolio Story

> I built an AI-powered operations dashboard for a real med spa business. The expense classifier uses real historical business data and compares classical ML, PyTorch, and Keras models. The lead conversion feature starts with a transparent rule-based scoring system because the business did not yet have valid non-converted lead data. I solved that by building the lead intake pipeline first, allowing the business to collect the right data for a future ML upgrade — with a concrete retraining milestone already scheduled. The project includes a private business version, trained on real data and never published, and a public GitHub demo version running entirely on synthetic data and a synthetic-trained model.
