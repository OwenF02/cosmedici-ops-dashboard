# App Wireframe

Low-fidelity layout for the six dashboard pages, sidebar navigation. This is the plan to walk a staff member through for the 10-minute Sprint 1 check before any of it gets built — catching a confusing layout or naming choice now is cheap; catching it after Sprint 4 is expensive.

## Navigation

Persistent left sidebar, six pages: Overview, Lead Log, Lead Priority Scorer, Expense Classifier, Model Results, Documentation.

## 1. Overview

- Four summary metric cards across the top: total leads, high-priority leads, total expenses, top expense category.
- Monthly expense trend chart below.

## 2. Lead Log

- Left: "add new lead" form (source, service interest, message type, discount offered).
- Right: lead list — source, priority label, outcome (editable — this is where staff mark a lead booked/no-show/declined/no-response as it resolves).

## 3. Lead Priority Scorer

- Left: enter lead details (same fields as the intake form).
- Right: output — score, priority label, and reason codes (per `lead_scoring_rubric.md`).

## 4. Expense Classifier

- Top: CSV upload.
- Below: predicted category, confidence score, a correction control (dropdown or button to fix a wrong prediction — this writes to the `expense_corrections` table), and a spend-by-category chart.

## 5. Model Results

- Three panels: baseline model metrics, PyTorch vs. Keras comparison, and the stated production model choice with reasoning.
- Includes the demo-model vs. production-model explainer (which one is running depends on `DEMO_MODE` vs `BUSINESS_MODE`).

## 6. Documentation

- Explains demo vs. business mode.
- Links out to the other project docs (data dictionary, scoring rubric, model evaluation, business use guide).

## What to Watch For in the Staff Walkthrough

- Does "priority label" (High/Medium/Low) make sense without further explanation, or does it need a tooltip?
- Is it obvious that Lead Log is for ongoing tracking and Lead Priority Scorer is for scoring a single new inquiry — two different pages that could get confused?
- Does the expense correction flow feel like it takes more than a few seconds per row?
- Any page someone expected to find that isn't here?

Record what comes out of this in `docs/testing_notes.md` — even though the full staff test run is Sprint 5, this early check is worth keeping a record of too.
