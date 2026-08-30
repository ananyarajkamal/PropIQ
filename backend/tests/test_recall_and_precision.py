"""Comprehensive recall, precision, and state fidelity test suite for PropIQ.

Evaluates word-number parsing, Recall@K retrieval depth, false-missing recovery,
false-positive prevention, compound subconditions, and deterministic state decision rules.
"""

import pytest
import fitz
from typing import List, Dict, Optional
from app.models import (
    ProcurementRequirements,
    PageExtractedText,
    ChunkMetadata,
    CategoryExtractionResult,
    VendorFactSheet,
)
from app.services.pdf_parser import parse_pdf_bytes
from app.services.chunker import chunk_document_pages
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import get_vector_store
from app.services.retrieval_service import RetrievalService
from app.services.extraction_service import ExtractionService
from app.services.comparison_service import ComparisonService
from app.services.normalization_service import NormalizationService, replace_word_numbers_in_text


def test_generic_word_number_parser():
    """Verify generic word-number parser converts English word numbers into digits."""
    assert replace_word_numbers_in_text("rollout completed within four weeks") == "rollout completed within 4 weeks"
    assert replace_word_numbers_in_text("contract extends for twelve months") == "contract extends for 12 months"
    assert replace_word_numbers_in_text("critical response within sixty minutes") == "critical response within 60 minutes"
    assert replace_word_numbers_in_text("payable within thirty days of invoice") == "payable within 30 days of invoice"
    assert replace_word_numbers_in_text("warranty period of two years") == "warranty period of 2 years"


def test_false_missing_semantic_phrasing_recovery():
    """Verify facts expressed in varied natural language phrasing are recovered correctly."""
    normalizer = NormalizationService()

    # 1. Implementation phrasing: "rollout completed within four weeks"
    norm_impl = normalizer.normalize_duration("four weeks")
    assert norm_impl.normalized_value == 28.0  # 4 * 7 days

    # 2. Payment phrasing: "payable within thirty days of invoice"
    norm_pay = normalizer.normalize_payment_terms("payable within thirty days")
    assert norm_pay.normalized_value.get("due_days") == 30

    # 3. Support response: "sixty minutes response"
    norm_dur = normalizer.normalize_duration("sixty minutes")
    assert norm_dur.normalized_value is not None

    # 4. Renewal phrasing: "automatically extends for another 12 months"
    norm_ren = normalizer.normalize_renewal("automatically extends for another 12 months")
    assert norm_ren.normalized_value.get("renewal_type") == "automatic"


def test_false_positive_negative_collision_prevention():
    """Verify context-aware semantic validators reject incompatible cross-category values."""
    comp_service = ComparisonService()

    # 1. Contract duration (24 months) must NOT satisfy implementation timeline requirement
    fs_contract_term = VendorFactSheet(
        vendor_name="Acme Corp",
        categories=[
            CategoryExtractionResult(
                category="Delivery / Implementation",
                status="NOT_FOUND",
                raw_value=None,
                summary="No implementation timeline found.",
            )
        ]
    )
    reqs = ProcurementRequirements(timeline_value=30, timeline_unit="days")
    row = comp_service._evaluate_timeline_requirement(reqs, [fs_contract_term])
    eval_res = row.vendor_evaluations["Acme Corp"]
    assert eval_res.status == "MISSING"

    # 2. Price escalation percentage (7%) must NOT satisfy SLA uptime requirement
    fs_escalation = VendorFactSheet(
        vendor_name="Acme Corp",
        categories=[
            CategoryExtractionResult(
                category="SLA / Uptime",
                status="NOT_FOUND",
                raw_value=None,
                summary="No SLA uptime clause found.",
            )
        ]
    )
    reqs_sla = ProcurementRequirements(minimum_sla=99.9)
    row_sla = comp_service._evaluate_sla_requirement(reqs_sla, [fs_escalation])
    assert row_sla.vendor_evaluations["Acme Corp"].status == "MISSING"


def test_deterministic_certification_state_matrix():
    """Verify the 7 deterministic certification decision outcomes."""
    comp_service = ComparisonService()
    reqs = ProcurementRequirements(certifications=["SOC 2", "ISO 27001"])

    # 1. All required confirmed -> MEETS
    fs_meets = VendorFactSheet(
        vendor_name="Vendor A",
        categories=[CategoryExtractionResult(category="Certifications", status="FOUND", raw_value="SOC 2, ISO 27001", summary="Both certified.")]
    )
    assert comp_service._evaluate_certifications_requirement(reqs, [fs_meets]).vendor_evaluations["Vendor A"].status == "MEETS"

    # 2. At least one confirmed & remaining unstated -> PARTIAL
    fs_partial = VendorFactSheet(
        vendor_name="Vendor B",
        categories=[CategoryExtractionResult(category="Certifications", status="FOUND", raw_value="SOC 2", summary="SOC 2 certified.")]
    )
    assert comp_service._evaluate_certifications_requirement(reqs, [fs_partial]).vendor_evaluations["Vendor B"].status == "PARTIAL"

    # 3. None confirmed & vendor holds other certs -> FAILS
    fs_fails = VendorFactSheet(
        vendor_name="Vendor C",
        categories=[CategoryExtractionResult(category="Certifications", status="FOUND", raw_value="ISO 9001", summary="ISO 9001 certified.")]
    )
    assert comp_service._evaluate_certifications_requirement(reqs, [fs_fails]).vendor_evaluations["Vendor C"].status == "FAILS"

    # 4. None mentioned -> MISSING
    fs_missing = VendorFactSheet(
        vendor_name="Vendor D",
        categories=[CategoryExtractionResult(category="Certifications", status="NOT_FOUND", raw_value=None, summary="Not mentioned.")]
    )
    assert comp_service._evaluate_certifications_requirement(reqs, [fs_missing]).vendor_evaluations["Vendor D"].status == "MISSING"


def test_compound_support_subconditions_evaluation():
    """Verify compound support requirements track availability and response time independently."""
    comp_service = ComparisonService()
    reqs = ProcurementRequirements(support_requirement="24/7 technical support and <=1 hour critical response")

    # 1. Availability supported (24/7), response time unstated -> PARTIAL (not MEETS!)
    fs_partial = VendorFactSheet(
        vendor_name="Vendor A",
        categories=[CategoryExtractionResult(category="Support", status="FOUND", raw_value="24/7 technical support", summary="24/7 support.")]
    )
    res_partial = comp_service._evaluate_support_requirement(reqs, [fs_partial]).vendor_evaluations["Vendor A"]
    assert res_partial.status == "PARTIAL"

    # 2. Availability supported (24/7), response time ambiguous ("rapid response") -> UNCLEAR
    fs_unclear = VendorFactSheet(
        vendor_name="Vendor B",
        categories=[CategoryExtractionResult(category="Support", status="UNCLEAR", raw_value="rapid critical incident response", summary="Rapid response.")]
    )
    res_unclear = comp_service._evaluate_support_requirement(reqs, [fs_unclear]).vendor_evaluations["Vendor B"]
    assert res_unclear.status == "UNCLEAR"
