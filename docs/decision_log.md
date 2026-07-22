# Decision Log

Records the reasoning behind key project decisions as they're made — this is what lets a recruiter (or future you) understand *why* the project looks the way it does, not just what it does.

| Date | Decision | Reason |
|---|---|---|
| Week 1 | Lead model starts rule-based, not ML | No real labeled non-converted lead data exists yet; forcing a model would mean training on fabricated labels |
| Week 1 | Public/private data split architected via folder structure + config flag, not convention | Real business data must never accidentally reach the public repo; needs to be structurally enforced, not just remembered |
| Week 1 | Expense classifier trained on real data from launch | ~1,000+ real expense/revenue lines (Aug 2025–June 2026) exist — enough to train on legitimately, unlike leads |
| Week 1 | Revenue and expense records kept as separate datasets/tables | Different reporting purposes; combining them would blur the P&L view and complicate both the cleaning and modeling steps |
| Week 1 | Expense classifier compares classical baseline vs. PyTorch vs. Keras | Legitimate portfolio use of both deep learning frameworks via transfer learning (pretrained text embeddings on vendor/description), not forced onto a problem that doesn't need it |
| Week 1 | Best-performing expense model wins production; comparison documented honestly | Avoids shipping a deep learning model just because it's more impressive-sounding if a simpler model actually performs better |
| Week 1 | Real-trained model files never committed to GitHub | Model weights/embeddings can encode real vendor names, category patterns, and financial ranges even without a data file present |
| Week 1 | Public demo ships a separately trained synthetic-data model (`models/public/`) | Keeps the public Streamlit demo functional without exposing any real-data-trained artifact |
| Week 1 | `no_show` maps to "converted" in the lead conversion label | The lead booked — that's what lead-gen/follow-up measures. No-show is a downstream scheduling/reminder problem, tracked separately, not folded into the conversion label |
| Week 1 | Pending leads auto-resolve to `no_response` after 30 days | Prevents an ever-growing pool of unusable "pending" leads from shrinking the effective training set over time |
| Week 1 | `expense_corrections` table schema defined in Sprint 2, not Sprint 4 | Needed to exist before Sprint 4 starts logging real corrections; better to design the schema without app-building time pressure |
| Week 1 | "Lead Predictor" page renamed to "Lead Priority Scorer" | The system is rule-based at launch, not predictive — the name shouldn't overstate what it does, to staff or in the portfolio |
| Week 1 | SQLite backup plan (WAL mode, automated daily backups, off-machine copy) built in Sprint 2, before real data accumulates | A single-file database has exactly one copy unless backups are deliberately built in from the start |
| Week 2 | Final category list locked at 13, matching Jan–Jun 2026 actuals | Real bookkeeping data confirmed this over the earlier placeholder and June-only estimate; "Other/Non-Operating" serves as the catch-all |
| Week 2 | Aug–Dec 2025 legacy categories mapped via crosswalk rather than discarded | Preserves 5 extra months of training data; ambiguous cases (e.g. "Machine Payment") routed to Other rather than guessed |
| Week 2 | Lead priority score computed only from fields knowable at intake (message type, discount) | `response_time` and `follow_up_count` don't exist yet for a brand-new lead — scoring on them would be circular. They're still captured, just for future ML training, not the real-time score |
| Week 2 | Lead source and service interest tracked but not scored in the V1 rubric | No observed conversion pattern across sources or across the four service categories yet; scoring them now would mean inventing weights with no basis. Revisit once real intake-log outcomes exist |
| Week 2 | Discount mentioned/offered scored as a positive (+30 pts), not a penalty | Based on direct observation that discount-driven leads still convert well, contrary to the common assumption that price-sensitivity signals a weaker lead |
| Week 2 | Message type is the dominant scoring factor (0–70 of 100 points) | The only field with a clear, ordered intent signal (booking request > availability question > price question > general question) available without real outcome data |
| Week 2 | Real-time website (Duda) lead sync deferred post-launch; manual/CSV entry only for now | Duda supports contact-form webhooks, but the local business-mode app is intentionally not publicly reachable, so real-time sync needs a paid Duda Zapier tier plus an intermediary (e.g. Zapier → Google Sheet → local import). Not worth the added cost/scope before seeing actual manual-entry volume post-launch |
| Week 2 | Staff access via local hostname (`<computer-name>.local:8501`) with the app set to auto-start on boot | Avoids a changing IP address breaking a bookmarked link, and avoids staff hitting a dead link because the app wasn't manually launched that day. Full setup steps to be written into `business_use_guide.md` in Sprint 4 |
| Week 3 | `$0` expense rows dropped as data artifacts, not treated as a real category | Only one such row exists across all 12 months, with no date/vendor/category/payment method populated — not a genuine transaction |
| Week 3 | "Refund" revenue rows kept positive, not flipped to negative | Confirmed these represent funds returned *to* Cosmedici (tied to a Maryland Comptroller registration gap), not refunds paid out to clients — the existing positive sign is already correct |
