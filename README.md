# AI Small Business Operations Dashboard

**Status:** In active development — Sprint 0 (Foundation & Architecture) complete.

An AI-powered operations dashboard built for Cosmedici Laser, a real med spa business, to help prioritize lead follow-up and automatically classify business expenses. Built as both a working internal business tool and a public portfolio project.

> Full project reasoning, timeline, and definitions of done live in [`docs/project_scope.md`](docs/project_scope.md). Decisions and their rationale are tracked in [`docs/decision_log.md`](docs/decision_log.md); known risks and mitigations in [`docs/risk_log.md`](docs/risk_log.md).

## The Problem

Cosmedici Laser had no systematic way to prioritize which leads to follow up on first, or to consistently categorize business expenses for reporting. This project addresses both.

## Two Modules

**Expense Classifier** — trained on real historical business data (Aug 2025–June 2026). Compares a classical ML baseline against PyTorch and Keras models built on pretrained text embeddings, and ships whichever performs best.

**Lead Priority Scorer** — launches as a transparent, rule-based scoring system rather than a trained model, because the business doesn't yet have labeled data on which leads did and didn't convert. A live intake log starts collecting that data now, with a documented path to a real ML model once enough real outcomes accumulate.

## Public Demo vs. Private Business Version

This repo ships two versions from one codebase:

| | Public Demo | Private Business |
|---|---|---|
| Data | Synthetic only | Real Cosmedici data |
| Model | Synthetic-trained (`models/public/`) | Real-trained (`models/private/`, not committed) |
| Where it runs | Streamlit Community Cloud | Locally / local business network |

*(Deployment links, screenshots, and a demo GIF will be added at launch — Sprint 6.)*

## Project Status

This README will be filled out fully at launch (Sprint 6): setup instructions, model evaluation results, screenshots, and limitations. Right now the repo reflects Sprint 0 — foundation, folder structure, and the public/private safety architecture are in place; no data has been loaded or models trained yet.

See [`docs/`](docs/) for the full sprint plan, data dictionary (coming in Sprint 1), model evaluation (Sprint 3), and business use guide (Sprint 4).
