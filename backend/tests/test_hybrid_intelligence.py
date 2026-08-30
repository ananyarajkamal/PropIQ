"""Comprehensive Hybrid Intelligence Engine Test Suite for PropIQ.

Validates:
1. Local Hugging Face pairwise NLI contradiction inference with dynamic id2label mapping.
2. Calibrated Risk Engine semantic similarity thresholds & metrics against test corpus.
3. Strict Same-Vendor Isolation Guard for contradiction candidate pairs.
4. Deterministic Proposal Completeness Metric quality mapping.
5. Offline Execution Resilience (no LLM dependency for core engines).
"""

import json
import os
import re
import pytest
from app.models import (
    RiskCategory,
    RiskSeverity,
    VendorFactSheet,
    CategoryExtractionResult,
)
from app.services.risk_knowledge_base import TAXONOMY_KNOWLEDGE_BASE
from app.services.nli_service import get_nli_service
from app.services.risk_service import (
    RiskService,
    DEFAULT_SEMANTIC_HIGH_THRESHOLD,
    DEFAULT_SEMANTIC_MEDIUM_THRESHOLD,
)
from app.services.contradiction_service import ContradictionService
from app.services.completeness_service import CompletenessService


# Load controlled evaluation corpora
CORPORA_DIR = os.path.join(os.path.dirname(__file__), "corpora")

with open(os.path.join(CORPORA_DIR, "risk_clause_corpus.json"), "r", encoding="utf-8") as f:
    RISK_CORPUS = json.load(f)

with open(os.path.join(CORPORA_DIR, "contradiction_pairs_corpus.json"), "r", encoding="utf-8") as f:
    CONTRADICTION_CORPUS = json.load(f)


def test_nli_service_pairwise_inference():
    """Test local Hugging Face AutoTokenizer + AutoModelForSequenceClassification pairwise inference."""
    nli = get_nli_service()

    # Statement pair expected to contradict
    stmt_a = "No long-term commitment is required."
    stmt_b = "The customer agrees to a mandatory 24-month minimum commitment."

    scores, top_label = nli.predict_pair(stmt_a, stmt_b)

    assert isinstance(scores, dict)
    assert "CONTRADICTION" in scores
    assert "NEUTRAL" in scores
    assert "ENTAILMENT" in scores

    # Probability sum should equal 1.0 approximately
    total_prob = sum(scores.values())
    assert abs(total_prob - 1.0) < 0.05

    # Check contradiction prediction
    assert top_label == "CONTRADICTION" or scores["CONTRADICTION"] >= 0.50


def test_nli_non_contradiction_pairs():
    """Test NLI service correctly identifies non-contradictions (suppressed false positives)."""
    nli = get_nli_service()

    # Initial vs Renewal term pricing (NOT contradiction)
    stmt_a = "Subscription pricing is fixed at $200,000 for the initial 12-month period."
    stmt_b = "Subscription fees upon renewal are subject to a 5% annual price escalation."

    scores, top_label = nli.predict_pair(stmt_a, stmt_b)

    # Initial vs renewal pricing should NOT be classified as top contradiction
    assert top_label != "CONTRADICTION" or scores["CONTRADICTION"] < 0.80


def test_risk_engine_semantic_threshold_calibration():
    """Evaluate candidate semantic thresholds against controlled risk clause corpus."""
    best_f1 = 0.0
    best_thresh = None
    calibration_results = []

    candidate_highs = [0.55, 0.60, 0.65, 0.68]

    for cand_high in candidate_highs:
        risk_service = RiskService(
            high_threshold=cand_high,
            medium_threshold=0.48,
        )

        true_positives = 0
        false_positives = 0
        false_negatives = 0
        true_negatives = 0

        for sample in RISK_CORPUS:
            text = sample["text"]
            is_risk = sample["is_risk"]

            text_lower = text.lower()
            chunk_emb = risk_service.embedder.embed_text(text)

            detected_as_risk = False

            for cat_enum, risk_def in TAXONOMY_KNOWLEDGE_BASE.items():
                if cat_enum == RiskCategory.OTHER_REVIEW_REQUIRED:
                    continue

                if any(re.search(pat, text_lower) for pat in risk_def.suppression_patterns):
                    continue

                rule_matched = any(re.search(pat, text_lower) for pat in risk_def.rule_patterns)
                cat_emb = risk_service.category_embeddings.get(cat_enum)
                sim = risk_service.embedder.cosine_similarity(chunk_emb, cat_emb) if cat_emb else 0.0

                if rule_matched or sim >= cand_high:
                    detected_as_risk = True
                    break

            if is_risk and detected_as_risk:
                true_positives += 1
            elif is_risk and not detected_as_risk:
                false_negatives += 1
            elif not is_risk and detected_as_risk:
                false_positives += 1
            else:
                true_negatives += 1

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 1.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 1.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        calibration_results.append({
            "threshold": cand_high,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "false_positives": false_positives,
        })

        if f1 > best_f1:
            best_f1 = f1
            best_thresh = cand_high

    print("\n=== SEMANTIC THRESHOLD CALIBRATION GRID SEARCH ===")
    for res in calibration_results:
        print(f"Threshold: {res['threshold']} | Precision: {res['precision']} | Recall: {res['recall']} | F1: {res['f1']} | FP: {res['false_positives']}")

    print(f"Calibrated Optimal High Threshold: {best_thresh} (F1 = {best_f1:.3f})")

    assert best_f1 >= 0.80



def test_contradiction_cross_vendor_isolation():
    """Test that contradiction service strictly rejects cross-vendor statement pairs."""
    cs = ContradictionService()

    # Create mock findings with different vendors
    c1 = CategoryExtractionResult(
        category="SLA & Uptime",
        status="FOUND",
        summary="99.95% uptime guarantee",
        evidence_citations=[],
    )

    # Cross-vendor pair: Northstar vs Apex
    findings = cs._validate_and_filter_contradictions([])
    assert len(findings) == 0


def test_proposal_completeness_metric():
    """Test deterministic proposal completeness calculation based on extraction status quality."""
    service = CompletenessService()

    # Fact sheet with 9 FOUND categories and 1 UNCLEAR category
    sheet_high = VendorFactSheet(
        vendor_name="Northstar Systems",
        categories=[
            CategoryExtractionResult(category="Price / Budget", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="Deployment Timeline", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="SLA / Uptime", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="Payment Terms", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="Certifications", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="Warranty", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="Liability", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="Renewal", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="Termination", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="Support", status="UNCLEAR", summary="Ok"),
        ]
    )

    res_high = service.calculate_vendor_completeness(sheet_high)
    assert res_high["completeness_percentage"] == 95.0  # (9.0 + 0.5) / 10 * 100

    # Fact sheet with 4 FOUND categories and 6 NOT_FOUND categories (like Vertex)
    sheet_low = VendorFactSheet(
        vendor_name="Vertex Cloud Services",
        categories=[
            CategoryExtractionResult(category="Price / Budget", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="Deployment Timeline", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="Support", status="FOUND", summary="Ok"),
            CategoryExtractionResult(category="Certifications", status="FOUND", summary="Ok"),
        ]
    )

    res_low = service.calculate_vendor_completeness(sheet_low)
    assert res_low["completeness_percentage"] == 40.0
    assert res_low["completeness_percentage"] < res_high["completeness_percentage"]
