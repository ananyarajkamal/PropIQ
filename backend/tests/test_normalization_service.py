"""Unit tests for NormalizationService module."""

import pytest
from app.services.normalization_service import NormalizationService


def test_normalize_duration_variations():
    """Verify duration normalization across hours, days, weeks, months, years, and ranges."""
    ns = NormalizationService()

    # 24 hours -> 1 day
    d1 = ns.normalize_duration("24 hours")
    assert d1.normalized_value == 1.0
    assert d1.normalized_unit == "days"

    # 48 hours -> 2 days
    d2 = ns.normalize_duration("48 hours")
    assert d2.normalized_value == 2.0
    assert d2.normalized_unit == "days"

    # 720 hours -> 30 days
    d3 = ns.normalize_duration("720 hours")
    assert d3.normalized_value == 30.0
    assert d3.normalized_unit == "days"

    # 4 weeks -> 28 days
    d4 = ns.normalize_duration("4 weeks")
    assert d4.normalized_value == 28.0
    assert d4.normalized_unit == "days"

    # 12 months -> 12 months
    d5 = ns.normalize_duration("12 months")
    assert d5.normalized_value == 12.0
    assert d5.normalized_unit == "months"

    # 1 year -> 12 months
    d6 = ns.normalize_duration("1 year")
    assert d6.normalized_value == 12.0
    assert d6.normalized_unit == "months"

    # Range: 30 to 45 days
    d7 = ns.normalize_duration("30 to 45 days")
    assert d7.normalized_value == {"min": 30.0, "max": 45.0}
    assert d7.normalized_unit == "days"


def test_normalize_sla_variations():
    """Verify SLA percentage parsing and downtime formula conversions."""
    ns = NormalizationService()

    # Direct percentage
    s1 = ns.normalize_sla("99.9% monthly uptime")
    assert s1.normalized_value == 99.9
    assert s1.normalized_unit == "percent_uptime"

    # Downtime formula conversion: 8.76 hours annual downtime = 99.9% uptime
    s2 = ns.normalize_sla("8.76 hours annual downtime")
    assert s2.normalized_value == 99.9
    assert s2.approximate_conversion is True

    # Downtime formula conversion: 52.56 minutes annual downtime = 99.99% uptime
    s3 = ns.normalize_sla("52.56 minutes annual downtime")
    assert s3.normalized_value == 99.99


def test_normalize_payment_terms_variations():
    """Verify Net terms and written number word parsing."""
    ns = NormalizationService()

    # Net 30
    p1 = ns.normalize_payment_terms("Net 30")
    assert p1.normalized_value["due_days"] == 30

    # Written words: "within thirty calendar days"
    p2 = ns.normalize_payment_terms("payable within thirty calendar days")
    assert p2.normalized_value["due_days"] == 30

    # Upfront payment
    p3 = ns.normalize_payment_terms("50% upfront, 50% on deployment")
    assert p3.normalized_value["upfront_percentage"] == 50.0


def test_normalize_certifications_variations():
    """Verify canonical certification string matching and negation handling."""
    ns = NormalizationService()

    # ISO 27001 variants
    c1 = ns.normalize_certifications("ISO27001")
    assert "ISO 27001" in c1.normalized_value

    c2 = ns.normalize_certifications("ISO-27001")
    assert "ISO 27001" in c2.normalized_value

    # SOC 2 Type II
    c3 = ns.normalize_certifications("SOC 2 Type II accredited")
    assert "SOC 2 Type II" in c3.normalized_value

    # Negation test
    c4 = ns.normalize_certifications("We are not ISO 27001 certified.")
    assert c4.normalized_value == []


def test_normalize_support_variations():
    """Verify technical support coverage window normalization."""
    ns = NormalizationService()

    s1 = ns.normalize_support("24/7 technical support included")
    assert s1.normalized_value["window"] == "24_7"
    assert s1.normalized_value["is_paid_addon"] is False

    s2 = ns.normalize_support("24x7 available with premium add-on")
    assert s2.normalized_value["window"] == "24_7"
    assert s2.normalized_value["is_paid_addon"] is True

    s3 = ns.normalize_support("Business hours support weekdays 9 AM to 5 PM")
    assert s3.normalized_value["window"] == "business_hours"
