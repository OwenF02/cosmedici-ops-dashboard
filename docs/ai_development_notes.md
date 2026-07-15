# AI Development Notes

Documenting where and how AI tooling was used throughout this project — kept incrementally, not written retroactively.

## Planning Phase (Sprint 0)

Used Claude (Anthropic) as a planning collaborator to develop and stress-test the full 7-week sprint plan before writing any code. Specific contributions:

- Reviewed an initial sprint plan draft and surfaced structural gaps: category list inconsistencies, potential label leakage in the lead conversion features, accuracy-only evaluation (missing per-category precision/recall/F1), untested deployment assumptions, and an unused SQLite dependency.
- Identified that the two ML modules had fundamentally different data readiness — real historical data exists for expenses, but not for lead outcomes — which reshaped the plan into a rule-based-first lead scorer with a documented ML upgrade path, rather than training a model on fabricated labels.
- Worked through the target-variable definition for lead conversion (specifically how `no_show` should be labeled) as a business judgment call, not a purely technical one.
- Helped design the public/private architecture (data, models, database, config) so it's structurally enforced via `.gitignore` and folder layout from Sprint 0, rather than relying on manual discipline later.
- Proposed the SQLite backup plan (WAL mode, automated backups, off-machine copy, tested restore) before the database held any real data.
- Scaffolded the initial Sprint 0 project structure and seeded `project_scope.md`, `risk_log.md`, and `decision_log.md` from the decisions made during planning.

## What AI did *not* do

- Did not access, view, or process any real Cosmedici business data (leads, expenses, client records) during planning — all planning discussion used hypothetical/aggregate descriptions of the data, not the data itself.
- Did not make the underlying business judgment calls (e.g., how to treat `no_show` in the conversion label) — those were confirmed by the project owner; AI's role was to surface the ambiguity and lay out the tradeoffs.

*(Continue logging entries here as later sprints use AI assistance — model debugging, code review, documentation drafting, etc.)*
