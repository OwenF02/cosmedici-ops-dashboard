"""
lead_scoring.py

Rule-based V1 lead priority scorer -- the real, production logic (not a
placeholder). Built around the actual lead intake columns, not the
message-type/discount rubric sketched earlier in planning, which assumed
fields (message_type, discount_offered) that the real intake log doesn't
capture. This scores what's actually being recorded: whether a lead has
been contacted, and what happened when they were.

Expected input columns (case-insensitive, spaces allowed):
    Date, Lead Name, Phone, Email, Service Interested in,
    Source Ad, Contacted, Response status, Booking status, Notes

Scoring logic (confirmed with the business owner):
    Booking status = Booked          -> excluded from priority scoring (converted, closed)
    Not contacted yet                -> priority 100 (needs first outreach)
    Contacted, no response logged    -> priority 75  (warm -- likely still deciding, follow up to close)
    Contacted, voicemail/mailbox full-> priority 50  (no live contact yet, try again)
    Contacted, not in service        -> priority 25  (bad number, needs alternate contact or should be dropped)
    Contacted, not interested        -> priority 0   (closed-lost, deprioritize)

"Contacted" is inferred, not read literally off the Contacted column --
in the real intake log that column is left blank far more often than
it's filled in, while Response status only ever gets written after an
actual contact attempt. A lead counts as contacted if either Contacted
says yes, or Response status has any content at all. See
_effective_contacted() below.

Response status is treated as a strict set of 4 known values (plus a
few obvious spelling/spacing variants). Anything else -- including
free-text notes that ended up in this column instead of Notes, e.g.
"wrong person" or "he did not click on anything" -- is flagged for
manual review rather than silently mis-scored.

Source Ad and Service Interested in are tracked but deliberately not
scored yet -- there isn't enough real outcome volume to know which
sources or services actually convert better (see docs/decision_log.md).
They're carried through in the output so that pattern can be analyzed
once more data accumulates.

Usage:
    python src/lead_scoring.py
    python src/lead_scoring.py --input-csv data/private/leads.csv --output-csv scored_leads.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_INPUT_PATH = Path("data/private/leads.csv")
DEFAULT_OUTPUT_PATH = Path("scored_leads.csv")

# Canonical internal column names <- accepted raw header variants
COLUMN_MAP = {
    "date": "date",
    "lead name": "lead_name",
    "phone": "phone",
    "email": "email",
    "service interested in": "service_interested",
    "source ad": "source_ad",
    "contacted": "contacted",
    "response status": "response_status",
    "booking status": "booking_status",
    "notes": "notes",
}

TRUE_VALUES = {"yes", "y", "true", "1"}

NOT_INTERESTED_VALUES = {"not interested"}
NOT_IN_SERVICE_VALUES = {"not in service", "number not in service", "out of service"}
NO_LIVE_CONTACT_VALUES = {
    "voicemail", "voice mail", "left voicemail",
    "mailbox full", "mail box full",
}

BOOKED_VALUES = {"booked"}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map real-world header variants (spacing/casing) onto canonical
    snake_case column names used internally."""
    df = df.copy()
    rename = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in COLUMN_MAP:
            rename[col] = COLUMN_MAP[key]
    df = df.rename(columns=rename)

    for canonical in COLUMN_MAP.values():
        if canonical not in df.columns:
            df[canonical] = np.nan

    return df


def _is_contacted(value) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip().lower() in TRUE_VALUES


def _effective_contacted(contacted, response_status) -> bool:
    """A lead counts as contacted if the Contacted column says so, OR if
    Response status has any content at all. In practice the real intake
    log leaves Contacted blank far more often than it's filled in, while
    Response status only ever gets written after an actual contact
    attempt -- so its presence is the more reliable signal."""
    if _is_contacted(contacted):
        return True
    if pd.isna(response_status):
        return False
    return str(response_status).strip() != ""


def _is_booked(value) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip().lower() in BOOKED_VALUES


def score_row(contacted, response_status, booking_status) -> tuple[int | None, str, bool]:
    """Return (priority_score, reason, is_converted) for a single lead.

    priority_score is None only for a response_status value that doesn't
    match any known bucket -- flagged for manual review rather than
    silently guessed at.
    """
    if _is_booked(booking_status):
        return None, "Already booked -- converted, no longer needs prioritization", True

    if not _effective_contacted(contacted, response_status):
        return 100, "Not yet contacted -- reach out as soon as possible", False

    status = "" if pd.isna(response_status) else str(response_status).strip().lower()

    if status == "":
        return 75, "Contacted, no outcome logged yet -- likely still deciding, follow up to close", False
    if status in NO_LIVE_CONTACT_VALUES:
        return 50, f"Contacted ({status}) -- no live contact yet, try again", False
    if status in NOT_IN_SERVICE_VALUES:
        return 25, "Number not in service -- try an alternate contact method or drop", False
    if status in NOT_INTERESTED_VALUES:
        return 0, "Marked not interested -- deprioritize", False

    return None, f"Unrecognized response status ({response_status!r}) -- needs manual review", False


def score_leads(df: pd.DataFrame) -> pd.DataFrame:
    """Score every row of a leads dataframe. Non-destructive -- returns a
    new dataframe with priority_score, priority_reason, and is_converted
    columns added, sorted with the highest-priority open leads first."""
    df = normalize_columns(df)

    results = df.apply(
        lambda row: score_row(row["contacted"], row["response_status"], row["booking_status"]),
        axis=1,
        result_type="expand",
    )
    results.columns = ["priority_score", "priority_reason", "is_converted"]

    out = pd.concat([df, results], axis=1)

    # Highest priority first; unscored/needs-review rows (NaN score) sink
    # to the bottom rather than sorting unpredictably.
    out = out.sort_values(
        by="priority_score", ascending=False, na_position="last"
    ).reset_index(drop=True)

    return out


def main():
    parser = argparse.ArgumentParser(description="Score leads by follow-up priority.")
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    print(f"Loaded {len(df)} leads from {args.input_csv}")

    scored = score_leads(df)
    scored.to_csv(args.output_csv, index=False)

    needs_review = scored["priority_reason"].str.startswith("Unrecognized", na=False).sum()
    converted = scored["is_converted"].sum()
    open_leads = len(scored) - converted

    print(f"\nSaved scored leads to {args.output_csv}")
    print(f"Open leads: {open_leads} | Already booked: {converted} | Needs manual review: {needs_review}")
    print("\nPriority breakdown (open leads):")
    print(scored.loc[~scored["is_converted"], "priority_score"].value_counts(dropna=False).sort_index(ascending=False))


if __name__ == "__main__":
    main()
