"""Hybrid Contradiction Analysis Service for PropIQ.

Identifies materially inconsistent statements within the same vendor proposal PDF using:
1. Canonical Topic Clustering across 14 procurement areas
2. Strict Same-Vendor Isolation Enforcement (candidate_a.vendor_name == candidate_b.vendor_name)
3. Local Sequence-Pair Hugging Face NLI Model (CONTRADICTION, NEUTRAL, ENTAILMENT)
4. Heuristic & Domain False-Positive Suppression (Plan tiers, initial vs renewal terms)
5. Optional Generative Explanation with Offline Template Fallback
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from app.config import Config
from app.models import (
    RiskSeverity,
    ContradictionStatus,
    ContradictionFindingModel,
    EvidenceCitationModel,
    VendorFactSheet,
)
from app.services.vector_store import get_vector_store
from app.services.retrieval_service import RetrievalService
from app.services.nli_service import get_nli_service
from app.services.groq_service import GroqService

logger = logging.getLogger("propiq_backend")

# 14 Canonical Procurement Topics for Contradiction Clustering
CONTRADICTION_TOPICS: Dict[str, str] = {
    "Commitment & Term": "commitment cancellation term auto renewal long-term cancel anytime minimum term initial term",
    "Pricing & Fees": "fees pricing setup fee implementation fee fixed pricing additional charges price adjustment escalation",
    "SLA & Uptime": "support 24/7 business hours uptime SLA response time guaranteed target standard premium downtime",
    "Support Availability": "support hours 8x5 24/7 helpdesk incident resolution escalation channel email phone",
    "Deployment Timeline": "deployment implementation timeline schedule launch go-live days weeks schedule target",
    "Renewal Terms": "renewal term annual extension price increase notice window non-renewal cancellation",
    "Warranty Coverage": "warranty coverage guarantee defect period 30 days 90 days 12 months as-is",
    "Certifications": "SOC 2 Type II ISO 27001 compliance certified audit report security assessment",
    "Liability & Cap": "liability cap uncapped limitation of liability aggregate damages carve-out indemnification",
    "Payment Terms": "payment terms Net 30 Net 45 upfront deposit milestone billing schedule invoice",
    "Data Ownership": "customer data ownership analytics rights derived data vendor ownership intellectual property",
    "Data Usage": "machine learning AI model training aggregate data processing usage rights privacy",
    "Security Commitments": "encryption at rest in transit SOC 2 security controls access management MFA",
    "Termination Rights": "termination for convenience cause notice period cancellation penalty buyout fee",
}


class ContradictionService:
    """Service handling evidence-grounded intra-vendor contradiction intelligence."""

    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.nli_service = get_nli_service()
        self.groq_service = GroqService()

    def analyze_session_contradictions(
        self,
        session_id: str,
        fact_sheets: Optional[List[VendorFactSheet]] = None,
        vendor_name_filter: Optional[str] = None,
    ) -> List[ContradictionFindingModel]:
        """Detect intra-vendor contradictions across session proposals."""
        vector_store = get_vector_store()
        all_vendor_names = vector_store.get_session_vendors(session_id)

        if not all_vendor_names and fact_sheets:
            all_vendor_names = list(dict.fromkeys([s.vendor_name for s in fact_sheets if s.vendor_name]))

        if not all_vendor_names:
            return []

        target_vendors = (
            [v for v in all_vendor_names if v.lower() == vendor_name_filter.lower()]
            if vendor_name_filter
            else all_vendor_names
        )

        all_findings: List[ContradictionFindingModel] = []

        # 1. Reuse Phase 3 CONFLICTING extracted fact sheets directly
        if fact_sheets:
            conf_fact_findings = self._extract_phase3_conflicting_facts(session_id, fact_sheets)
            all_findings.extend(conf_fact_findings)

        # 2. Perform Same-Vendor Pairwise NLI Inference for each vendor
        for vname in target_vendors:
            try:
                sem_findings = self._analyze_vendor_nli_contradictions(session_id, vname)
                all_findings.extend(sem_findings)
            except Exception as err:
                logger.error("Contradiction analysis failure for vendor '%s': %s", vname, str(err))

        # 3. Apply False-Positive Suppression & Deduplication
        validated = self._validate_and_filter_contradictions(all_findings)
        return validated

    def _extract_phase3_conflicting_facts(
        self,
        session_id: str,
        fact_sheets: List[VendorFactSheet],
    ) -> List[ContradictionFindingModel]:
        """Convert Phase 3 CONFLICTING extraction results into contradiction findings."""
        findings: List[ContradictionFindingModel] = []

        for sheet in fact_sheets:
            vname = sheet.vendor_name
            for cat in sheet.categories:
                if cat.status == "CONFLICTING":
                    citations = cat.evidence_citations
                    if len(citations) >= 2:
                        c1 = [citations[0]]
                        c2 = [citations[1]]
                    elif len(citations) == 1:
                        c1 = [citations[0]]
                        c2 = [citations[0]]
                    else:
                        continue

                    # STRICT SAME-VENDOR ISOLATION GUARD
                    if c1[0].vendor_name.lower() != c2[0].vendor_name.lower():
                        continue

                    ctr_id = f"ctr_{re.sub(r'[^a-zA-Z0-9]', '', vname).lower()}_{re.sub(r'[^a-zA-Z0-9]', '', cat.category).lower()}"

                    findings.append(
                        ContradictionFindingModel(
                            contradiction_id=ctr_id,
                            vendor_name=vname,
                            category=cat.category,
                            severity=RiskSeverity.HIGH if cat.category in {"Pricing", "Payment Terms", "SLA / Uptime"} else RiskSeverity.MEDIUM,
                            statement_a=cat.summary,
                            statement_b=cat.notes or cat.raw_value or "Conflicting statement extracted from proposal.",
                            context_a=f"Page {citations[0].start_page}" if citations else None,
                            context_b=f"Page {citations[-1].start_page}" if citations else None,
                            evidence_a=c1,
                            evidence_b=c2,
                            reason=f"Proposal contains conflicting statements regarding {cat.category}.",
                            status=ContradictionStatus.CONFIRMED_CONTRADICTION,
                        )
                    )

        return findings

    def _analyze_vendor_nli_contradictions(
        self,
        session_id: str,
        vendor_name: str,
    ) -> List[ContradictionFindingModel]:
        """Perform pairwise statement pairing and local NLI inference within THIS vendor ONLY."""
        findings: List[ContradictionFindingModel] = []

        for topic_name, query_str in CONTRADICTION_TOPICS.items():
            results = self.retrieval_service.search_evidence(
                session_id=session_id,
                query=query_str,
                vendor_name=vendor_name,
                top_k=4,
            )

            if len(results) < 2:
                continue

            # Compare distinct candidate pairs within THIS vendor ONLY
            for i in range(len(results)):
                for j in range(i + 1, len(results)):
                    r1 = results[i]
                    r2 = results[j]

                    # 1. STRICT SAME-VENDOR ISOLATION GUARD (Rule 13)
                    if r1.vendor_name.lower() != r2.vendor_name.lower():
                        continue

                    # Skip identical chunks
                    if r1.chunk_id == r2.chunk_id:
                        continue

                    # 2. Local Pairwise NLI Inference (Rule 1)
                    nli_scores, top_label = self.nli_service.predict_pair(r1.text, r2.text)
                    contra_prob = nli_scores.get("CONTRADICTION", 0.0)

                    # Contradiction threshold: contra_prob >= 0.55 or top_label == 'CONTRADICTION'
                    if top_label == "CONTRADICTION" or contra_prob >= 0.55:
                        c1 = EvidenceCitationModel(
                            evidence_id="E1",
                            vendor_name=r1.vendor_name,
                            source_filename=r1.source_filename,
                            start_page=r1.start_page,
                            end_page=r1.end_page,
                            chunk_id=r1.chunk_id,
                            excerpt_text=r1.text,
                        )
                        c2 = EvidenceCitationModel(
                            evidence_id="E2",
                            vendor_name=r2.vendor_name,
                            source_filename=r2.source_filename,
                            start_page=r2.start_page,
                            end_page=r2.end_page,
                            chunk_id=r2.chunk_id,
                            excerpt_text=r2.text,
                        )

                        ctr_id = f"ctr_{re.sub(r'[^a-zA-Z0-9]', '', vendor_name).lower()}_{len(findings)+1}"

                        explanation = f"Local NLI model identified contradiction probability of {round(contra_prob * 100, 1)}% on topic '{topic_name}' between Page {r1.start_page} and Page {r2.start_page}."

                        findings.append(
                            ContradictionFindingModel(
                                contradiction_id=ctr_id,
                                vendor_name=vendor_name,
                                category=topic_name,
                                severity=RiskSeverity.HIGH if "Pricing" in topic_name or "Term" in topic_name else RiskSeverity.MEDIUM,
                                statement_a=r1.text[:200],
                                statement_b=r2.text[:200],
                                context_a=f"Page {r1.start_page}",
                                context_b=f"Page {r2.start_page}",
                                evidence_a=[c1],
                                evidence_b=[c2],
                                reason=explanation,
                                status=ContradictionStatus.POTENTIAL_CONTRADICTION,
                            )
                        )

        return findings

    def _validate_and_filter_contradictions(
        self,
        findings: List[ContradictionFindingModel],
    ) -> List[ContradictionFindingModel]:
        """Apply domain false-positive suppression rules to candidate findings."""
        valid_findings: List[ContradictionFindingModel] = []
        seen_keys: Set[Tuple[str, str, str]] = set()

        for f in findings:
            # 1. Dual citation validation
            if not f.evidence_a or not f.evidence_b:
                continue

            # 2. Strict same-vendor check
            v1 = f.evidence_a[0].vendor_name.lower()
            v2 = f.evidence_b[0].vendor_name.lower()
            if v1 != v2:
                continue

            text_a = (f.statement_a + " " + f.evidence_a[0].excerpt_text).lower()
            text_b = (f.statement_b + " " + f.evidence_b[0].excerpt_text).lower()
            combined = text_a + " " + text_b

            # False-Positive Rule 1: Plan Tier distinctions (Standard vs Premium)
            if ("standard" in text_a and "premium" in text_b) or ("standard" in text_b and "premium" in text_a):
                continue
            if ("basic" in text_a and "enterprise" in text_b) or ("basic" in text_b and "enterprise" in text_a):
                continue

            # False-Positive Rule 2: Initial term vs Renewal term
            if ("initial term" in text_a and "renewal term" in text_b) or ("initial term" in text_b and "renewal term" in text_a):
                continue

            # False-Positive Rule 3: Fixed current pricing vs CPI renewal escalation
            if ("initial term" in combined or "fixed" in combined) and ("renewal" in combined or "cpi" in combined):
                if "sole discretion" not in combined:
                    continue

            # False-Positive Rule 4: Distinct certifications (ISO 27001 vs SOC 2)
            if ("iso 27001" in text_a and "soc 2" in text_b) or ("iso 27001" in text_b and "soc 2" in text_a):
                continue

            # False-Positive Rule 5: Distinct terms e.g. cancellation notice vs invoice payment terms
            if ("notice" in text_a and "invoice" in text_b) or ("notice" in text_b and "invoice" in text_a):
                continue

            # False-Positive Rule 6: Distinct support aspects e.g. helpdesk channel vs response SLA
            if ("channel" in text_a and "sla" in text_b) or ("channel" in text_b and "sla" in text_a):
                continue

            # Deduplication
            dedup_key = (f.vendor_name.lower(), f.statement_a[:40].lower(), f.statement_b[:40].lower())
            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                valid_findings.append(f)

        return valid_findings
