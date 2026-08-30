# PropIQ

AI Procurement Intelligence for Smarter Vendor Decisions

PropIQ is an AI-powered procurement intelligence platform designed to help teams analyze and compare vendor proposals. It transforms complex proposal documents into structured commercial and technical insights, identifies contractual concerns and contradictions, surfaces missing information, generates clarification questions, and supports evidence-backed vendor evaluation.

## The Problem

Procurement teams regularly evaluate complex vendor response proposals submitted in non-standard PDF formats. These proposals contain differing:

- Pricing structures and subscription terms
- Implementation timelines and deployment milestones
- Service level agreement (SLA) uptime guarantees
- Payment and invoicing terms
- Security and compliance certifications
- Software functionality warranties
- Liability caps and indemnity provisions
- Renewal clauses and automatic renewal terms
- Termination restrictions and fees
- Support tier commitments

Manual comparison across multi-page proposals is slow, error-prone, and key contractual differences or hidden risk clauses can easily be overlooked.

## The Solution

PropIQ turns unstructured vendor proposal documents into an interactive, evidence-grounded procurement decision workflow. By combining high-speed document parsing, local semantic vector search, structured fact extraction, and deterministic scoring, PropIQ enables procurement leaders to evaluate vendor proposals rapidly and objectively.

## Key Features

- **Proposal PDF Parsing**: Automated extraction of text and metadata across multi-page vendor response PDFs using PyMuPDF.
- **Structured Fact Extraction**: Automated extraction of core commercial, technical, SLA, and legal terms into structured schemas.
- **Requirement-Based Comparison**: Side-by-side comparison matrix evaluating vendor proposals against customizable business requirements.
- **Terminology and Unit Normalization**: Standardized conversion of varying units (e.g. converting 720 hours into 30 days, or mapping uptime SLAs to percentages).
- **Evidence-Backed Citations**: Page-level document citations for extracted facts and requirement evaluation cells.
- **Risky Clause Detection**: Automated identification of contractual risk items (e.g. automatic renewal locks, uncapped liability, or short termination windows).
- **Contradiction Detection**: Cross-clause inconsistency detection within vendor proposals.
- **Missing Information Detection**: Automated detection of omitted requirement details (e.g. missing SLA definitions or unstated warranty periods).
- **Vendor Clarification Questions**: Automated generation of prioritized clarification questions to send to vendors before contract award.
- **Deterministic Vendor Scoring**: Weighted alignment scoring engine evaluating requirements compliance while applying bounded risk, contradiction, and clarification penalties.
- **Vendor Ranking**: Multi-tier vendor stack ranking highlighting overall alignment leaders and conditional candidates.
- **Executive Recommendation Brief**: Generated executive decision brief summarizing top candidates, key trade-offs, and pre-award items to confirm.

## How PropIQ Works

1. Upload vendor proposals (PDF format)
2. Define procurement requirements
3. Extract and normalize proposal facts
4. Compare vendors against requirements
5. Analyze risks and contradictions
6. Identify missing information
7. Generate clarification questions
8. Score and rank vendors
9. Generate the recommendation brief

## Intelligence Pipeline

```
PDF Proposal
    │
    ▼
Document Parsing (PyMuPDF)
    │
    ▼
Text Chunking & Local Embeddings (Sentence Transformers)
    │
    ▼
FAISS Evidence Retrieval Index
    │
    ▼
Structured Fact Extraction & Reasoning (Groq API)
    │
    ▼
Unit & Terminology Normalization
    │
    ▼
Requirement Comparison Matrix
    │
    ▼
Risk & Contradiction Analysis
    │
    ▼
Clarification Question Generation
    │
    ▼
Deterministic Weighted Scoring
    │
    ▼
Vendor Stack Ranking
    │
    ▼
Executive Recommendation Brief
```

## What Makes PropIQ Different

