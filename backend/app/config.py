"""Central application configuration for PropIQ FastAPI Backend.

Loads environment variables, defines system defaults, and specifies
hardware / embedding configuration constants.
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


class Config:
    """Application Configuration Settings."""

    # General System Identity
    APP_NAME: str = "PropIQ API"
    APP_VERSION: str = "1.0.0-hackathon"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS Allowed Origins
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    ALLOWED_CORS_ORIGINS: List[str] = [
        FRONTEND_ORIGIN,
        "http://127.0.0.1:5173",
    ]

    # File Processing Constraints
    MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB max file size limit
    MIN_PROPOSALS: int = 2
    MAX_PROPOSALS: int = 5
    MAX_PAGES_PER_PDF: int = 250
    MAX_EXTRACTED_CHARS_PER_DOC: int = 500_000

    # Session Lifetime Constraints
    SESSION_TTL_MINUTES: int = 60  # Auto-prune vector store sessions after 60 mins

    # Local Sentence-Transformers Embedding Settings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Vector Retrieval & Search Defaults
    DEFAULT_TOP_K: int = 5
    RERANK_TOP_K: int = 3

    # Groq Reasoning Service Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "groq/compound")
    GROQ_TIMEOUT_SECONDS: float = 30.0  # Finite request timeout
    MAX_LLM_RETRIES: int = 1

    # Security & Rate Limiting Constants
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 20
    MAX_TEXT_INPUT_LENGTH: int = 2000

    # Deterministic Scoring Engine Configuration
    SCORING_VERSION: str = "1.0"
    RECOMMENDATION_POLICY_VERSION: str = "1.0"

    # Structured Scoring Configuration Dictionary (Phase 7 Exact Baseline)
    SCORING_CONFIG: Dict[str, Any] = {
        "scoring_version": "1.0",
        "priority_weights": {
            "MUST_HAVE": 5.0,
            "HIGH": 4.0,
            "MEDIUM": 3.0,
            "LOW": 1.0,
        },
        "state_scores": {
            "MEETS": 1.0,
            "PARTIAL": 0.6,
            "UNCLEAR": 0.3,
            "FAILS": 0.0,
            "MISSING": 0.0,
            "CONFLICTING": 0.0,
        },
        "risk_penalties": {
            "LOW": 0.5,
            "MEDIUM": 1.5,
            "HIGH": 3.0,
            "CRITICAL": 6.0,
        },
        "risk_penalty_cap": 15.0,
        "linked_risk_reduction_factor": 0.50,
        "contradiction_penalties": {
            "CONFIRMED_CONTRADICTION": 2.5,
            "POTENTIAL_CONTRADICTION": 1.0,
            "CONTEXT_DEPENDENT": 0.0,
            "DISMISSED": 0.0,
        },
        "contradiction_penalty_cap": 10.0,
        "clarification_penalties": {
            "HIGH": 1.5,
            "MEDIUM": 0.75,
            "LOW": 0.25,
        },
        "clarification_penalty_cap": 8.0,
        "tie_tolerance": 0.5,
    }

    # Controlled Risk Categories Taxonomy Dictionary
    RISK_TAXONOMY: Dict[str, Any] = {
        "AUTO_RENEWAL": {"default_severity": "HIGH"},
        "LIABILITY_CAP": {"default_severity": "HIGH"},
        "UNCAPPED_LIABILITY": {"default_severity": "CRITICAL"},
        "TERMINATION_RESTRICTION": {"default_severity": "MEDIUM"},
        "EARLY_TERMINATION_FEE": {"default_severity": "MEDIUM"},
        "SUPPORT_LIMITATION": {"default_severity": "MEDIUM"},
        "SLA_EXCLUSION": {"default_severity": "HIGH"},
        "PRICE_INCREASE_CAP": {"default_severity": "MEDIUM"},
    }

    # Procurement Recommendation Policy Thresholds (Phase 8 Policy Hardening)
    TIE_THRESHOLD: float = 0.5  # Score difference < 0.5 indicates a tie
    CLOSE_LEADER_THRESHOLD: float = 2.0  # 0.5 <= Score difference < 2.0 indicates a close leader

    # Privacy & Legal Disclaimer Notice
    PRIVACY_NOTICE: str = (
        "Documents are processed locally. Only relevant retrieved excerpts "
        "are submitted to Groq for structured analysis."
    )

    @classmethod
    def get_groq_api_key(cls) -> str:
        """Retrieve configured Groq API key."""
        return cls.GROQ_API_KEY

    @classmethod
    def is_groq_configured(cls) -> bool:
        """Check if a valid Groq API key is present in environment."""
        return bool(cls.GROQ_API_KEY and cls.GROQ_API_KEY.strip())

    def __repr__(self) -> str:
        """Represent config without exposing API keys."""
        return f"<Config APP_NAME={self.APP_NAME} APP_VERSION={self.APP_VERSION} GROQ_CONFIGURED={self.is_groq_configured()}>"
