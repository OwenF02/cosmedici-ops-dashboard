"""
Template for config/private_cleaning_overrides.py — copy this file to
that name and fill in real values for your machine. That file is
git-ignored and never committed; this example (with placeholder data
only) is what's committed instead, so the public repo shows the
mechanism without exposing any real vendor names, amounts, or people.

src/data_cleaning.py imports ESTIMATED_DATES and VENDOR_CATEGORY_OVERRIDES
from config/private_cleaning_overrides.py if it exists, and falls back to
empty values (no-op) if it doesn't — so the public demo path never needs
this file at all.
"""

import datetime as dt

# Example only — replace with real (month, vendor, amount) -> date entries
# for any real transactions missing a date.
ESTIMATED_DATES = {
    ("2025-08", "Example Vendor", 100): dt.date(2025, 8, 1),
}

# Example only — replace with real vendor-based category corrections.
VENDOR_CATEGORY_OVERRIDES = [
    {
        "vendor_pattern": r"example\s*vendor",
        "target_category": "Other/Non-Operating",
        # Optional fields also supported: "desc_includes", "desc_excludes"
    },
]
