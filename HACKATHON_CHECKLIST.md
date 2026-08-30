# PropIQ Hackathon Submission Checklist

- [x] Repository cleaned of debug logs, temporary uploads, and `.env` secrets
- [x] Comprehensive `README.md` finalized with project overview, architecture diagram, usage flow, and privacy model
- [x] 4 Fictional synthetic proposal PDFs available in `evaluation/proposals/`
- [x] Independent ground truth JSON fixture available in `evaluation/ground_truth.json`
- [x] Evaluation dataset documentation available in `evaluation/README.md`
- [x] Deployment guide available in `DEPLOYMENT_CHECKLIST.md`
- [x] Presentation script available in `PRESENTATION_SCRIPT.md` (3-minute demo script)
- [x] All 142 backend unit, security, resilience, failure handling, pre-session IP rate limiting, operation locking, and evaluation tests passing (`python -m pytest -v`)
- [x] Frontend React production build compiling cleanly (`cmd /c npm run build`)
- [x] Health endpoint returning valid status (`GET /api/health`)
- [x] Zero hardcoded secrets committed to git
