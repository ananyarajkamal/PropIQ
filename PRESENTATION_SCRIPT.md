# PropIQ 3-Minute Hackathon Demo Script

## Timing Breakdown

- **0:00 – 0:20 | Problem Statement**
  "Procurement teams often receive vendor proposals that look similar on the surface but use different pricing structures, timelines, service terms, and contractual language. Manually evaluating complex proposals takes days and risks missing hidden auto-renewal clauses, liability caps, or conflicting terms. PropIQ turns those raw proposal PDFs into a single evidence-backed decision workflow."

- **0:20 – 0:40 | Proposal Upload & Requirements Setup**
  "Here we start an analysis by uploading proposal PDFs from four enterprise software vendors: Northstar Systems, Meridian Labs, Apex Procurement Technologies, and Vertex Cloud Services. We define our procurement criteria: budget ceiling of $120,000, 30-day implementation timeline, 99.9% SLA, SOC 2 and ISO 27001 certifications, Net 30 payment terms, and 24/7 support."

- **0:40 – 1:05 | Comparison & Terminology Normalization**
  "Different vendors express commercial terms differently. PropIQ automatically normalizes these values. For example, Northstar's proposal states an implementation duration of 720 hours—PropIQ normalizes 720 hours to 30 days before evaluating it against our 30-day requirement. Every status tag—MEETS, PARTIAL, FAILS, or MISSING—is backed by page-traceable evidence citations."

- **1:05 – 1:35 | Contradiction & Contract Risk Intelligence**
  "PropIQ identifies contract risks and intra-vendor statement contradictions. In the Apex proposal, the Executive Summary claims 'No long-term commitment.' However, PropIQ flags a conflicting 24-month automatic renewal clause later in Section 5, presenting side-by-side evidence citations for both statements."

- **1:35 – 1:55 | Missing Information & Clarification Questions**
  "When information is missing or unclear, PropIQ does not guess or hallucinate. In the Vertex proposal, SLA percentage and liability cap terms are omitted. PropIQ marks these as MISSING and automatically generates targeted clarification questions ready to copy or download as an export file."

- **1:55 – 2:25 | Deterministic Scoring & Transparent Ranking**
  "PropIQ ranks vendors using 100% deterministic Python math based on requirement weights, risk penalties, contradiction penalties, and clarification gaps—zero LLM calls are involved in calculating scores. Northstar Systems leads with an alignment score of 88.0 out of 100."

- **2:25 – 2:50 | Evidence-Backed Executive Recommendation**
  "Finally, PropIQ produces an Executive Decision Brief. Northstar Systems is recommended with conditions due to an auto-renewal clause. If a vendor receives a critical contract risk, PropIQ's deterministic guardrails automatically shift the recommendation state to 'Further Review Required' without relying on LLM decision-making."

- **2:50 – 3:00 | Privacy Model & Summary**
  "Privacy is built into the core: proposals are parsed and indexed locally using sentence-transformers and FAISS. Only relevant excerpts are sent to Groq when reasoning is required. PropIQ delivers speed, transparency, and evidence-grounded confidence for enterprise procurement teams."