- **Evidence-Grounded Analysis**: Every evaluated requirement status, risk finding, and clarification question is linked to page-level document citations.
- **Semantic Vector Retrieval**: Uses local vector search to retrieve precise document passages rather than passing raw multi-page files directly to prompts.
- **Deterministic Scoring Engine**: Uses transparent weighted mathematical formulas for vendor scoring rather than allowing an LLM to arbitrarily select a winner.
- **Terminology Normalization**: Automatically converts varying timeline units, pricing structures, and SLA terms into standard units for side-by-side comparison.
- **Clause-Level Risk and Contradiction Detection**: Identifies hidden automatic renewal provisions, liability gaps, and conflicting statements inside vendor documents.

## Example Intelligence

*(Illustrative generic examples)*

**Example 1: Unit Normalization**
- Proposal Wording: Total active setup duration is 720 hours.
- Evaluated Requirement: Maximum deployment timeline of 30 days.
- Normalized Result: 30 days (MEETS).

**Example 2: Contradiction Detection**
- Executive Summary Wording: No long-term commitment required for our flexible package.
- Contract Terms Wording: Agreement automatically renews for an additional 24-month term.
- Intelligence Finding: Potential contradiction detected between executive marketing summary and legal renewal terms.

## Technology Stack

- **Frontend**: React, Vite, JavaScript, Vanilla CSS
- **Backend**: FastAPI, Python 3.11+
- **Document Processing**: PyMuPDF (fitz)
- **Retrieval & Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2), FAISS
- **AI Reasoning**: Groq API
- **Data Validation**: Pydantic v2
- **Testing**: Pytest

## Architecture

- **React Frontend**: Single-page application providing an interactive procurement workspace, requirement definition controls, side-by-side comparison matrices, risk dashboards, ranking cards, and recommendation brief tools.
- **FastAPI Backend REST API**: Exposes structured API endpoints for PDF document processing, FAISS vector search, structured fact extraction, requirement comparison, risk analysis, clarification generation, deterministic scoring, and recommendation generation.

## Project Structure

```
PropIQ/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── services/
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── validators.py
│   └── tests/
├── evaluation/
│   ├── generate_synthetic_pdfs.py
│   ├── ground_truth.json
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── styles/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm 9 or higher

### Backend Setup

1. Navigate to the backend directory:

```bash
cd backend
```

2. Create and activate a Python virtual environment:

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\activate
```

Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install required Python dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables:

Copy the environment template from the root directory:

```bash
cp ../.env.example .env
```

Edit `.env` and provide your Groq API key:

```env
GROQ_API_KEY=your_actual_groq_api_key_here
FRONTEND_ORIGIN=http://localhost:5173
```

5. Start the backend FastAPI server:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend server will run at `http://127.0.0.1:8000`.

### Frontend Setup

1. Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

2. Install Node.js dependencies:

```bash
npm install
```

3. Start the Vite development server:

```bash
npm run dev
```

The frontend application will run at `http://localhost:5173`.

## Environment Variables

| Variable | Description | Required | Default |
| :--- | :--- | :---: | :--- |
| `GROQ_API_KEY` | API key for the backend Groq reasoning service | Yes | None |
| `FRONTEND_ORIGIN` | Allowed origin for backend CORS configuration | Yes | `http://localhost:5173` |

## Running Tests

### Backend Automated Test Suite

To run the backend Pytest test suite:

```bash
cd backend
python -m pytest -v
```

### Frontend Build Verification

To verify the production build of the frontend application:

```bash
cd frontend
npm run build
```

## Current Scope

PropIQ is currently designed as a procurement intelligence MVP developed for evaluation and hackathon demonstration. It provides end-to-end proposal analysis, structured comparison, risk detection, deterministic scoring, vendor ranking, and executive decision briefs.

## Disclaimer

PropIQ is a procurement decision-support tool. Findings, risk detections, and recommendation briefs provided by PropIQ are intended to assist decision-making and should be reviewed by appropriate procurement, financial, technical, and legal professionals prior to final vendor selection or contract award.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
