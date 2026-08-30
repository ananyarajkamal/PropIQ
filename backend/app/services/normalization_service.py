"""Deterministic terminology normalization service for PropIQ.

Converts vendor proposal facts expressed in diverse formats (e.g. 720 hours -> 30 days,
8.76 hours annual downtime -> 99.9% uptime, Net 30/written words, ISO 27001 variants)
into canonical structured representations while preserving original raw wording intact.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from app.models import NormalizedValueModel

logger = logging.getLogger("propiq_backend")

# Controlled word-to-number dictionary for legal/procurement natural language
WORD_TO_NUMBER: Dict[str, float] = {
    "zero": 0.0,
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
    "eleven": 11.0,
    "twelve": 12.0,
    "thirteen": 13.0,
    "fourteen": 14.0,
    "fifteen": 15.0,
    "sixteen": 16.0,
    "seventeen": 17.0,
    "eighteen": 18.0,
    "nineteen": 19.0,
    "twenty": 20.0,
    "twenty-four": 24.0,
    "thirty": 30.0,
    "forty": 40.0,
    "forty-five": 45.0,
    "fifty": 50.0,
    "sixty": 60.0,
    "ninety": 90.0,
}


def replace_word_numbers_in_text(text: str) -> str:
    """Generic converter replacing English word numbers with digits in text."""
    if not text:
        return text
    
    result = text
    # Replace compound/hyphenated words first
    sorted_words = sorted(WORD_TO_NUMBER.keys(), key=lambda w: len(w), reverse=True)
    for word in sorted_words:
        num_val = int(WORD_TO_NUMBER[word])
        # Replace word bounded by word boundaries
        pattern = r'\b' + re.escape(word) + r'\b'
        result = re.sub(pattern, str(num_val), result, flags=re.IGNORECASE)
    return result


def parse_numeric_word_or_float(text: str) -> Optional[float]:
    """Parse integer, float, or controlled numeric word safely without eval."""
    clean = text.strip().lower()
    if clean in WORD_TO_NUMBER:
        return WORD_TO_NUMBER[clean]
    try:
        clean_num = re.sub(r"[^\d.]", "", clean)
        return float(clean_num) if clean_num else None
    except ValueError:
        return None


class NormalizationService:
    """Service providing deterministic normalization for vendor proposal facts."""

    @staticmethod
    def normalize_duration(raw_value: Optional[str]) -> NormalizedValueModel:
        """Normalize duration strings into canonical days or months.

        Examples:
            "720 hours" -> 30.0 days (NORMALIZED)
            "4 weeks" -> 28.0 days (NORMALIZED)
            "30 days" -> 30.0 days (ALREADY_STANDARD)
            "30 to 45 days" -> {"min": 30.0, "max": 45.0} days (NORMALIZED)
        """
        if not raw_value or not raw_value.strip():
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=None,
                normalized_unit=None,
                normalization_status="NOT_APPLICABLE",
            )

        text = raw_value.strip().lower()

        # Check for Range e.g. "30 to 45 days" or "30 - 45 days"
        range_match = re.search(r"(\d+(?:\.\d+)?|\b\w+\b)\s*(?:to|-)\s*(\d+(?:\.\d+)?|\b\w+\b)\s*(day|hour|week|month|year)", text)
        if range_match:
            min_v = parse_numeric_word_or_float(range_match.group(1))
            max_v = parse_numeric_word_or_float(range_match.group(2))
            unit_str = range_match.group(3)

            if min_v is not None and max_v is not None:
                mult = 1.0
                c_unit = "days"
                approx = False

                if "hour" in unit_str:
                    mult = 1.0 / 24.0
                elif "week" in unit_str:
                    mult = 7.0
                elif "month" in unit_str:
                    mult = 30.4375
                    approx = True
                elif "year" in unit_str:
                    mult = 365.0
                    approx = True

                return NormalizedValueModel(
                    raw_value=raw_value,
                    normalized_value={"min": round(min_v * mult, 2), "max": round(max_v * mult, 2)},
                    normalized_unit=c_unit,
                    normalization_status="NORMALIZED",
                    approximate_conversion=approx,
                    notes=f"Duration range normalized to {c_unit}.",
                )

        # Single duration extraction e.g. "720 hours", "60 minutes", "4 weeks", "12 months"
        text_with_digits = replace_word_numbers_in_text(text)
        dur_match = re.search(r"(\d+(?:\.\d+)?|\b\w+\b)\s*(hour|hr|minute|min|mins|day|week|wk|month|mo|year|yr)", text_with_digits)
        if not dur_match:
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=None,
                normalized_unit=None,
                normalization_status="UNSUPPORTED",
                notes="Could not parse numeric duration value.",
            )

        val_num = parse_numeric_word_or_float(dur_match.group(1))
        unit_raw = dur_match.group(2).lower()

        if val_num is None:
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=None,
                normalized_unit=None,
                normalization_status="UNSUPPORTED",
            )

        if "min" in unit_raw:
            c_val = round(val_num / 1440.0, 4)
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=c_val,
                normalized_unit="days",
                normalization_status="NORMALIZED",
                approximate_conversion=False,
                notes=f"{val_num} minutes converted to {c_val} days.",
            )

        if "hour" in unit_raw or "hr" in unit_raw:
            c_val = round(val_num / 24.0, 2)
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=c_val,
                normalized_unit="days",
                normalization_status="NORMALIZED",
                approximate_conversion=False,
                notes=f"{val_num} hours converted to {c_val} days.",
            )
        elif "week" in unit_raw or "wk" in unit_raw:
            c_val = round(val_num * 7.0, 2)
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=c_val,
                normalized_unit="days",
                normalization_status="NORMALIZED",
                approximate_conversion=False,
                notes=f"{val_num} weeks converted to {c_val} days.",
            )
        elif "month" in unit_raw or "mo" in unit_raw:
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=val_num,
                normalized_unit="months",
                normalization_status="ALREADY_STANDARD" if unit_raw in {"month", "months"} else "NORMALIZED",
                approximate_conversion=False,
                notes=f"{val_num} months duration.",
            )
        elif "year" in unit_raw or "yr" in unit_raw:
            c_val = round(val_num * 12.0, 2)
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=c_val,
                normalized_unit="months",
                normalization_status="NORMALIZED",
                approximate_conversion=False,
                notes=f"{val_num} year(s) converted to {c_val} months.",
            )
        elif "day" in unit_raw:
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=val_num,
                normalized_unit="days",
                normalization_status="ALREADY_STANDARD",
            )

        return NormalizedValueModel(
            raw_value=raw_value,
            normalized_value=val_num,
            normalized_unit="days",
            normalization_status="NORMALIZED",
        )

    @staticmethod
    def normalize_sla(raw_value: Optional[str]) -> NormalizedValueModel:
        """Normalize SLA availability representations (uptime % or downtime hours).

        Examples:
            "99.9% monthly uptime" -> 99.9 percent_uptime (ALREADY_STANDARD)
            "8.76 hours annual downtime" -> 99.9 percent_uptime (NORMALIZED)
            "52.56 minutes annual downtime" -> 99.99 percent_uptime (NORMALIZED)
        """
        if not raw_value or not raw_value.strip():
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=None,
                normalized_unit=None,
                normalization_status="NOT_APPLICABLE",
            )

        text = raw_value.strip().lower()

        period = "annual" if "annual" in text or "year" in text else "monthly" if "month" in text else "unspecified"
        qualifier = "target" if "target" in text or "expected" in text else "guaranteed" if "guarante" in text or "commit" in text else "standard"

        # 1. Direct percentage uptime match e.g. "99.9%", "99.95%", "99.99%"
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        if pct_match:
            try:
                val = float(pct_match.group(1))
                if 0.0 <= val <= 100.0:
                    return NormalizedValueModel(
                        raw_value=raw_value,
                        normalized_value=val,
                        normalized_unit="percent_uptime",
                        normalization_status="ALREADY_STANDARD" if text.strip() == f"{val}%" else "NORMALIZED",
                        notes=f"Uptime percentage {val}% (Period: {period}, Qualifier: {qualifier}).",
                    )
            except ValueError:
                pass

        # 2. Downtime conversion match e.g. "8.76 hours annual downtime" or "52.56 minutes annual downtime"
        dt_match = re.search(r"(\d+(?:\.\d+)?)\s*(hour|hr|minute|min)s?.*downtime", text)
        if dt_match:
            try:
                dt_val = float(dt_match.group(1))
                dt_unit = dt_match.group(2)

                total_hours_year = 8760.0
                if "min" in dt_unit:
                    dt_hours = dt_val / 60.0
                else:
                    dt_hours = dt_val

                calc_uptime = round(100.0 - (dt_hours / total_hours_year * 100.0), 4)

                return NormalizedValueModel(
                    raw_value=raw_value,
                    normalized_value=calc_uptime,
                    normalized_unit="percent_uptime",
                    normalization_status="NORMALIZED",
                    approximate_conversion=True,
                    notes=f"Converted {dt_val} {dt_unit} downtime to {calc_uptime}% annual uptime.",
                )
            except ValueError:
                pass

        return NormalizedValueModel(
            raw_value=raw_value,
            normalized_value=None,
            normalized_unit="percent_uptime",
            normalization_status="UNSUPPORTED",
            notes="Unrecognized SLA format.",
        )

    @staticmethod
    def normalize_pricing(raw_value: Optional[str]) -> NormalizedValueModel:
        """Normalize pricing into canonical currency, amount, and billing period."""
        if not raw_value or not raw_value.strip():
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=None,
                normalized_unit=None,
                normalization_status="NOT_APPLICABLE",
            )

        text = raw_value.strip()

        currency = "USD"
        if "₹" in text or "inr" in text.lower() or "rs" in text.lower():
            currency = "INR"
        elif "€" in text or "eur" in text.lower():
            currency = "EUR"
        elif "£" in text or "gbp" in text.lower():
            currency = "GBP"

        lower_text = text.lower()
        b_period = "annual" if any(w in lower_text for w in ["annually", "annual", "year", "yr", "/yr", "per annum", "p.a."]) else \
                   "monthly" if any(w in lower_text for w in ["monthly", "month", "/mo", "per month"]) else \
                   "one-time" if any(w in lower_text for w in ["one-time", "upfront", "fixed"]) else \
                   "unspecified"

        is_per_seat = "per user" in lower_text or "per seat" in lower_text or "per license" in lower_text

        k_match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", lower_text)
        if k_match:
            amount = float(k_match.group(1)) * 1000.0
        else:
            nums = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", text)
            if not nums:
                return NormalizedValueModel(
                    raw_value=raw_value,
                    normalized_value=None,
                    normalized_unit=currency,
                    normalization_status="UNSUPPORTED",
                )
            clean_nums = [float(n.replace(",", "")) for n in nums]
            amount = max(clean_nums)

        annual_amount = amount
        is_annualized = False
        if b_period == "monthly" and not is_per_seat:
            annual_amount = amount * 12.0
            is_annualized = True

        return NormalizedValueModel(
            raw_value=raw_value,
            normalized_value={
                "base_amount": amount,
                "annual_amount": annual_amount,
                "currency": currency,
                "billing_period": b_period,
                "is_per_seat": is_per_seat,
            },
            normalized_unit=currency,
            normalization_status="NORMALIZED",
            notes=f"Annualized to {currency} {annual_amount:,.2f}" if is_annualized else f"Parsed {currency} {amount:,.2f}",
        )

    @staticmethod
    def normalize_payment_terms(raw_value: Optional[str]) -> NormalizedValueModel:
        """Normalize payment terms into due days or upfront milestone structures."""
        if not raw_value or not raw_value.strip():
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=None,
                normalized_unit=None,
                normalization_status="NOT_APPLICABLE",
            )

        text = raw_value.strip().lower()

        upfront_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*upfront", text)
        if upfront_match:
            uf_pct = float(upfront_match.group(1))
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value={
                    "due_days": 0,
                    "upfront_percentage": uf_pct,
                    "type": "upfront_milestone",
                },
                normalized_unit="days",
                normalization_status="NORMALIZED",
                notes=f"Requires {uf_pct}% upfront payment.",
            )

        days_match = re.search(r"(?:net\s*|within\s*|due\s*|in\s*)(\d+|\b\w+\b)\s*(?:days|calendar days)?", text)
        if days_match:
            days_val = parse_numeric_word_or_float(days_match.group(1))
            if days_val is not None:
                return NormalizedValueModel(
                    raw_value=raw_value,
                    normalized_value={
                        "due_days": int(days_val),
                        "upfront_percentage": 0.0,
                        "type": "net_terms",
                    },
                    normalized_unit="days",
                    normalization_status="NORMALIZED" if "thirty" in text else "ALREADY_STANDARD",
                    notes=f"Net {int(days_val)} days payment terms.",
                )

        return NormalizedValueModel(
            raw_value=raw_value,
            normalized_value=None,
            normalized_unit="days",
            normalization_status="UNSUPPORTED",
            notes="Unstructured payment terms.",
        )

    @staticmethod
    def normalize_certifications(raw_value: Optional[str]) -> NormalizedValueModel:
        """Normalize certification names into canonical uppercase strings."""
        if not raw_value or not raw_value.strip():
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=[],
                normalized_unit="certifications",
                normalization_status="NOT_APPLICABLE",
            )

        text = raw_value.strip()
        lower_text = text.lower()

        # Check for explicit negation BEFORE scanning keywords!
        if any(neg in lower_text for neg in ["not certified", "not iso", "none", "no certification", "pending certification"]):
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=[],
                normalized_unit="certifications",
                normalization_status="NORMALIZED",
                notes="Explicitly not certified.",
            )

        canonical_certs: List[str] = []

        if re.search(r"iso\s*-?\s*27001", lower_text):
            canonical_certs.append("ISO 27001")

        if re.search(r"soc\s*-?\s*2\s*type\s*ii|soc\s*-?\s*ii\s*type\s*ii", lower_text):
            canonical_certs.append("SOC 2 Type II")
        elif re.search(r"soc\s*-?\s*2|soc\s*-?\s*ii", lower_text):
            canonical_certs.append("SOC 2")

        if re.search(r"pci\s*-?\s*dss", lower_text):
            canonical_certs.append("PCI DSS")

        if "hipaa" in lower_text:
            canonical_certs.append("HIPAA")

        is_compliance_only = "compliant" in lower_text and "certified" not in lower_text

        return NormalizedValueModel(
            raw_value=raw_value,
            normalized_value=canonical_certs,
            normalized_unit="certifications",
            normalization_status="NORMALIZED" if canonical_certs else "UNSUPPORTED",
            notes="Compliance wording without formal certification" if is_compliance_only else None,
        )

    @staticmethod
    def normalize_warranty(raw_value: Optional[str]) -> NormalizedValueModel:
        """Normalize warranty coverage into months."""
        return NormalizationService.normalize_duration(raw_value)

    @staticmethod
    def normalize_renewal(raw_value: Optional[str]) -> NormalizedValueModel:
        """Normalize contract renewal clause attributes."""
        if not raw_value or not raw_value.strip():
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=None,
                normalization_status="NOT_APPLICABLE",
            )

        text = raw_value.strip().lower()
        is_auto = "auto" in text or "automatic" in text
        is_manual = "manual" in text or "upon agreement" in text or "opt-in" in text

        notice_days = None
        n_match = re.search(r"(\d+|\b\w+\b)\s*day", text)
        if n_match:
            notice_days = parse_numeric_word_or_float(n_match.group(1))

        return NormalizedValueModel(
            raw_value=raw_value,
            normalized_value={
                "renewal_type": "automatic" if is_auto else "manual" if is_manual else "unclear",
                "notice_period_days": int(notice_days) if notice_days is not None else None,
            },
            normalization_status="NORMALIZED",
        )

    @staticmethod
    def normalize_termination(raw_value: Optional[str]) -> NormalizedValueModel:
        """Normalize termination clause attributes."""
        if not raw_value or not raw_value.strip():
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=None,
                normalization_status="NOT_APPLICABLE",
            )

        text = raw_value.strip().lower()
        for_convenience = "convenience" in text or "without cause" in text or "any reason" in text
        cause_only = "cause" in text or "breach" in text

        notice_days = None
        n_match = re.search(r"(\d+|\b\w+\b)\s*day", text)
        if n_match:
            notice_days = parse_numeric_word_or_float(n_match.group(1))

        return NormalizedValueModel(
            raw_value=raw_value,
            normalized_value={
                "termination_for_convenience": for_convenience,
                "cause_only": cause_only and not for_convenience,
                "notice_period_days": int(notice_days) if notice_days is not None else None,
            },
            normalization_status="NORMALIZED",
        )

    @staticmethod
    def normalize_support(raw_value: Optional[str]) -> NormalizedValueModel:
        """Normalize technical support coverage windows."""
        if not raw_value or not raw_value.strip():
            return NormalizedValueModel(
                raw_value=raw_value,
                normalized_value=None,
                normalization_status="NOT_APPLICABLE",
            )

        text = raw_value.strip().lower()
        is_24_7 = any(w in text for w in ["24/7", "24x7", "24 x 7", "24 hours", "around the clock"])
        is_business = any(w in text for w in ["business hours", "8x5", "8/5", "weekdays", "9 to 5"])
        is_paid_addon = any(w in text for w in ["add-on", "premium", "extra fee", "available with"])

        return NormalizedValueModel(
            raw_value=raw_value,
            normalized_value={
                "window": "24_7" if is_24_7 else "business_hours" if is_business else "unspecified",
                "is_paid_addon": is_paid_addon,
            },
            normalization_status="NORMALIZED",
        )
