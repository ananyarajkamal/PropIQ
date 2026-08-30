"""Retrieval quality evaluation test suite using synthetic multi-page proposal PDFs.

Evaluates Recall@1, Recall@3, and Recall@5 on 20 procurement concepts using the real
sentence-transformers all-MiniLM-L6-v2 model and local FAISS vector store.
"""

import fitz
import pytest
from app.services.pdf_parser import parse_pdf_bytes
from app.services.chunker import chunk_document_pages
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import get_vector_store
from app.services.retrieval_service import RetrievalService


def create_vendor_a_pdf() -> bytes:
    """Generate synthetic PDF for Vendor A: Northstar Systems (5 pages)."""
    doc = fitz.open()

    # Page 1: Distractor / Background
    p1 = doc.new_page()
    p1.insert_text((50, 50), (
        "Northstar Systems Company Profile and Executive Overview.\n\n"
        "Northstar Systems is a leading enterprise software provider with over 15 years "
        "of industry experience delivering reliable cloud infrastructure and procurement systems."
    ))

    # Page 2: Pricing
    p2 = doc.new_page()
    p2.insert_text((50, 50), (
        "Commercial Proposal and Pricing Structure.\n\n"
        "The annual contract fee for Northstar Systems enterprise suite is $180,000 per year. "
        "This includes standard licensing, core maintenance, and platform updates."
    ))

    # Page 3: Payment & Implementation
    p3 = doc.new_page()
    p3.insert_text((50, 50), (
        "Payment Terms and Implementation Schedule.\n\n"
        "Invoices shall be settled Net 30 days of receipt by bank transfer.\n\n"
        "Implementation timeline is estimated at 30 days from contract execution."
    ))

    # Page 4: SLA & Support
    p4 = doc.new_page()
    p4.insert_text((50, 50), (
        "Service Level Agreement and Support Services.\n\n"
        "Northstar Systems guarantees 99.9% uptime availability SLA commitment.\n\n"
        "Customer support includes 24/7 critical incident response and dedicated account management."
    ))

    # Page 5: Legal Terms & Certifications
    p5 = doc.new_page()
    p5.insert_text((50, 50), (
        "Legal Terms, Warranty, and Security Certifications.\n\n"
        "Northstar Systems provides a 12 months warranty on software functionality.\n\n"
        "The company is ISO 27001 certified for information security.\n\n"
        "Total liability is capped at the annual contract value.\n\n"
        "Contract renewal occurs every 12 months with a 60-day advance notice requirement."
    ))

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_vendor_b_pdf() -> bytes:
    """Generate synthetic PDF for Vendor B: Meridian Labs (5 pages)."""
    doc = fitz.open()

    # Page 1: Distractor
    p1 = doc.new_page()
    p1.insert_text((50, 50), (
        "Meridian Labs Overview and Platform Architecture.\n\n"
        "Meridian Labs designs next-generation automated workflow solutions for modern procurement."
    ))

    # Page 2: Pricing & Payment
    p2 = doc.new_page()
    p2.insert_text((50, 50), (
        "Financial Terms and Payment Structure.\n\n"
        "The annual contract value is $165,000.\n\n"
        "Payment terms require 50% upfront payment upon signing, with remainder after deployment."
    ))

    # Page 3: Implementation
    p3 = doc.new_page()
    p3.insert_text((50, 50), (
        "Deployment and Onboarding Plan.\n\n"
        "The implementation timeline is 45 days following project kickoff."
    ))

    # Page 4: SLA & Warranty
    p4 = doc.new_page()
    p4.insert_text((50, 50), (
        "Service Levels and Guarantee.\n\n"
        "Service availability SLA target is 99.5% monthly uptime.\n\n"
        "Meridian Labs offers a 6 months warranty covering software defects."
    ))

    # Page 5: Security & Liability
    p5 = doc.new_page()
    p5.insert_text((50, 50), (
        "Security, Liability, and Renewal Terms.\n\n"
        "Meridian Labs is SOC 2 Type II certified.\n\n"
        "Uncapped liability applies for selected data protection claims.\n\n"
        "Terms include automatic annual renewal with 30-day notice required for non-renewal.\n\n"
        "Support is provided during standard business hours."
    ))

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_vendor_c_pdf() -> bytes:
    """Generate synthetic PDF for Vendor C: Vertex Solutions (5 pages)."""
    doc = fitz.open()

    # Page 1: Distractor
    p1 = doc.new_page()
    p1.insert_text((50, 50), (
        "Vertex Solutions Corporate Overview and References.\n\n"
        "Vertex Solutions provides secure enterprise operations platforms to global businesses."
    ))

    # Page 2: Pricing & Payment
    p2 = doc.new_page()
    p2.insert_text((50, 50), (
        "Commercial Proposal Details.\n\n"
        "Total pricing fee is $195,000 for the initial annual period.\n\n"
        "Payment terms are Net 45 days."
    ))

    # Page 3: Implementation
    p3 = doc.new_page()
    p3.insert_text((50, 50), (
        "Implementation Schedule.\n\n"
        "Deployment duration is estimated at 6 weeks for full integration."
    ))

    # Page 4: SLA & Warranty
    p4 = doc.new_page()
    p4.insert_text((50, 50), (
        "SLA and Warranty Terms.\n\n"
        "Vertex Solutions guarantees 99.95% monthly uptime SLA commitment.\n\n"
        "A 24 months warranty is included."
    ))

    # Page 5: Security & Terms
    p5 = doc.new_page()
    p5.insert_text((50, 50), (
        "Certifications, Liability, and Renewal.\n\n"
        "Vertex Solutions maintains ISO 27001 and SOC 2 certifications.\n\n"
        "Liability is limited to two times annual fees paid.\n\n"
        "Contract requires manual renewal upon expiration.\n\n"
        "Provides 24/7 customer support."
    ))

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_real_retrieval_quality_evaluation():
    """Execute real integration retrieval quality evaluation on 20 procurement queries.

    Calculates Recall@1, Recall@3, and Recall@5 using the actual all-MiniLM-L6-v2 model and FAISS.
    """
    embedding_service = EmbeddingService()
    vector_store = get_vector_store()
    retrieval_service = RetrievalService(embedding_service=embedding_service)

    # 1. Generate synthetic vendor PDFs
    pdf_a = create_vendor_a_pdf()
    pdf_b = create_vendor_b_pdf()
    pdf_c = create_vendor_c_pdf()

    pages_a, _, _ = parse_pdf_bytes(pdf_a, "northstar.pdf")
    pages_b, _, _ = parse_pdf_bytes(pdf_b, "meridian.pdf")
    pages_c, _, _ = parse_pdf_bytes(pdf_c, "vertex.pdf")

    chunks_a = chunk_document_pages("Northstar Systems", "northstar.pdf", 1, pages_a)
    chunks_b = chunk_document_pages("Meridian Labs", "meridian.pdf", 2, pages_b)
    chunks_c = chunk_document_pages("Vertex Solutions", "vertex.pdf", 3, pages_c)

    all_chunks = chunks_a + chunks_b + chunks_c
    chunk_texts = [c.text for c in all_chunks]

    embeddings = embedding_service.embed_texts(chunk_texts)
    session_id = "eval_session_synth_20"
    vector_store.create_session_index(session_id, embeddings, all_chunks)

    # 2. Define 20 procurement evaluation queries with expected target vendor and target page
    eval_queries = [
        {"query": "Northstar annual contract price $180,000", "expected_vendor": "Northstar Systems", "expected_page": 2},
        {"query": "Meridian 50% upfront payment terms", "expected_vendor": "Meridian Labs", "expected_page": 2},
        {"query": "Vertex total pricing fee $195,000", "expected_vendor": "Vertex Solutions", "expected_page": 2},
        {"query": "Invoices settled Net 30 days", "expected_vendor": "Northstar Systems", "expected_page": 3},
        {"query": "Meridian implementation timeline 45 days", "expected_vendor": "Meridian Labs", "expected_page": 3},
        {"query": "Vertex 6 weeks implementation schedule", "expected_vendor": "Vertex Solutions", "expected_page": 3},
        {"query": "Northstar 99.9% uptime SLA commitment", "expected_vendor": "Northstar Systems", "expected_page": 4},
        {"query": "Meridian 99.5% service availability SLA", "expected_vendor": "Meridian Labs", "expected_page": 4},
        {"query": "Vertex 99.95% monthly uptime SLA", "expected_vendor": "Vertex Solutions", "expected_page": 4},
        {"query": "Northstar 12 months warranty", "expected_vendor": "Northstar Systems", "expected_page": 5},
        {"query": "Meridian 6 months warranty", "expected_vendor": "Meridian Labs", "expected_page": 4},
        {"query": "Vertex 24 months warranty", "expected_vendor": "Vertex Solutions", "expected_page": 4},
        {"query": "Northstar ISO 27001 certification", "expected_vendor": "Northstar Systems", "expected_page": 5},
        {"query": "Meridian SOC 2 Type II certification", "expected_vendor": "Meridian Labs", "expected_page": 5},
        {"query": "Vertex liability limited to two times annual fees", "expected_vendor": "Vertex Solutions", "expected_page": 5},
        {"query": "Northstar total liability capped at annual contract value", "expected_vendor": "Northstar Systems", "expected_page": 5},
        {"query": "Meridian uncapped liability data protection", "expected_vendor": "Meridian Labs", "expected_page": 5},
        {"query": "Northstar 60-day renewal notice requirement", "expected_vendor": "Northstar Systems", "expected_page": 5},
        {"query": "Meridian automatic annual renewal 30-day notice", "expected_vendor": "Meridian Labs", "expected_page": 5},
        {"query": "Vertex 24/7 customer support", "expected_vendor": "Vertex Solutions", "expected_page": 5},
    ]

    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0

    for item in eval_queries:
        q = item["query"]
        expected_v = item["expected_vendor"]
        expected_p = item["expected_page"]

        res = retrieval_service.search_evidence(session_id=session_id, query=q, top_k=5)
        top_results = res.results

        # Helper checking if chunk covers expected vendor and page number
        def is_match(r):
            return r.vendor_name == expected_v and (r.start_page <= expected_p <= r.end_page)

        r1_match = any(is_match(r) for r in top_results[:1])
        r3_match = any(is_match(r) for r in top_results[:3])
        r5_match = any(is_match(r) for r in top_results[:5])

        if r1_match:
            hits_at_1 += 1
        if r3_match:
            hits_at_3 += 1
        if r5_match:
            hits_at_5 += 1

    total_q = len(eval_queries)
    recall_at_1 = hits_at_1 / total_q
    recall_at_3 = hits_at_3 / total_q
    recall_at_5 = hits_at_5 / total_q

    print(f"\n--- RETRIEVAL QUALITY EVALUATION REPORT ---")
    print(f"Queries Tested: {total_q}")
    print(f"Recall@1: {recall_at_1:.2f} ({hits_at_1}/{total_q})")
    print(f"Recall@3: {recall_at_3:.2f} ({hits_at_3}/{total_q})")
    print(f"Recall@5: {recall_at_5:.2f} ({hits_at_5}/{total_q})")

    # Quality Gate Assertion
    assert recall_at_3 >= 0.85, f"Recall@3 quality target failed: {recall_at_3:.2f} < 0.85"
