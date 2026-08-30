"""Structured procurement extraction service module for PropIQ.

Orchestrates category-specific vector retrieval, Evidence Pack creation,
Groq (llama-3.3-70b) extraction, and strict backend citation validation.
"""

import re
import time
import logging
from typing import Any, Dict, List, Optional, Set

from app.config import Config
from app.models import (
    ProcurementRequirements,
    CategoryExtractionResult,
    EvidenceCitationModel,
    VendorFactSheet,
    ExtractionResponse,
    ChunkMetadata,
)
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import get_vector_store
from app.services.retrieval_service import RetrievalService, SessionNotFoundError
from app.services.groq_service import (
    GroqService,
    GroqNotConfiguredError,
    GroqTimeoutError,
    GroqRateLimitError,
)

from app.services.normalization_service import NormalizationService, replace_word_numbers_in_text

logger = logging.getLogger("propiq_backend")

# Baseline procurement category retrieval concepts with concise semantic query variants
BASELINE_CATEGORY_QUERIES: Dict[str, List[str]] = {
    "Pricing": [
        "contract price total fees annual cost subscription cost",
        "implementation licensing fee pricing schedule USD",
    ],
    "Payment Terms": [
        "payment terms Net 30 invoice due date",
        "upfront payment billing schedule payable days",
    ],
    "Delivery / Implementation": [
        "implementation timeline deployment schedule",
        "rollout timeframe onboarding go-live duration",
    ],
    "SLA / Uptime": [
        "service level agreement uptime target availability",
        "service credits SLA percentage monthly uptime",
    ],
    "Warranty": [
        "warranty coverage defect warranty period",
        "service warranty guarantee duration replacement",
    ],
    "Certifications": [
        "security certifications compliance SOC ISO PCI",
        "accreditation audit reports HIPAA GDPR certified",
    ],
    "Liability": [
        "limitation of liability liability cap damages",
        "indemnity capped at uncapped liability limit",
    ],
    "Renewal": [
        "contract renewal terms auto-renewal automatic extension",
        "non-renewal notice period successive term",
    ],
    "Termination / Exit": [
        "termination for convenience exit rights notice period",
        "early termination fee termination clause breach",
    ],
    "Support": [
        "24/7 technical support hours availability",
        "critical incident response time severity SLA",
    ],
}


