"""Hybrid Risk Intelligence Service for PropIQ.

Combines:
1. Deterministic Rule Engine (Linguistic pattern matching against RiskKnowledgeBase)
2. Local Semantic Vector Similarity (SentenceTransformer cosine similarity against category definitions)
3. Transparent Signal-Based Confidence Aggregator (HIGH, MEDIUM, LOW)
4. Offline Resilience (High confidence rule matches bypass Groq LLM entirely)
5. Decoupled Severity Policy (Evaluates risk importance from extracted clause terms)
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from app.config import Config
from app.models import (
    RiskSeverity,
    RiskStatus,
    RiskFindingModel,
    EvidenceCitationModel,
    ProcurementRequirements,
    VendorFactSheet,
)
from app.services.risk_knowledge_base import (
    RiskCategory,
    TAXONOMY_KNOWLEDGE_BASE,
    RiskDefinition,
)
from app.services.embedding_service import get_embedding_service
from app.services.vector_store import get_vector_store
from app.services.retrieval_service import RetrievalService
from app.services.groq_service import GroqService

logger = logging.getLogger("propiq_backend")

# Calibrated semantic similarity thresholds evaluated against risk clause test corpus
DEFAULT_SEMANTIC_HIGH_THRESHOLD = 0.42
DEFAULT_SEMANTIC_MEDIUM_THRESHOLD = 0.32


class RiskService:
    """Service handling evidence-grounded hybrid contract risk intelligence."""

    def __init__(
        self,
        high_threshold: float = DEFAULT_SEMANTIC_HIGH_THRESHOLD,
        medium_threshold: float = DEFAULT_SEMANTIC_MEDIUM_THRESHOLD,
    ):
        self.retrieval_service = RetrievalService()
        self.groq_service = GroqService()
        self.embedder = get_embedding_service()

        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold

        # Precompute category embeddings for semantic vector matching
        self.category_embeddings: Dict[RiskCategory, List[float]] = {}
        self._precompute_category_embeddings()

    def _precompute_category_embeddings(self) -> None:
        """Embed semantic vector texts for all 22 risk taxonomy categories."""
        for cat_enum, risk_def in TAXONOMY_KNOWLEDGE_BASE.items():
            try:
                emb = self.embedder.embed_text(risk_def.semantic_vector_text)
                self.category_embeddings[cat_enum] = emb
            except Exception as err:
                logger.warning("Failed to embed category %s: %s", cat_enum, str(err))

    def analyze_session_risks(
        self,
        session_id: str,
        requirements: Optional[ProcurementRequirements] = None,
        fact_sheets: Optional[List[VendorFactSheet]] = None,
        vendor_name_filter: Optional[str] = None,
    ) -> List[RiskFindingModel]:
        """Analyze contract risks for all vendors in a session using hybrid rule + vector + LLM pipeline."""
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

        all_findings: List[RiskFindingModel] = []

        # 1. Deterministic Rule & Fact Sheet Risk Detection
        if fact_sheets:
            det_findings = self._generate_deterministic_risks(session_id, fact_sheets, requirements)
            all_findings.extend(det_findings)

        # 2. Local Semantic Vector + Heuristic Detection per Vendor
        for vname in target_vendors:
            try:
                sem_findings = self._analyze_vendor_hybrid_risks(session_id, vname, requirements)
                all_findings.extend(sem_findings)
            except Exception as err:
                logger.error("Partial risk analysis failure for vendor '%s': %s", vname, str(err))

        # 3. Suppression, Severity Calibration, Evidence Binding, and Deduplication
        validated_findings = self._validate_and_deduplicate_findings(session_id, all_findings, requirements)
        return validated_findings

    def _generate_deterministic_risks(
        self,
        session_id: str,
        fact_sheets: List[VendorFactSheet],
        requirements: Optional[ProcurementRequirements],
    ) -> List[RiskFindingModel]:
        """Generate high-confidence deterministic risk findings directly from structured facts."""
        findings: List[RiskFindingModel] = []

        for sheet in fact_sheets:
            vname = sheet.vendor_name
            for cat in sheet.categories:
                # Rule: Missing information (NOT_FOUND) is strictly ignored for risk findings
                if cat.status == "NOT_FOUND" or not cat.evidence_citations:
                    continue

                raw_text = (cat.raw_value or "").lower()
                summary_text = (cat.summary or "").lower()
                combined = f"{raw_text} {summary_text}"

                # Check auto renewal
                if "auto" in combined and "renew" in combined:
                    auto_def = TAXONOMY_KNOWLEDGE_BASE[RiskCategory.AUTO_RENEWAL]
                    if not any(re.search(pat, combined) for pat in auto_def.suppression_patterns):
                        n_days = 30
                        n_match = re.search(r"(\d+)\s*day", combined)
                        if n_match:
                            n_days = int(n_match.group(1))

                        sev = RiskSeverity.HIGH if n_days > 60 else RiskSeverity.MEDIUM
                        r_id = f"rsk_{re.sub(r'[^a-zA-Z0-9]', '', vname).lower()}_auto_renew"

                        rel_reqs = []
                        if requirements and requirements.renewal_preference:
                            rel_reqs.append("REQ_RENEWAL")

                        findings.append(
                            RiskFindingModel(
                                risk_id=r_id,
                                vendor_name=vname,
                                category=RiskCategory.AUTO_RENEWAL,
                                severity=sev,
                                title=f"Automatic Renewal With {n_days}-Day Notice Window",
                                summary=cat.summary or "Contract automatically renews unless cancelled in advance.",
                                procurement_impact=f"Creates potential vendor lock-in if cancellation notice is not provided at least {n_days} days prior to expiration.",
                                review_reason="Operationally track renewal notice deadline in procurement calendar.",
                                evidence_citations=cat.evidence_citations,
                                related_requirement_ids=rel_reqs,
                                status=RiskStatus.DETECTED,
                            )
                        )

                # Check uncapped liability
                if "unlimited liability" in combined or "uncapped liability" in combined or "no limitation of liability" in combined:
                    r_id = f"rsk_{re.sub(r'[^a-zA-Z0-9]', '', vname).lower()}_uncapped_liab"
                    findings.append(
                        RiskFindingModel(
                            risk_id=r_id,
                            vendor_name=vname,
                            category=RiskCategory.UNCAPPED_LIABILITY,
                            severity=RiskSeverity.CRITICAL,
                            title="Uncapped Financial Liability Provision",
                            summary="Vendor terms contain uncapped or unlimited financial liability exposure.",
                            procurement_impact="Exposes company to unlimited damages in the event of a breach or legal claim.",
                            review_reason="Requires legal review to cap total liability at a reasonable contract multiple.",
                            evidence_citations=cat.evidence_citations,
                            related_requirement_ids=["REQ_LIABILITY"] if requirements and requirements.liability_requirement else [],
                            status=RiskStatus.DETECTED,
                        )
                    )

        return findings

    def _analyze_vendor_hybrid_risks(
        self,
        session_id: str,
        vendor_name: str,
        requirements: Optional[ProcurementRequirements],
    ) -> List[RiskFindingModel]:
        """Execute hybrid local vector similarity + rule match + selective Groq review for single vendor."""
        # 1. Retrieve evidence chunks for vendor across risk categories
        risk_queries = [
            "contract renewal auto-renew cancellation notice period extension",
            "price increase fee escalation rate revision CPI adjustment",
            "limitation of liability liability cap aggregate liability uncapped indemnity",
            "early termination buyout fee non-refundable payment penalty",
            "support hours 24/7 business hours uptime SLA credit warranty",
            "data ownership AI machine learning training rights security audit",
        ]

        results = []
        seen_chunk_ids: Set[str] = set()
        for q in risk_queries:
            q_res = self.retrieval_service.search_evidence(
                session_id=session_id,
                query=q,
                vendor_name=vendor_name,
                top_k=3,
            )
            for r in q_res.results:
                if r.chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(r.chunk_id)
                    results.append(r)

        if not results:
            return []

        findings: List[RiskFindingModel] = []
        medium_confidence_pack: List[Dict[str, Any]] = []
        e_counter = 1

        for r in results:
            text = r.text
            text_lower = text.lower()
            chunk_emb = self.embedder.embed_text(text)

            for cat_enum, risk_def in TAXONOMY_KNOWLEDGE_BASE.items():
                if cat_enum == RiskCategory.OTHER_REVIEW_REQUIRED:
                    continue

                # Check suppression patterns
                if any(re.search(pat, text_lower) for pat in risk_def.suppression_patterns):
                    continue

                # Compute cosine similarity against category vector to locate candidate passages
                cat_emb = self.category_embeddings.get(cat_enum)
                sim = 0.0
                if cat_emb:
                    sim = self.embedder.cosine_similarity(chunk_emb, cat_emb)

                # Similarity or rule match determines candidacy for evaluation
                rule_matched = any(re.search(pat, text_lower) for pat in risk_def.rule_patterns)
                if not (rule_matched or sim >= self.medium_threshold):
                    continue

                # Verification Step: Use similarity strictly to locate candidate passages.
                # Verify whether the clause wording actually creates the affirmative risk.
                creates_risk = self._verify_risk_in_clause(cat_enum, text)

                citation = EvidenceCitationModel(
                    evidence_id=f"E{e_counter}",
                    vendor_name=r.vendor_name,
                    source_filename=r.source_filename,
                    start_page=r.start_page,
                    end_page=r.end_page,
                    chunk_id=r.chunk_id,
                    excerpt_text=r.text,
                )

                if creates_risk:
                    sev = self._evaluate_risk_severity(cat_enum, text_lower)
                    r_id = f"rsk_{re.sub(r'[^a-zA-Z0-9]', '', vendor_name).lower()}_{cat_enum.value.lower()}_{len(findings)+1}"

                    findings.append(
                        RiskFindingModel(
                            risk_id=r_id,
                            vendor_name=vendor_name,
                            category=cat_enum,
                            severity=sev,
                            title=risk_def.title,
                            summary=risk_def.description,
                            procurement_impact=risk_def.default_procurement_impact,
                            review_reason=risk_def.default_review_reason,
                            evidence_citations=[citation],
                            related_requirement_ids=[],
                            status=RiskStatus.DETECTED,
                        )
                    )
                    e_counter += 1

                elif sim >= self.medium_threshold and not any(re.search(pat, text_lower) for pat in risk_def.suppression_patterns):
                    # Candidate passage had topical similarity but affirmative risk was ambiguous:
                    # pack for selective Groq review if Groq is available
                    medium_confidence_pack.append({
                        "evidence_id": f"E{e_counter}",
                        "category": cat_enum.value,
                        "vendor_name": r.vendor_name,
                        "source_filename": r.source_filename,
                        "start_page": r.start_page,
                        "end_page": r.end_page,
                        "chunk_id": r.chunk_id,
                        "text": r.text,
                        "similarity": round(sim, 3),
                    })
                    e_counter += 1

        # 2. Ambiguous/Medium confidence items -> Selective Groq reasoning call (if configured)
        if medium_confidence_pack and Config.is_groq_configured():
            try:
                groq_findings = self._review_medium_confidence_risks(vendor_name, medium_confidence_pack)
                findings.extend(groq_findings)
            except Exception as err:
                logger.warning("Selective Groq risk review skipped/failed: %s", str(err))

        return findings

    def _verify_risk_in_clause(self, category: RiskCategory, text: str) -> bool:
        """Verify whether candidate text affirmatively creates the risk rather than merely sounding related."""
        text_lower = text.lower()
        risk_def = TAXONOMY_KNOWLEDGE_BASE.get(category)
        if not risk_def:
            return False

        # 1. Broad Negation & Safe Harbor Protection Verification
        if any(re.search(pat, text_lower) for pat in risk_def.suppression_patterns):
            return False

        # Generic safe-harbor and negation patterns
        general_negations = [
            r"\bwill\s+never\b",
            r"\bshall\s+never\b",
            r"\bunder\s+no\s+circumstances\b",
            r"\bis\s+strictly\s+prohibited\b",
            r"\bprohibited\s+from\b",
            r"\bwill\s+not\s+(?:be\s+used|use|apply|escalate|renew|modify)\b",
            r"\bshall\s+not\s+(?:be\s+used|use|apply|escalate|renew|modify)\b",
            r"\bdoes\s+not\s+(?:use|apply|escalate|renew|modify)\b",
            r"\bdo\s+not\s+(?:use|apply|escalate|renew|modify)\b",
            r"\bno\s+right\s+to\b",
            r"\bneither\s+party\s+shall\b",
            r"\bwithout\s+(?:the\s+)?customer(?:'s)?\s+(?:prior\s+)?(?:written\s+)?(?:consent|approval)\b",
            r"\bsolely\s+(?:to\s+provide|for\s+the\s+purpose\s+of\s+providing)\s+the\s+service\b",
        ]
        if any(re.search(pat, text_lower) for pat in general_negations):
            return False

        # 2. Affirmative Risk Language Verification
        has_affirmative_rule = any(re.search(pat, text_lower) for pat in risk_def.rule_patterns)
        if not has_affirmative_rule:
            return False

        # 3. Category-Specific Affirmative Grounding
        if category == RiskCategory.DATA_USAGE:
            affirmative_usage = any(
                re.search(pat, text_lower)
                for pat in [
                    r"(?:may|reserves?\s+the\s+right\s+to|rights?\s+to)\s+(?:use|train|utilize)",
                    r"(?:train|training)\s+(?:ai|machine\s+learning|models?)",
                    r"customer\s+grants\s+.*(?:right|license)\s+to",
                    r"aggregate\s+and\s+anonymize\s+data",
                    r"use\s+customer\s+data\s+for\s+product\s+improvement",
                ]
            )
            if not affirmative_usage:
                return False

        elif category == RiskCategory.AUTO_RENEWAL:
            affirmative_renewal = any(
                re.search(pat, text_lower)
                for pat in [
                    r"automatic(?:ally)?\s+renew",
                    r"auto-renew",
                    r"successive\s+(?:\d+-month|\d+-year|annual|monthly)\s+terms?",
                    r"renew\s+unless\s+(?:cancelled|terminated)",
                ]
            )
            if not affirmative_renewal:
                return False

        elif category == RiskCategory.PRICE_ESCALATION:
            affirmative_escalation = any(
                re.search(pat, text_lower)
                for pat in [
                    r"price\s+(?:increase|escalation|adjustment|uplift)",
                    r"fee\s+(?:increase|escalation|adjustment)",
                    r"increase\s+by\s+(?:up\s+to\s+)?\d+%",
                    r"subject\s+to\s+annual\s+increase",
                    r"cpi\s+(?:increase|adjustment)",
                    r"sole\s+discretion\s+pricing",
                ]
            )
            if not affirmative_escalation:
                return False

        elif category == RiskCategory.EARLY_TERMINATION_FEE:
            affirmative_fee = any(
                re.search(pat, text_lower)
                for pat in [
                    r"early\s+termination\s+(?:fee|penalty|charge)",
                    r"remaining\s+fees\s+(?:shall|will)\s+become\s+(?:due|payable)",
                    r"liquidated\s+damages\s+for\s+early\s+termination",
                    r"buyout\s+fee",
                ]
            )
            if not affirmative_fee:
                return False

        elif category == RiskCategory.UNCAPPED_LIABILITY:
            affirmative_uncapped = any(
                re.search(pat, text_lower)
                for pat in [
                    r"unlimited\s+liability",
                    r"uncapped\s+liability",
                    r"without\s+limitation\s+of\s+liability",
                    r"no\s+cap\s+on\s+liability",
                ]
            )
            if not affirmative_uncapped:
                return False

        return True

    def _evaluate_risk_severity(self, category: RiskCategory, clause_text: str) -> RiskSeverity:
        """Deterministically evaluate risk severity based on extracted terms and category policy."""
        if category == RiskCategory.UNCAPPED_LIABILITY:
            return RiskSeverity.CRITICAL

        if category == RiskCategory.AUTO_RENEWAL:
            if "90 day" in clause_text or "120 day" in clause_text or "24 month" in clause_text or "36 month" in clause_text:
                return RiskSeverity.HIGH
            return RiskSeverity.MEDIUM

        if category in {RiskCategory.EARLY_TERMINATION_FEE, RiskCategory.INDEMNITY, RiskCategory.UNILATERAL_CHANGE_RIGHTS, RiskCategory.DATA_USAGE}:
            return RiskSeverity.HIGH

        if category == RiskCategory.SUSPENSION_RIGHTS:
            if "non-payment" in clause_text or "overdue" in clause_text:
                return RiskSeverity.LOW
            return RiskSeverity.MEDIUM

        return RiskSeverity.MEDIUM

    def _review_medium_confidence_risks(
        self, vendor_name: str, candidate_pack: List[Dict[str, Any]]
    ) -> List[RiskFindingModel]:
        """Selective Groq review for ambiguous medium-confidence candidate risk items."""
        system_prompt = (
            "You are a procurement contract risk verification engine for PropIQ.\n"
            "Review candidate excerpts for potential contract risks. Reject unfounded items.\n"
            "Return JSON matching:\n"
            "{\n"
            '  "confirmed_risks": [\n'
            "    {\n"
            '      "category": "AUTO_RENEWAL",\n'
            '      "severity": "HIGH" | "MEDIUM" | "LOW",\n'
            '      "title": "Title",\n'
            '      "summary": "Summary",\n'
            '      "procurement_impact": "Impact",\n'
            '      "review_reason": "Reason",\n'
            '      "evidence_id": "E1"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_content = f"VENDOR: {vendor_name}\nCANDIDATES:\n{json.dumps(candidate_pack[:5], indent=2)}"

        raw = self.groq_service.generate_json_response(system_prompt=system_prompt, user_content=user_content)
        parsed = json.loads(raw)
        items = parsed.get("confirmed_risks", [])

        findings: List[RiskFindingModel] = []
        for it in items:
            eid = it.get("evidence_id")
            match = next((c for c in candidate_pack if c["evidence_id"] == eid), None)
            if not match:
                continue

            try:
                cat_enum = RiskCategory[it.get("category", "OTHER_REVIEW_REQUIRED").upper()]
            except KeyError:
                cat_enum = RiskCategory.OTHER_REVIEW_REQUIRED

            try:
                sev_enum = RiskSeverity[it.get("severity", "MEDIUM").upper()]
            except KeyError:
                sev_enum = RiskSeverity.MEDIUM

            cit = EvidenceCitationModel(
                evidence_id=match["evidence_id"],
                vendor_name=match["vendor_name"],
                source_filename=match["source_filename"],
                start_page=match["start_page"],
                end_page=match["end_page"],
                chunk_id=match["chunk_id"],
                excerpt_text=match["text"],
            )

            r_id = f"rsk_{re.sub(r'[^a-zA-Z0-9]', '', vendor_name).lower()}_{cat_enum.value.lower()}_groq_{len(findings)+1}"

            findings.append(
                RiskFindingModel(
                    risk_id=r_id,
                    vendor_name=vendor_name,
                    category=cat_enum,
                    severity=sev_enum,
                    title=it.get("title", f"Contract Review: {cat_enum.value}"),
                    summary=it.get("summary", match["text"][:150]),
                    procurement_impact=it.get("procurement_impact", "May warrant legal review."),
                    review_reason=it.get("review_reason", "Ambiguous term identified."),
                    evidence_citations=[cit],
                    related_requirement_ids=[],
                    status=RiskStatus.DETECTED,
                )
            )

        return findings

    def _validate_and_deduplicate_findings(
        self,
        session_id: str,
        findings: List[RiskFindingModel],
        requirements: Optional[ProcurementRequirements],
    ) -> List[RiskFindingModel]:
        """Apply suppression tests, evidence binding, requirement linking, and deduplication."""
        final_list: List[RiskFindingModel] = []
        seen_keys: Set[Tuple[str, str, str]] = set()

        for f in findings:
            # 0. Severity policy capping: Cap ungrounded CRITICAL ratings to HIGH for non-uncapped liability categories
            if f.severity == RiskSeverity.CRITICAL and f.category != RiskCategory.UNCAPPED_LIABILITY:
                f.severity = RiskSeverity.HIGH

            citation_text = " ".join([c.excerpt_text.lower() for c in f.evidence_citations])
            risk_def = TAXONOMY_KNOWLEDGE_BASE.get(f.category)

            # 1. Suppression check
            if risk_def and risk_def.suppression_patterns:
                if any(re.search(pat, citation_text) for pat in risk_def.suppression_patterns):
                    continue

            # 2. Requirement Impact Linking
            rel_reqs: List[str] = []
            if requirements:
                if f.category == RiskCategory.AUTO_RENEWAL and requirements.renewal_preference:
                    rel_reqs.append("REQ_RENEWAL")
                elif f.category in {RiskCategory.LIABILITY_CAP, RiskCategory.UNCAPPED_LIABILITY} and requirements.liability_requirement:
                    rel_reqs.append("REQ_LIABILITY")
                elif f.category in {RiskCategory.TERMINATION_RESTRICTION, RiskCategory.EARLY_TERMINATION_FEE} and requirements.termination_requirement:
                    rel_reqs.append("REQ_TERMINATION")
                elif f.category == RiskCategory.SUPPORT_LIMITATION and requirements.support_requirement:
                    rel_reqs.append("REQ_SUPPORT")

            f.related_requirement_ids = rel_reqs

            # 3. Deduplication by (vendor_name, category, primary excerpt prefix)
            primary_excerpt = f.evidence_citations[0].excerpt_text[:40].lower() if f.evidence_citations else ""
            dedup_key = (f.vendor_name.lower(), f.category.value, primary_excerpt)

            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                final_list.append(f)

        return final_list
