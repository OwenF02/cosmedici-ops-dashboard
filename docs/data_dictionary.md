# Data Dictionary

Built from the real Master Sheets, August 2025–July 2026 (12 months). This file describes structure only — no real values from the source files are reproduced here.

## Source File Manifest

One canonical file per month. Where a month had duplicate or conflicting candidate files, the choice made and why is recorded here so Sprint 2 cleaning doesn't have to re-derive it.

| Month | Canonical source | Note |
|---|---|---|
| Aug 2025 | `Accounted Statements/August Master Sheet.xlsx` (expenses) + `Revenue 2025/Service_Revenue_08_25.xlsx` (revenue) | A second file named "August Master Sheet.xlsx" exists in the `Revenue 2025` folder but is actually a duplicate of the *expense* data, misfiled — not used. August's Accounted Statements file doesn't have a usable revenue tab, hence the separate source. |
| Sep 2025 | `Accounted Statements/Septemember Master Sheet.xlsx` (both tabs) | Filename typo ("Septemember") is consistent across copies — cosmetic only. |
| Oct 2025 | `Accounted Statements/October Master Sheet (up to date).xlsb.xlsx` (both tabs) | A second copy in the month folder (`10_2025/October Master Sheet.xlsx`) is a partial mid-month snapshot (47 rows, through Oct 15 only) — not used. |
| Nov 2025 | `Accounted Statements/November Master Sheet (up to date).xlsb - Copy.xlsx` (both tabs) | A second copy (`Nov_Manipluated_Sheet.xlsx`) is byte-for-byte identical (same 84 rows, same total) — no conflict, either would work. |
| Dec 2025 | `Accounted Statements/December Master Sheet..xlsx` (both tabs) | |
| Jan–Jul 2026 | `<Month>_2026/<Month> Master Sheet.xlsx` (both tabs) | One clean canonical file per month, no duplicates found. |

**Not used, and not opened:** anything under `Taxes 2025/Personal Owen/`, `Bank Statement Chase/`, `DIana Checks/`, W-2/1099 PDFs, `.sql`/`.mwb` files, and check images. These were present in the uploaded archive but are out of scope for this project and were left untouched.

## Table: Expenses

| Field | Source column | Type | Notes |
|---|---|---|---|
| `date` | `Date` | date | Three rows in Aug 2025 have a typo'd year (2205 instead of 2025) — correct to 2025 during cleaning, all three belong to the "Aug 17-23" week. |
| `week_number` | `Week Number` | text | **Dropped.** Present in most months but format is inconsistent (sometimes "Week 1", sometimes a date range like "Aug 1-2"). Week-of-month is derived from `date` instead. |
| `vendor_name` | `Vendor` | text | Sometimes blank. For payroll-related rows, this field sometimes holds a real employee's name rather than a business vendor — treat as PII, same handling as a real client name, when generating synthetic data. |
| `category` | `Category` | text (see Category Taxonomy below) | Taxonomy changed between Dec 2025 and Jan 2026 — see crosswalk. |
| `category_for_model` | *(new, derived, Sprint 3)* | text | Same as `category`, except rows in a small number of categories with too few real examples to train on reliably are folded into `Other/Non-Operating` for modeling purposes only. See "Sprint 3 Additions" below. `category` itself is left untouched for real bookkeeping/reporting. |
| `description` | `Description` | text | Blank on the large majority of rows (~70%+ in the months checked). The classifier's text signal will lean heavily on `vendor_name`; the embedding pipeline should handle a blank `description` gracefully rather than erroring or treating it as a distinct token. |
| `amount` | `Amount` | number | No negative values observed in Expenses. |
| `payment_method` | `Payment Method` | text | Observed values: Bank Transfer, Zelle, Check. Occasionally blank. One observed value appears to include a specific person's name and partial card number — never surface `payment_method` values raw in any public-facing output. |
| `date_estimated` | *(new, derived)* | boolean | `True` for the 4 rows below where a date had to be estimated. Lets the app/analysis distinguish real dates from best-guess ones later. |

## Table: Revenue