class ExtractionService:
    """Service handling structured evidence extraction and citation validation."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        groq_service: Optional[GroqService] = None,
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.groq_service = groq_service or GroqService()
        self.vector_store = get_vector_store()

    def extract_vendor_fact_sheets(
        self,
        session_id: str,
        requirements: ProcurementRequirements,
        vendor_name_filter: Optional[str] = None,
    ) -> ExtractionResponse:
        """Extract structured evidence fact sheets for all vendors in session.

        Args:
            session_id: Active session identifier string.
            requirements: ProcurementRequirements object.
            vendor_name_filter: Optional specific vendor name filter.

        Returns:
            Structured ExtractionResponse model.

        Raises:
            SessionNotFoundError: If session_id is not indexed in vector store.
        """
        if not self.vector_store.has_session(session_id):
            raise SessionNotFoundError(f"Session '{session_id}' not found or index not built.")

        session_data = self.vector_store._sessions[session_id]
        all_chunks = session_data.chunks

        # Collect unique vendor names in session
        session_vendors = sorted(list(set(c.vendor_name for c in all_chunks)))

        if vendor_name_filter and vendor_name_filter.strip():
            clean_filter = vendor_name_filter.strip().lower()
            session_vendors = [v for v in session_vendors if v.lower() == clean_filter]

        vendor_fact_sheets: List[VendorFactSheet] = []

        for vname in session_vendors:
            v_start = time.time()
            logger.info("extraction.vendor_start: Beginning fact extraction for vendor '%s'", vname)

            categories = list(BASELINE_CATEGORY_QUERIES.keys())
            custom_map = {}
            for idx, custom_req in enumerate(requirements.custom_requirements):
                clean_custom = custom_req.strip()
                if clean_custom:
                    cname = f"Custom: {clean_custom}"
                    categories.append(cname)
                    custom_map[cname] = f"Search query: {clean_custom}"

            req_contexts = {}
            for cat in categories:
                if cat in custom_map:
                    req_contexts[cat] = custom_map[cat]
                else:
                    req_contexts[cat] = self._get_requirement_context(cat, requirements) or ""

            # Perform targeted FAISS evidence retrieval per category for this vendor
            evidence_pack = []
            evidence_map: Dict[str, Any] = {}
            cat_evidence_map: Dict[str, List[Dict[str, Any]]] = {}
            seen_chunk_ids: Set[str] = set()
            cat_first_eid_map: Dict[str, str] = {}
            eid_counter = 1

            for cat_name in categories:
                cat_evidence_map[cat_name] = []
                cat_queries = custom_map.get(cat_name) or BASELINE_CATEGORY_QUERIES.get(cat_name) or [cat_name]
                if isinstance(cat_queries, str):
                    cat_queries = [cat_queries]

                for cat_query in cat_queries:
                    cat_retrieval = self.retrieval_service.search_evidence(
                        session_id=session_id,
                        query=cat_query,
                        vendor_name=vname,
                        top_k=3,
                    )
                    for res_item in cat_retrieval.results:
                        eid = None
                        if res_item.chunk_id in seen_chunk_ids:
                            # Find existing eid for this chunk
                            for existing_eid, item in evidence_map.items():
                                if item.chunk_id == res_item.chunk_id:
                                    eid = existing_eid
                                    break
                        else:
                            seen_chunk_ids.add(res_item.chunk_id)
                            eid = f"E{eid_counter}"
                            eid_counter += 1

                            evidence_pack.append({
                                "evidence_id": eid,
                                "chunk_id": res_item.chunk_id,
                                "text": res_item.text,
                            })
                            evidence_map[eid] = res_item

                        if eid and not any(c.get("chunk_id") == res_item.chunk_id for c in cat_evidence_map[cat_name]):
                            cat_evidence_map[cat_name].append({
                                "evidence_id": eid,
                                "chunk_id": res_item.chunk_id,
                                "text": res_item.text,
                            })
                            if cat_name not in cat_first_eid_map:
                                cat_first_eid_map[cat_name] = eid

            # Single Groq call per vendor for all categories with deterministic fallback
            try:
                batch_out = self.groq_service.extract_vendor_fact_sheet_batch(
                    vendor_name=vname,
                    categories=categories,
                    evidence_pack=evidence_pack,
                    requirement_contexts=req_contexts,
                )
            except (GroqNotConfiguredError, GroqTimeoutError, GroqRateLimitError) as err:
                logger.warning(
                    "Groq extraction limited for vendor '%s' (%s), using deterministic evidence extraction fallback.",
                    vname,
                    str(err),
                )
                batch_out = self._extract_deterministic_fallback(
                    categories=categories,
                    cat_evidence_map=cat_evidence_map,
                    evidence_map=evidence_map,
                    cat_first_eid_map=cat_first_eid_map,
                    requirements=requirements,
                )

            cat_results: List[CategoryExtractionResult] = []
            for cat_name in categories:
                groq_cat = batch_out.get(cat_name) or {
                    "status": "NOT_FOUND",
                    "raw_value": None,
                    "summary": "Not found in retrieved proposal evidence.",
                    "cited_evidence_ids": [],
                    "notes": None,
                }

                raw_status = groq_cat.get("status", "NOT_FOUND")
                extracted_raw = groq_cat.get("raw_value")
                valid_citations: List[EvidenceCitationModel] = []

                if raw_status in {"FOUND", "UNCLEAR", "CONFLICTING"}:
                    for cited_eid in groq_cat.get("cited_evidence_ids", []):
                        if cited_eid in evidence_map:
                            item = evidence_map[cited_eid]
                            valid_citations.append(
                                EvidenceCitationModel(
                                    evidence_id=cited_eid,
                                    vendor_name=item.vendor_name,
                                    source_filename=item.source_filename,
                                    start_page=item.start_page,
                                    end_page=item.end_page,
                                    chunk_id=item.chunk_id,
                                    excerpt_text=item.text,
                                )
                            )

                    # Citation fallback: If fact was found but cited ID omitted/mismatched, find exact chunk containing extracted value
                    if not valid_citations and raw_status == "FOUND":
                        fallback_eid = None
                        nums = re.findall(r"\d+\.\d+|\d+", extracted_raw or "")
                        if nums and evidence_map:
                            for eid, item in evidence_map.items():
                                if any(num in item.text for num in nums):
                                    fallback_eid = eid
                                    break
                        if not fallback_eid:
                            fallback_eid = cat_first_eid_map.get(cat_name) or (list(evidence_map.keys())[0] if evidence_map else None)

                        if fallback_eid and fallback_eid in evidence_map:
                            item = evidence_map[fallback_eid]
                            valid_citations.append(
                                EvidenceCitationModel(
                                    evidence_id=fallback_eid,
                                    vendor_name=item.vendor_name,
                                    source_filename=item.source_filename,
                                    start_page=item.start_page,
                                    end_page=item.end_page,
                                    chunk_id=item.chunk_id,
                                    excerpt_text=item.text,
                                )
                            )
                        else:
                            if not evidence_map:
                                raw_status = "NOT_FOUND"

                    # Grounding check: Verify extracted raw_value is grounded in cited evidence or re-link to matching chunk
                    if raw_status == "FOUND" and extracted_raw and valid_citations:
                        nums = re.findall(r"\d+\.\d+|\d+", extracted_raw)
                        if nums:
                            citation_blob = " ".join(c.excerpt_text for c in valid_citations).lower()
                            if not any(num in citation_blob for num in nums):
                                # Re-link to chunk in evidence_map that actually contains the numbers
                                grounded_eid = None
                                for eid, item in evidence_map.items():
                                    if any(num in item.text for num in nums):
                                        grounded_eid = eid
                                        break
                                if grounded_eid and grounded_eid in evidence_map:
                                    item = evidence_map[grounded_eid]
                                    valid_citations = [
                                        EvidenceCitationModel(
                                            evidence_id=grounded_eid,
                                            vendor_name=item.vendor_name,
                                            source_filename=item.source_filename,
                                            start_page=item.start_page,
                                            end_page=item.end_page,
                                            chunk_id=item.chunk_id,
                                            excerpt_text=item.text,
                                        )
                                    ]
                                else:
                                    logger.warning("extraction.ungrounded_value_rejected: '%s' not found in cited evidence for '%s'", extracted_raw, cat_name)
                                    raw_status = "UNCLEAR"
                                    extracted_raw = None

                cat_results.append(
                    CategoryExtractionResult(
                        category=cat_name,
                        status=raw_status,
                        raw_value=extracted_raw if raw_status == "FOUND" else None,
                        summary=groq_cat.get("summary") or "Evidence processed.",
                        evidence_citations=valid_citations,
                        notes=groq_cat.get("notes"),
                    )
                )

            v_elapsed = time.time() - v_start
            logger.info("extraction.vendor_complete: Extracted facts for vendor '%s' in %.2fs", vname, v_elapsed)

            vendor_fact_sheets.append(
                VendorFactSheet(
                    vendor_name=vname,
                    categories=cat_results,
                )
            )


        return ExtractionResponse(
            status="success",
            session_id=session_id,
            privacy_notice=Config.PRIVACY_NOTICE,
            vendor_fact_sheets=vendor_fact_sheets,
            total_vendors=len(vendor_fact_sheets),
        )

    def _extract_single_category(
        self,
        session_id: str,
        vendor_name: str,
        category_name: str,
        query_text: str,
        requirement_context: Optional[str],
    ) -> CategoryExtractionResult:
        """Extract structured evidence for a single category for a vendor."""
        # 1. Perform vendor-specific FAISS evidence retrieval (top 4 chunks)
        retrieval_resp = self.retrieval_service.search_evidence(
            session_id=session_id,
            query=query_text,
            vendor_name=vendor_name,
            top_k=4,
        )

        # 2. Construct Evidence Pack & Metadata Map
        evidence_pack = []
        evidence_map: Dict[str, RetrievalService] = {}
        seen_chunk_ids: Set[str] = set()

        eid_counter = 1
        for res_item in retrieval_resp.results:
            if res_item.chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(res_item.chunk_id)

            eid = f"E{eid_counter}"
            eid_counter += 1

            evidence_pack.append({
                "evidence_id": eid,
                "chunk_id": res_item.chunk_id,
                "text": res_item.text,
            })
            evidence_map[eid] = res_item

        # 3. Call Groq service for structured extraction
        groq_out = self.groq_service.extract_category_evidence(
            vendor_name=vendor_name,
            category=category_name,
            evidence_pack=evidence_pack,
            requirement_context=requirement_context,
        )

        # 4. Strict Backend Citation & Claim Support Validation
        raw_status = groq_out["status"]
        valid_citations: List[EvidenceCitationModel] = []

        if raw_status in {"FOUND", "UNCLEAR", "CONFLICTING"}:
            for cited_eid in groq_out.get("cited_evidence_ids", []):
                if cited_eid in evidence_map:
                    item = evidence_map[cited_eid]
                    valid_citations.append(
                        EvidenceCitationModel(
                            evidence_id=cited_eid,
                            vendor_name=item.vendor_name,
                            source_filename=item.source_filename,
                            start_page=item.start_page,
                            end_page=item.end_page,
                            chunk_id=item.chunk_id,
                            excerpt_text=item.text,
                        )
                    )

            # If model claimed FOUND or CONFLICTING but backend rejected all citation IDs, fallback to NOT_FOUND safely
            if not valid_citations and raw_status == "FOUND":
                raw_status = "NOT_FOUND"

        extracted_raw = groq_out.get("raw_value")
        # Grounding check: Verify extracted raw_value is grounded in the cited evidence
        if raw_status == "FOUND" and extracted_raw and valid_citations:
            nums = re.findall(r"\d+(?:\.\d+)?", extracted_raw)
            citation_blob = " ".join(c.excerpt_text for c in valid_citations).lower()
            if nums and not any(num in citation_blob for num in nums):
                logger.warning("extraction.single_ungrounded_value_rejected: '%s' not found in cited evidence for '%s'", extracted_raw, category_name)
                raw_status = "UNCLEAR"
                extracted_raw = None

        return CategoryExtractionResult(
            category=category_name,
            status=raw_status,
            raw_value=extracted_raw if raw_status == "FOUND" else None,
            summary=groq_out.get("summary") or "No details extracted.",
            evidence_citations=valid_citations,
            notes=groq_out.get("notes"),
        )

    def _get_requirement_context(self, cat_name: str, reqs: ProcurementRequirements) -> Optional[str]:
        """Format user requirement context string for a category if defined."""
        if cat_name == "Pricing" and reqs.budget_ceiling is not None:
            return f"User budget ceiling: {reqs.budget_currency} {reqs.budget_ceiling:,.2f}"
        if cat_name == "Payment Terms" and reqs.payment_terms:
            return f"User payment requirement: {reqs.payment_terms}"
        if cat_name == "Delivery / Implementation" and reqs.timeline_value is not None:
            return f"User maximum timeline: {reqs.timeline_value} {reqs.timeline_unit}"
        if cat_name == "SLA / Uptime" and reqs.minimum_sla is not None:
            return f"User minimum SLA: {reqs.minimum_sla}% uptime"
        if cat_name == "Warranty" and reqs.warranty_value is not None:
            return f"User minimum warranty: {reqs.warranty_value} {reqs.warranty_unit}"
        if cat_name == "Certifications" and reqs.certifications:
            return f"User required certifications: {', '.join(reqs.certifications)}"
        if cat_name == "Liability" and reqs.liability_requirement:
            return f"User liability requirement: {reqs.liability_requirement}"
        if cat_name == "Renewal" and reqs.renewal_preference:
            return f"User renewal preference: {reqs.renewal_preference}"
        if cat_name == "Termination / Exit" and reqs.termination_requirement:
            return f"User termination requirement: {reqs.termination_requirement}"
        if cat_name == "Support" and reqs.support_requirement:
            return f"User support requirement: {reqs.support_requirement}"
        return None

    def _extract_deterministic_fallback(
        self,
        categories: List[str],
        cat_evidence_map: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        evidence_map: Optional[Dict[str, Any]] = None,
        cat_first_eid_map: Optional[Dict[str, str]] = None,
        requirements: Optional[ProcurementRequirements] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Extract generic procurement facts using deterministic category-scoped pattern matching."""
        import re
        result = {}
        cat_evidence_map = cat_evidence_map or {}
        evidence_map = evidence_map or {}
        cat_first_eid_map = cat_first_eid_map or {}

        for cat in categories:
            matched_val = None
            cat_pack = cat_evidence_map.get(cat, [])
            raw_cat_text = " ".join(item["text"] for item in cat_pack) if cat_pack else ""
            
            # Fallback to general evidence if cat_text is empty
            if not raw_cat_text and evidence_map:
                raw_cat_text = " ".join(item.text for item in evidence_map.values() if hasattr(item, 'text'))

            # Apply generic word-number parser (e.g., "four weeks" -> "4 weeks")
            cat_text = replace_word_numbers_in_text(raw_cat_text)

            matched_eid = None
            if cat_pack:
                matched_eid = cat_pack[0]["evidence_id"]
            elif cat_first_eid_map.get(cat):
                matched_eid = cat_first_eid_map[cat]
            elif evidence_map:
                matched_eid = list(evidence_map.keys())[0]

            summary = "Extracted via deterministic evidence parsing."

            if cat == "Pricing":
                matches = list(re.finditer(r'(\$\s?[\d,]+(?:\.\d+)?(?:\s?(?:USD|per year|annually|per annum|/yr|/year))?|[\d,]+(?:\.\d+)?\s?USD|USD\s?[\d,]+(?:\.\d+)?)', cat_text, re.IGNORECASE))
                for m in matches:
                    val = m.group(1).strip()
                    start = max(0, m.start() - 60)
                    end = min(len(cat_text), m.end() + 60)
                    window = cat_text[start:end].lower()
                    if any(bad in window for bad in ["liability", "indemnification", "indemnity", "insurance", "damages", "cap on"]):
                        continue
                    matched_val = val
                    break
            elif cat == "Payment Terms":
                m = re.search(r'(Net\s?\d+|\d+%\s?upfront|due\s?in\s?\d+\s?days|payable\s?within\s?\d+\s?days|payable\s?upon\s?receipt|due\s?upon\s?invoice|invoice\s?payable\s?\d+\s?days)', cat_text, re.IGNORECASE)
                if m:
                    matched_val = m.group(1).strip()
            elif cat == "Delivery / Implementation":
                matches = list(re.finditer(r'(\d+\s?(?:days|weeks|months))\s*(?:of|from|after|implementation|deployment|onboarding|delivery|go-live|rollout)?', cat_text, re.IGNORECASE))
                for m in matches:
                    val = m.group(1).strip()
                    start = max(0, m.start() - 60)
                    end = min(len(cat_text), m.end() + 60)
                    window = cat_text[start:end].lower()
                    if any(bad in window for bad in ["contract term", "contract duration", "agreement period", "warranty", "notice period", "renewal"]):
                        continue
                    if any(good in window for good in ["implementation", "deployment", "onboarding", "delivery", "go-live", "rollout", "timeline", "schedule", "setup", "turnaround"]):
                        matched_val = val
                        break
            elif cat == "SLA / Uptime":
                matches = list(re.finditer(r'(\d+(?:\.\d+)?%\s*(?:uptime|availability|SLA)?)', cat_text, re.IGNORECASE))
                for m in matches:
                    val = m.group(1).strip()
                    if "%" not in val:
                        continue
                    start = max(0, m.start() - 60)
                    end = min(len(cat_text), m.end() + 60)
                    window = cat_text[start:end].lower()
                    if any(bad in window for bad in ["escalation", "increase", "discount", "tax", "fee", "interest"]):
                        continue
                    if any(good in window for good in ["uptime", "availability", "sla", "service level", "99."]):
                        matched_val = val
                        break
            elif cat == "Certifications":
                certs = []
                for cert in ["SOC 2", "ISO 27001", "PCI-DSS", "HIPAA", "ISO 9001", "GDPR"]:
                    if cert.lower() in cat_text.lower():
                        certs.append(cert)
                if certs:
                    matched_val = ", ".join(certs)
            elif cat == "Warranty":
                m = re.search(r'(\d+\s*(?:months?|years?))\s*(?:warranty|guarantee|defects?\s*covered)?', cat_text, re.IGNORECASE)
                if m:
                    matched_val = m.group(1).strip()
            elif cat == "Support":
                m = re.search(r'(24/7|24x7|business\s?hours|\d+\s*(?:hours?|minutes?)\s*(?:response|critical\s*response)|severity\s*1\s*response\s*within\s*\d+\s*(?:hours?|minutes?)|\d+\/\d+)', cat_text, re.IGNORECASE)
                if m:
                    matched_val = m.group(1).strip()
            elif cat == "Liability":
                m = re.search(r'(\d+x\s*annual|cap(?:ped)?\s*at|limited\s*to\s*[\$\d,]+|uncapped|no\s*limit)', cat_text, re.IGNORECASE)
                if m:
                    matched_val = m.group(1).strip()
            elif cat == "Renewal":
                m = re.search(r'(auto(?:matic)?\s*renewal|manual\s*renewal|\d+-day\s*notice\s*for\s*renewal|renews\s*for\s*\d+\s*months?|auto-renews|successive\s*(?:\d+-month|\d+-year|one-year|annual)\s*terms?|automatic\s*extension)', cat_text, re.IGNORECASE)
                if m:
                    matched_val = m.group(1).strip()
            elif cat == "Termination / Exit":
                m = re.search(r'(termination\s*for\s*convenience|\d+-day\s*notice|material\s*breach|early\s*termination\s*fee)', cat_text, re.IGNORECASE)
                if m:
                    matched_val = m.group(1).strip()
            elif cat.startswith("Custom:"):
                custom_req_text = cat.replace("Custom:", "").strip()
                words = [w.lower() for w in re.split(r'\W+', custom_req_text) if len(w) > 3]
                # Search cat_text for proposal sentences matching custom topic words
                if words and cat_text:
                    sentences = [s.strip() for s in re.split(r'[.\n]', cat_text) if s.strip()]
                    matched_sentence = None
                    for s in sentences:
                        s_lower = s.lower()
                        if sum(1 for w in words if w in s_lower) >= max(1, min(2, len(words))):
                            matched_sentence = s
                            break
                    if matched_sentence:
                        matched_val = matched_sentence

            if matched_val:
                result[cat] = {
                    "status": "FOUND",
                    "raw_value": matched_val,
                    "summary": summary,
                    "cited_evidence_ids": [matched_eid] if matched_eid else [],
                    "notes": None,
                }
            else:
                result[cat] = {
                    "status": "NOT_FOUND",
                    "raw_value": None,
                    "summary": "Not found in proposal evidence.",
                    "cited_evidence_ids": [],
                    "notes": None,
                }

        return result
