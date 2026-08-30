# PropIQ Evaluation Dataset & Ground Truth

These fictional vendor proposals and ground truth data are created solely for controlled evaluation of PropIQ. No real vendor or customer information is included.

## Fictional Synthetic Proposals (`evaluation/proposals/`)

1. **Northstar Systems (`northstar_systems_proposal.pdf`)**: Strongest overall candidate ($115k/yr, 30 days implementation, 99.95% SLA, Net 30, SOC 2 Type II, ISO 27001, 24/7 support, clear customer data ownership, but contains an auto-renewal clause).
2. **Meridian Labs (`meridian_labs_proposal.pdf`)**: Credible runner-up alternative ($98k/yr, 45 days implementation, 99.9% SLA, Net 45, SOC 2 Type II, ISO 27001 pending, 24/7 support).
3. **Apex Procurement Technologies (`apex_procurement_proposal.pdf`)**: Contradiction & contract risk test vendor ("No long-term commitment" vs 24-month auto-renewal; 30-day implementation vs 60 to 75 days SOW).
4. **Vertex Cloud Services (`vertex_cloud_services_proposal.pdf`)**: Missing-information detection test vendor ($120k/yr, but omits SLA %, liability cap, certification evidence, and termination terms).

## Ground Truth (`evaluation/ground_truth.json`)

`evaluation/ground_truth.json` contains independently defined expected evaluation findings for PDF parsing, text extraction, retrieval recall, structured fact extraction, terminology normalization, requirement comparison, contract risk detection, contradiction detection, missing information identification, vendor clarification quality, deterministic scoring, ranking order, and procurement recommendation state.

## Executing Evaluation Tests

Run the backend Phase 10 evaluation test suite:

```bash
cd backend
python -m pytest -v tests/test_phase10_evaluation.py
```
