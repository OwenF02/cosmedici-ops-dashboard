# Lead Scoring Rubric (V1 — Rule-Based)

This is the actual production logic for the Lead Priority Scorer at launch. It's built from business judgment, not historical data — no real labeled lead-outcome data exists yet (that's the whole reason this launches rule-based instead of as a trained model; see `decision_log.md`). Treat every weight here as a first draft, expected to be revisited once the lead intake log has accumulated real outcomes (target: ~3 months post-launch, per the retraining milestone in `project_scope.md`).

## Design principle: score what's knowable at intake

The score is computed the moment a new lead comes in — before anyone has responded to it — because its purpose is to tell staff who to call first. That means `first_response_time_hours` and `follow_up_count_at_first_contact` are **not** inputs to this score, even though they're captured in the schema. They can't be known yet for a brand-new lead; they're recorded afterward purely as historical data, to be used as features if a real ML model becomes viable later. Scoring a lead on how fast someone already responded to it would be circular.

## What's scored vs. what's tracked-only

Two factors have real signal behind them right now, based on what you've observed running the business. The rest are tracked in the schema for reporting and future pattern discovery, but don't move the score yet — there's no basis to weight them without guessing, and guessing here would undermine the whole "honest, evidence-based" framing of the project.

**Scored:**
- **Message type** — the clearest available signal of buying intent.
- **Discount mentioned/offered** — you've observed discount-driven leads still convert well, so this is a positive signal, not a penalty.

**Tracked, not scored (yet):**
- **Lead source** — no clear conversion pattern across Fresha / Meta / Instagram / Website yet, so it isn't weighted. Once the intake log has enough real outcomes, check whether a pattern emerges.
- **Service interest** — Laser Hair Removal, Injectables, Skin Treatments/Facials, and Body Contouring/Wellness are all in scope and currently treated as equally likely to convert, since there's no observed difference yet. Worth revisiting once ticket values or real conversion rates by service are known.
- **Day of week / time of day received** — logged for pattern discovery (e.g., do weekend inquiries convert differently?) but not scored.

## Scoring Logic

**Step 1 — Message type base score (0–70 points):**

| Message type | Points | Rationale |
|---|---|---|
| Direct booking request | 70 | Explicit intent to book — the strongest possible signal. |
| Availability question | 60 | "Do you have anything open this week?" — time-sensitive, usually close to booking. |
| Price/cost question | 45 | Actively evaluating a purchase decision. |
| General service question | 25 | Early-stage curiosity, intent unclear. |
| Other | 15 | Doesn't fit a known pattern — treated conservatively until observed otherwise. |

**Step 2 — Discount bonus (0 or +30 points):**

| Condition | Points |
|---|---|
| Discount mentioned or offered | +30 |
| No discount involved | +0 |

**Step 3 — Total and label:**

`priority_score = message_type_points + discount_bonus` (0–100)

| Score range | Priority label |
|---|---|
| 70–100 | High |
| 35–69 | Medium |
| 0–34 | Low |

## Example Output

```text
Priority: High
Score: 90 / 100
Reasons:
- Availability question — time-sensitive, usually close to booking (60 pts)
- Discount mentioned — discount-driven leads have converted well historically (+30 pts)
```

```text
Priority: Low
Score: 25 / 100
Reasons:
- General service question — early-stage curiosity, intent unclear (25 pts)
- No discount involved (+0 pts)
```

## Field Reference

See `data/leads_intake_template.csv` for the exact column layout. Value sets for categorical fields:

- **source:** Fresha, Meta/Instagram DM, Website Contact Form, Other
- **service_interest:** Laser Hair Removal, Injectables (Botox/Filler), Skin Treatments/Facials, Body Contouring/Wellness, Other
- **message_type:** Direct Booking Request, Availability Question, Price/Cost Question, General Service Question, Other
- **discount_offered:** Yes, No
- **outcome:** booked, no_show, no_response, declined, pending — see the Conversion Label Definition in `project_scope.md` for how this maps to a future ML target.

## Revisiting This Rubric

Once the intake log has real outcomes to look at (target: ~3 months post-launch), re-check:
1. Does lead source actually predict conversion? If so, add it as a scored factor.
2. Do the four service categories convert at meaningfully different rates? If so, weight them.
3. Are the message-type point values in the right relative order — does a booking request really convert better than an availability question, or did this rubric guess wrong?
4. Is the discount bonus the right size, or should it be larger/smaller than 30 points relative to message type's 70?

Log any changes made here in `decision_log.md`, same as every other rubric decision.