| Field | Source column | Type | Notes |
|---|---|---|---|
| `date` | `Date` | date | |
| `revenue_source` | `Description` | text | Despite the source column being labeled "Description," this field is actually a payment/booking channel (Square, Fresha, Groupon, Sync Bank, Cash, CareCredit, Refund), not free text. Renamed here to avoid confusion with the expense table's genuinely free-text `description`. A couple of typo/whitespace variants ("Sqaure", trailing-space "Fresha ") are normalized during cleaning — see `src/data_cleaning.py`. |
| `amount` | `Amount` (sometimes ` Amount ` with stray whitespace in the header) | number | No negative values observed, including "Refund" rows — see Resolved Cleaning Rules below for what "Refund" actually represents. |
| `payment_method` | `Payment Method` | text | Missing entirely from the August 2025 file (that month's revenue sheet only has Date/Description/Amount) — expect this column to be null for Aug 2025 rows specifically, not a data error. |

## Category Taxonomy

**Final 13 categories** (per your decision — the categories actually used Jan–June 2026, with anything ambiguous or non-conforming routed to the catch-all):

1. Payroll & Labor
2. Occupancy Cost
3. Marketing & Growth
4. Software & Technology
5. Insurance
6. Professional Services
7. Licensing & Compliance
8. Banking & Financial Fees
9. Repairs, Maintenance & Small Equipment
10. Debt Services
11. Cost of Services (Clinical Supplies)
12. Owner Distribution (Non-Operating)
13. **Other/Non-Operating** — the catch-all. Absorbs "Donation" (used as its own label in some 2026 months) and anything from the legacy taxonomy below that doesn't map cleanly to categories 1–12.

### Legacy Category Crosswalk (Aug–Dec 2025 → Final 13)

August–December 2025 used a more granular scheme (~25 distinct labels). Mapped here so all 12 months are usable for training, per your call to keep the extra data rather than only training on Jan–Jul 2026.

| Legacy category (Aug–Dec 2025) | Maps to |
|---|---|
| Salaries & Wages | Payroll & Labor |
| Payroll Taxes | Payroll & Labor |
| Staff Meals | Payroll & Labor |
| Employee Reimbursement - Staff Meals | Payroll & Labor |
| Contract Labor / Contacted Work | Payroll & Labor |
| Practice-Mgmt Software | Software & Technology |
| General SaaS | Software & Technology |
| Website & SEO | Marketing & Growth |
| Digital Ads | Marketing & Growth |
| Print/ In house Promo | Marketing & Growth |
| Rent/ CAM | Occupancy Cost |
| Utilities | Occupancy Cost |
| Disposable Clinic Supplies | Cost of Services (Clinical Supplies) |
| Skincare & Peel Products | Cost of Services (Clinical Supplies) |
| Injectable & IV Supplies | Cost of Services (Clinical Supplies) |
| Bank & Merchant Fees | Banking & Financial Fees |
| Interest Expense | Debt Services |
| Owner Draw/ Distribution | Owner Distribution (Non-Operating) |
| Insurance-Malpratice & Liability | Insurance |
| Licenses & Permits | Licensing & Compliance |
| Repairs & Maintenance | Repairs, Maintenance & Small Equipment |
| Small Tools & Décor | Repairs, Maintenance & Small Equipment |
| Employee Reimbursement - Office Supplies | Other/Non-Operating |
| Office Supplies | Other/Non-Operating |
| Machine Payment | Other/Non-Operating (ambiguous — could be equipment lease or debt financing; routed to catch-all per your instruction rather than guessed) |
| Charitable Contributions | Other/Non-Operating |
| Deprieciation & Amortization | Other/Non-Operating (not part of the final 13 — never appeared in actual Jan–Jul 2026 transactions) |

## Resolved Cleaning Rules

- **`$0` expense entries:** across all 12 months, exactly one row has a `$0` amount, and it has no date, vendor, category, or payment method — a stray artifact, not a real transaction. Dropped during cleaning.
- **"Refund" revenue entries:** these are funds returned *to* Cosmedici (a processing correction tied to a Maryland Comptroller registration gap), not refunds issued to clients. Correctly recorded as positive and stay that way — no sign flip in cleaning. Worth periodically confirming with the accountant whether the underlying registration issue driving these is resolved.
- **Rows with a blank `date`:** almost every month's Expenses and Revenue sheets have a trailing summary/total row baked directly into the data range — no date, no vendor, no description, just a number that matches that month's total. Confirmed across 11 of 12 expense sheets and 2 of 12 revenue sheets (Sept and Oct 2025 revenue specifically had multi-row scratch/profit-loss calculations mixed into the data). **Rule:** drop any row with a blank `date` *and* no vendor *and* no description — those are artifacts. Do **not** blindly drop every blank-date row, since a handful were real transactions missing only their date (see below).
- **Four real transactions with a missing date, given estimated dates rather than dropped:** three rows in Aug 2025 (no week label available on any of them, so each defaulted to the 1st of the month) and one row in Dec 2025 (labeled "Week 2," which starts 2025-12-08 in that month's own week labeling). Together they represent roughly $3,000 in real spend that a blind "drop if no date" rule would have silently deleted. The exact vendor names, amounts, and dates are intentionally **not** reproduced in this document — they live in `config/private_cleaning_overrides.py` (git-ignored, real data only, never committed). All four rows get `date_estimated = True` so they can be excluded from any day-of-week/time-sensitive analysis later while still counting toward totals and category breakdowns.

## Sprint 3 Additions

- **Vendor-based category consistency fix:** a small number of real vendors were found to have the same real-world transaction type logged under different categories depending on which month's file recorded it (inconsistent manual bookkeeping, not a structural data issue). Fixed by matching on vendor rather than by month, since the underlying transaction type doesn't change month to month. The real vendor names and their corrected target categories are kept in `config/private_cleaning_overrides.py` (git-ignored) rather than in this document — see `config/private_cleaning_overrides.example.py` for the format, and `docs/decision_log.md` for the reasoning.
- **One real transaction reclassified to Owner Distribution (Non-Operating):** confirmed with the business owner to be a personal expense paid from business funds rather than a genuine business expense. Same treatment as an existing, already-correctly-categorized personal-insurance row found during the same review.
- **Sparse-category rule:** `Professional Services` and `Licensing & Compliance` have too few real rows (~10 or fewer, even after the vendor fix above) to reliably train a per-category prediction on. A new `category_for_model` column (see Table: Expenses above) folds these two into `Other/Non-Operating` for modeling purposes only. The real `category` column is untouched, so real bookkeeping/reporting still shows all 13 categories accurately.

## Open Items for Sprint 2

- None remaining from the original list — category taxonomy, `$0` handling, "Refund" handling, `week_number`, the Aug 2025 date typos, and the full revenue-sheet quality check are all resolved above. Next step is building `src/data_cleaning.py` against these rules.
