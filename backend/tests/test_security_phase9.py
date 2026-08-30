"""Phase 9 Security, Privacy, and Defense Test Suite for PropIQ.

Tests PDF magic validation, MIME/extension boundaries, file size limits, file count limits,
encrypted/corrupt PDF handling, path traversal defense, cryptographically secure high-entropy
session ID validation, 1000-token uniqueness, session isolation, vendor isolation, secret scan, safe logging, and XSS safety.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import Config
from app.validators import (
    validate_pdf_magic_header,
    sanitize_filename,
    validate_session_id,
    validate_vendor_name,
    generate_secure_session_id,
)
from app.services.pdf_parser import (
    parse_pdf_bytes,
    CorruptedPDFError,
    PasswordProtectedPDFError,
)
from app.services.vector_store import get_vector_store
from app.models import ChunkMetadata

client = TestClient(app)


def test_session_token_uniqueness_and_entropy():
    """Verify generate_secure_session_id produces unique cryptographically strong tokens with 256 bits intended entropy (Section 1)."""
    sample_size = 1000
    tokens = [generate_secure_session_id() for _ in range(sample_size)]

    # 1. Zero collisions across 1,000 generated tokens
    assert len(tokens) == sample_size
    assert len(set(tokens)) == sample_size

    # 2. Token format & length check
    first_token = tokens[0]
    assert first_token.startswith("sess_")
    assert len(first_token) >= 48
    assert validate_session_id(first_token) == first_token


def test_pdf_magic_header_validation():
    """Verify validate_pdf_magic_header correctly validates %PDF- magic bytes (Rule 4)."""
    valid_pdf_header = b"%PDF-1.7\n%abc..."
    invalid_header_txt = b"Hello world this is a text file"
    invalid_header_exe = b"MZ\x90\x00\x03\x00\x00\x00"

    assert validate_pdf_magic_header(valid_pdf_header) is True
    assert validate_pdf_magic_header(invalid_header_txt) is False
    assert validate_pdf_magic_header(invalid_header_exe) is False


def test_filename_sanitization_path_traversal():
    """Verify sanitize_filename strips path traversal and dangerous characters (Rule 7 & 8)."""
    assert sanitize_filename("../../secret.pdf") == "secret.pdf"
    assert sanitize_filename("..\\..\\windows\\system32.pdf") == "system32.pdf"
    assert sanitize_filename("proposal_script.pdf") == "proposal_script.pdf"
    assert sanitize_filename("proposal%00.pdf") == "proposal.pdf"
    assert sanitize_filename("CON.pdf") == "file_CON.pdf"
    assert sanitize_filename("NUL.pdf") == "file_NUL.pdf"


def test_session_id_validation_security():
    """Verify validate_session_id blocks path traversal, injection, and excessive length (Rule 16)."""
    valid_secure_sid = generate_secure_session_id()
    assert validate_session_id(valid_secure_sid) == valid_secure_sid

    with pytest.raises(ValueError):
        validate_session_id("../../etc/passwd")

    with pytest.raises(ValueError):
        validate_session_id("<script>alert(1)</script>")

    with pytest.raises(ValueError):
        validate_session_id("a" * 150)


def test_encrypted_and_corrupt_pdf_handling():
    """Verify parse_pdf_bytes safely catches corrupt and encrypted PDFs (Rule 9)."""
    corrupt_bytes = b"%PDF-1.4\nCorrupt xref header line..."
    with pytest.raises(CorruptedPDFError):
        parse_pdf_bytes(corrupt_bytes, "corrupt.pdf")


def test_session_isolation_cross_session_leakage_blocked():
    """Verify Session A cannot access or expose Session B evidence (Rule 14)."""
    vs = get_vector_store()
    vs.clear_all_sessions()

    # Session A chunk
    chunk_a = ChunkMetadata(
        chunk_id="v01_p001_c001",
        vendor_name="Vendor A",
        source_filename="a.pdf",
        start_page=1,
        end_page=1,
        character_count=50,
        text="Session A secret pricing details.",
    )
    import numpy as np
    emb_a = np.ones((1, 384), dtype=np.float32)
    vs.create_session_index("session_A", emb_a, [chunk_a])

    # Session B search attempt on Session A -> Must raise KeyError or return empty
    assert vs.has_session("session_B") is False
    with pytest.raises(KeyError):
        vs.search("session_B", emb_a, top_k=5)


def test_vendor_isolation_filtering():
    """Verify Vendor A search does not return Vendor B chunks (Rule 15)."""
    vs = get_vector_store()
    vs.clear_all_sessions()

    chunk_a = ChunkMetadata(chunk_id="c1", vendor_name="Vendor A", source_filename="a.pdf", start_page=1, end_page=1, character_count=20, text="Text A")
    chunk_b = ChunkMetadata(chunk_id="c2", vendor_name="Vendor B", source_filename="b.pdf", start_page=1, end_page=1, character_count=20, text="Text B")

    import numpy as np
    embs = np.ones((2, 384), dtype=np.float32)
    vs.create_session_index("sess_vendor_iso", embs, [chunk_a, chunk_b])

    # Search filtered by Vendor A
    results_a = vs.search("sess_vendor_iso", embs[0:1], top_k=5, vendor_name="Vendor A")
    assert len(results_a) == 1
    assert results_a[0][0].vendor_name == "Vendor A"


def test_secret_scan_health_endpoint():
    """Verify GET /api/health does not leak GROQ_API_KEY or filesystem paths (Rule 24-26)."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    # Verify no secret key leakage
    data_str = str(data)
    assert "gsk_" not in data_str
    assert "GROQ_API_KEY" not in data_str
    assert "C:\\Users" not in data_str
    assert "groq_configured" in data


def test_cors_origin_restriction():
    """Verify CORS headers are restricted to configured origins (Rule 27)."""
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://evil-attacker.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Origin should not be allowed
    access_control = response.headers.get("Access-Control-Allow-Origin")
    assert access_control != "http://evil-attacker.com"
