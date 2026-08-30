"""Unit tests verifying backend module imports and Pydantic schemas."""

import pytest


def test_internal_backend_imports():
    """Verify backend modules import cleanly without errors."""
    import app.config
    import app.logging_config
    import app.models
    import app.validators
    import app.utils
    import app.main

    assert app.config.Config.APP_NAME == "PropIQ API"


def test_models_instantiation():
    """Verify Pydantic models can be instantiated correctly."""
    from app.models import (
        HealthResponseModel,
        ApplicationConfigModel,
        VendorBasicInfo,
        SystemStatusModel,
    )

    health = HealthResponseModel()
    assert health.status == "ok"
    assert health.service == "PropIQ API"

    app_config = ApplicationConfigModel(groq_configured=True)
    assert app_config.app_name == "PropIQ API"
    assert app_config.groq_configured is True

    vendor = VendorBasicInfo(vendor_name="TechCorp")
    assert vendor.vendor_name == "TechCorp"

    status = SystemStatusModel(status_code="OK", message="System operational", is_ready=True)
    assert status.is_ready is True


def test_third_party_dependencies_import():
    """Verify core third-party backend dependencies import correctly."""
    import fastapi
    import uvicorn
    import pydantic
    import dotenv
    import fitz
    import pandas
    import groq

    assert fastapi.__version__ is not None
    assert uvicorn.__version__ is not None
    assert pydantic.__version__ is not None
    assert fitz.__version__ is not None
    assert pandas.__version__ is not None
