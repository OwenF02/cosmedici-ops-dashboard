# Risk Log

Updated at the end of every sprint, not written retroactively.

| Date | Risk | Impact | Mitigation | Status |
|---|---|---|---|---|
| Week 1 | Real expense categories are imbalanced | Model may perform poorly on rare categories (e.g. Insurance, Equipment) | Report per-category F1, not just accuracy; merge or flag categories with fewer than ~10-15 real examples | Open |
| Week 1 | Streamlit Cloud install fails with ML dependencies | Public demo may break or fail to deploy | `requirements.txt` (deployed) includes only the synthetic demo model's dependencies (scikit-learn); PyTorch/TensorFlow stay in `requirements-dev.txt` | Open |
| Week 1 | Lead log adoption is low | Not enough real outcome data accumulates for a future ML upgrade | Keep lead entry simple; test the flow with front desk staff early (Sprint 1 wireframe check) and again in Sprint 5 | Open |
| Week 1 | GitHub file size limits hit by saved models | Push fails or repo becomes unwieldy | Only the synthetic demo model is ever committed; watch its size, use Git LFS if it exceeds ~50MB | Open |
| Week 1 | Real client/financial data leaks into public repo | Breaks GitHub-safe requirement, privacy risk | `data/private/`, `models/private/`, `backups/`, real `config.toml`, and real `.db` files are all git-ignored from Sprint 0; explicit safety check in Sprint 5 before anything is pushed | Open |
| Week 3 (planned) | SQLite database file corruption or loss | Loses lead/expense-correction history | WAL mode, automated daily backups (`backup_db.py`), off-machine copy, tested restore procedure (Sprint 5) | Planned |
| Week 3 (planned) | Exploration notebook contains real data in cell outputs | `01_data_exploration.ipynb` previews (`.head()`, category breakdowns) could leak real vendor names/figures if committed as-is | Treated as private for now; Sprint 5 safety check decides whether a sanitized version gets published or it's excluded entirely | Open |
| Week 2 | Two typo'd years in Aug 2025 expense dates (2205, 2005) | Would corrupt date-based features/sorting if uncleaned | Flagged for correction in Sprint 2 cleaning | Open |
| Week 2 | Category sparsity confirmed with real data — several categories had 0-1 transactions in individual months | Some categories may not have enough real examples to train on reliably | Already covered by the sparse-category rule in the sprint plan; now validated as a real, not hypothetical, risk | Open |
