"""
Sprint 2 — synthetic public sample generator.

Produces data/expenses_sample.csv and data/leads_sample.csv: fully
fabricated data, safe for the public GitHub repo. Nothing here is derived
from real Cosmedici records - vendor names, amounts, and lead details are
all synthetic. The expense category *distribution* (row-count proportions
and rough amount ranges per category) is modeled after the real cleaned
data so the public demo model trains on a realistic-shaped problem, but no
real value is copied in.

Usage:
    python src/generate_synthetic_samples.py
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

OUT_DIR = Path(__file__).resolve().parent.parent / "data"

# ---------------------------------------------------------------------------
# Expense sample
# ---------------------------------------------------------------------------

# (category, row-count weight, amount_min, amount_median, amount_max) -
# weights and amount ranges are modeled on the real Aug2025-Jul2026 data's
# shape, not copied from it.
CATEGORY_PROFILE = [
    ("Payroll & Labor", 383, 20, 385, 2500),
    ("Other/Non-Operating", 144, 5, 135, 2800),
    ("Marketing & Growth", 121, 5, 25, 999),
    ("Cost of Services (Clinical Supplies)", 94, 15, 118, 1789),
    ("Software & Technology", 69, 3, 25, 195),
    ("Debt Services", 49, 25, 400, 1900),
    ("Occupancy Cost", 45, 20, 787, 2250),
    ("Owner Distribution (Non-Operating)", 45, 50, 1000, 5225),
    ("Banking & Financial Fees", 38, 2, 38, 1543),
    ("Repairs, Maintenance & Small Equipment", 19, 10, 61, 4657),
    ("Licensing & Compliance", 15, 5, 58, 2500),
    ("Insurance", 12, 40, 105, 2000),
    ("Professional Services", 10, 20, 452, 2500),
]

VENDOR_POOL = {
    "Payroll & Labor": ["Staff Payroll Run", "Front Desk Payroll", "Contract Esthetician Pay", "Payroll Tax Deposit"],
    "Other/Non-Operating": ["Office Supply Co", "Miscellaneous Purchase", "Break Room Supplies", "General Store Purchase"],
    "Marketing & Growth": ["Social Ads Platform", "Search Ads Platform", "Local Print Promo Co", "Referral Program Payout"],
    "Cost of Services (Clinical Supplies)": ["Injectable Supply Distributor", "Skincare Product Restock", "Disposable Clinic Supplies Co", "Medical Supply Wholesaler"],
    "Software & Technology": ["Booking Software Subscription", "Cloud Storage Plan", "Point-of-Sale Software", "Scheduling App Fee"],
    "Debt Services": ["Equipment Loan Payment", "Line of Credit Interest", "Financing Payment"],
    "Occupancy Cost": ["Suite Rent - Main Location", "Electric Utility Co", "Water & Sewer Utility", "CAM Fee"],
    "Owner Distribution (Non-Operating)": ["Owner Draw"],
    "Banking & Financial Fees": ["Merchant Processing Fee", "Bank Monthly Fee", "Wire Transfer Fee"],
    "Repairs, Maintenance & Small Equipment": ["HVAC Repair Co", "Equipment Tune-Up Service", "Small Tools Purchase", "Facility Repair Co"],
    "Licensing & Compliance": ["State Business License Renewal", "Professional Certification Fee", "Local Permit Office"],
    "Insurance": ["Malpractice Insurance Premium", "General Liability Policy", "Property Insurance Premium"],
    "Professional Services": ["Bookkeeping Services", "Legal Consultation", "Tax Prep Services"],
}

PAYMENT_METHODS = ["Bank Transfer", "Zelle", "Check", "Business Debit", "Cash", "Credit Card"]


def gen_amount(lo, med, hi):
    # Skewed toward the median, occasionally hitting the tails - mirrors the
    # long-tail shape seen in the real per-category amount distributions.
    r = random.random()
    if r < 0.7:
        val = random.uniform(lo, med)
    elif r < 0.95:
        val = random.uniform(med, med + (hi - med) * 0.4)
    else:
        val = random.uniform(med + (hi - med) * 0.4, hi)
    return round(max(lo, val), 2)


def random_date_in_window(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_expenses():
    start, end = date(2025, 8, 1), date(2026, 7, 31)
    rows = []
    expense_id = 1
    for category, count, lo, med, hi in CATEGORY_PROFILE:
        vendors = VENDOR_POOL[category]
        for _ in range(count):
            vendor = random.choice(vendors)
            rows.append(
                {
                    "expense_id": expense_id,
                    "date": random_date_in_window(start, end).isoformat(),
                    "vendor_name": vendor,
                    "category": category,
                    "description": vendor,
                    "amount": gen_amount(lo, med, hi),
                    "payment_method": random.choice(PAYMENT_METHODS),
                }
            )
            expense_id += 1
    random.shuffle(rows)
    for i, row in enumerate(rows, start=1):
        row["expense_id"] = i
    rows.sort(key=lambda r: r["date"])
    for i, row in enumerate(rows, start=1):
        row["expense_id"] = i
    return rows


# ---------------------------------------------------------------------------
# Leads sample - built from docs/lead_scoring_rubric.md's V1 scoring rules:
# message type (0-70 pts) + discount bonus (0/+30), bands High 70-100 /
# Medium 35-69 / Low 0-34.
# ---------------------------------------------------------------------------

MESSAGE_TYPES = [
    ("Direct booking request", 70, 0.20),
    ("Availability question", 60, 0.25),
    ("Price or cost question", 45, 0.25),
    ("General service question", 25, 0.20),
    ("Other", 15, 0.10),
]

SOURCES = ["Fresha", "Meta/Instagram/Facebook DMs", "Website Contact Form"]
SERVICES = ["Laser Hair Removal", "Injectables (Botox/Filler)", "Skin Treatments/Facials", "Body Contouring/Wellness"]
STATUSES = ["New", "Contacted", "Booked", "No Response"]

NOTE_TEMPLATES = {
    "Direct booking request": "Asked to book an appointment for {service}.",
    "Availability question": "Asked what times are open this week for {service}.",
    "Price or cost question": "Asked how much {service} costs.",
    "General service question": "Asked general questions about {service}.",
    "Other": "Inquiry not clearly tied to a specific service.",
}


def score_lead(message_type_points: int, discount_requested: bool) -> tuple[int, str]:
    score = message_type_points + (30 if discount_requested else 0)
    score = min(score, 100)
    if score >= 70:
        label = "High"
    elif score >= 35:
        label = "Medium"
    else:
        label = "Low"
    return score, label


def generate_leads(n=180):
    start, end = date(2025, 8, 1), date(2026, 7, 31)
    types, weights = zip(*[(t, w) for t, _, w in MESSAGE_TYPES])
    points_lookup = {t: p for t, p, _ in MESSAGE_TYPES}

    rows = []
    for lead_id in range(1, n + 1):
        message_type = random.choices(types, weights=weights, k=1)[0]
        discount_requested = random.random() < 0.30
        score, label = score_lead(points_lookup[message_type], discount_requested)
        service = random.choice(SERVICES)
        rows.append(
            {
                "lead_id": lead_id,
                "date_received": random_date_in_window(start, end).isoformat(),
                "source": random.choice(SOURCES),
                "service_interest": service,
                "message_type": message_type,
                "discount_requested": "Yes" if discount_requested else "No",
                "priority_score": score,
                "priority_label": label,
                "status": random.choice(STATUSES),
                "notes": NOTE_TEMPLATES[message_type].format(service=service),
            }
        )
    rows.sort(key=lambda r: r["date_received"])
    for i, row in enumerate(rows, start=1):
        row["lead_id"] = i
    return rows


def write_csv(rows, path: Path):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    expenses = generate_expenses()
    leads = generate_leads()
    write_csv(expenses, OUT_DIR / "expenses_sample.csv")
    write_csv(leads, OUT_DIR / "leads_sample.csv")
    print(f"Wrote {len(expenses)} synthetic expense rows -> {OUT_DIR / 'expenses_sample.csv'}")
    print(f"Wrote {len(leads)} synthetic lead rows -> {OUT_DIR / 'leads_sample.csv'}")


if __name__ == "__main__":
    main()
