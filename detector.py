"""
detector.py
Rule-based sensitive data detection engine.

Design choice: detection is 100% deterministic (regex + validation rules),
NOT LLM-based. This keeps it explainable, auditable, and free to run --
important for a compliance tool where you need to justify *why* something
was flagged. The LLM (see llm_qa.py) is only used for the conversational
Q&A layer, and only ever sees REDACTED text (see redact_findings()).
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Finding:
    category: str
    risk: str          # HIGH / MEDIUM / LOW
    value: str          # raw matched value
    masked: str         # masked-for-display value
    start: int
    end: int
    context: str = ""   # small window of surrounding text


# ---------------------------------------------------------------------
# Risk levels per category (compliance-driven judgement call, documented
# in README): identity + financial = HIGH, contact/internal-ref = MEDIUM,
# generic/public-facing = LOW.
# ---------------------------------------------------------------------
RISK_LEVELS = {
    "Aadhaar Number": "HIGH",
    "PAN Number": "HIGH",
    "Credit Card Number": "HIGH",
    "Bank Account / IFSC": "HIGH",
    "API Key / Password": "HIGH",
    "Phone Number": "MEDIUM",
    "Employee ID": "MEDIUM",
    "Confidential Business Info": "MEDIUM",
    "Email Address": "LOW",
}

RISK_WEIGHT = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


# ---------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------
PATTERNS: Dict[str, re.Pattern] = {
    "Aadhaar Number": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    "PAN Number": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    "Email Address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "Phone Number": re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"),
    "Credit Card Number": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "Bank Account / IFSC": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),  # IFSC code
    "API Key / Password": re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|pwd)\b\s*[:=]\s*[\'\"]?[A-Za-z0-9_\-/+]{6,}[\'\"]?"
        r"|AKIA[0-9A-Z]{16}"
        r"|sk-[A-Za-z0-9]{20,}"
    ),
    "Employee ID": re.compile(r"(?i)\bEMP[-_]?\d{3,6}\b"),
    "Confidential Business Info": re.compile(
        r"(?i)\b(confidential|internal use only|proprietary|do not distribute|trade secret|not for external distribution)\b"
    ),
}

CONFIDENTIAL_KEYWORDS = {"Confidential Business Info"}  # keyword hits, not PII values


def _luhn_valid(number: str) -> bool:
    digits = [int(d) for d in re.sub(r"\D", "", number)]
    if len(digits) < 13:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _mask(category: str, value: str) -> str:
    v = value.strip()
    if category in ("Aadhaar Number", "Credit Card Number"):
        digits = re.sub(r"\D", "", v)
        return "XXXX-XXXX-" + digits[-4:] if len(digits) >= 4 else "XXXX"
    if category == "PAN Number":
        return v[:2] + "XXX" + v[-2:]
    if category == "Email Address":
        name, _, domain = v.partition("@")
        return (name[:2] + "***@" + domain) if name else "***@" + domain
    if category == "Phone Number":
        digits = re.sub(r"\D", "", v)
        return "XXXXXX" + digits[-4:]
    if category == "API Key / Password":
        return v[:12] + "...REDACTED"
    return v  # keywords / IFSC / employee ID shown as-is (not personally identifying)


def scan_text(text: str) -> List[Finding]:
    findings: List[Finding] = []
    for category, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            value = m.group(0)

            # Extra validation to cut false positives
            if category == "Credit Card Number":
                if not _luhn_valid(value):
                    continue
            if category == "Aadhaar Number":
                # skip if it's actually a valid-looking credit card / phone-like run
                digits = re.sub(r"\D", "", value)
                if len(digits) != 12:
                    continue

            start, end = m.span()
            ctx_start = max(0, start - 25)
            ctx_end = min(len(text), end + 25)
            findings.append(
                Finding(
                    category=category,
                    risk=RISK_LEVELS[category],
                    value=value,
                    masked=_mask(category, value),
                    start=start,
                    end=end,
                    context=text[ctx_start:ctx_end].replace("\n", " "),
                )
            )
    findings = _dedupe_overlaps(findings)
    # sort by position in doc
    findings.sort(key=lambda f: f.start)
    return findings


def _dedupe_overlaps(findings: List[Finding]) -> List[Finding]:
    """
    When two patterns match overlapping spans (e.g. the first 12 digits of a
    16-digit credit card also satisfy the Aadhaar pattern), keep only the
    match with the longer span -- it's the more specific/confident match.
    """
    findings = sorted(findings, key=lambda f: (f.start, -(f.end - f.start)))
    kept: List[Finding] = []
    for f in findings:
        overlaps = False
        for k in kept:
            if f.start < k.end and k.start < f.end:  # spans overlap
                overlaps = True
                break
        if not overlaps:
            kept.append(f)
    return kept


def compute_risk_score(findings: List[Finding]) -> Dict:
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    by_category: Dict[str, int] = {}
    for f in findings:
        counts[f.risk] += 1
        by_category[f.category] = by_category.get(f.category, 0) + 1

    weighted = sum(RISK_WEIGHT[f.risk] for f in findings)
    if counts["HIGH"] > 0:
        overall = "HIGH"
    elif counts["MEDIUM"] > 0:
        overall = "MEDIUM"
    elif counts["LOW"] > 0:
        overall = "LOW"
    else:
        overall = "CLEAN"

    return {
        "overall_risk": overall,
        "counts": counts,
        "by_category": by_category,
        "weighted_score": weighted,
        "total_findings": len(findings),
    }


def generate_summary(findings: List[Finding], risk_report: Dict, filename: str) -> str:
    if not findings:
        return f"No sensitive data detected in '{filename}'. Document appears clean."

    lines = [
        f"Compliance & Security Summary for '{filename}'",
        "=" * 50,
        f"Overall Risk Level: {risk_report['overall_risk']}",
        f"Total sensitive items detected: {risk_report['total_findings']}",
        f"  - HIGH risk items:   {risk_report['counts']['HIGH']}",
        f"  - MEDIUM risk items: {risk_report['counts']['MEDIUM']}",
        f"  - LOW risk items:    {risk_report['counts']['LOW']}",
        "",
        "Breakdown by category:",
    ]
    for cat, count in sorted(risk_report["by_category"].items(), key=lambda x: -x[1]):
        lines.append(f"  - {cat}: {count} instance(s) [{RISK_LEVELS[cat]}]")

    lines.append("")
    lines.append("Recommendation:")
    if risk_report["overall_risk"] == "HIGH":
        lines.append(
            "  This document contains highly sensitive identity/financial data "
            "(e.g. Aadhaar, PAN, card numbers, credentials). Restrict access, "
            "encrypt at rest, and avoid sharing via unsecured channels."
        )
    elif risk_report["overall_risk"] == "MEDIUM":
        lines.append(
            "  This document contains internal/contact information. Handle "
            "under standard confidentiality policy before external sharing."
        )
    else:
        lines.append("  Low sensitivity. Standard handling is sufficient.")

    return "\n".join(lines)


def redact_text(text: str, findings: List[Finding]) -> str:
    """
    Produce a fully redacted version of the document text, replacing every
    detected span with a [REDACTED-<CATEGORY>] tag. This redacted text is
    the ONLY version ever sent to the LLM for Q&A -- raw PII never leaves
    the app's process boundary.
    """
    if not findings:
        return text
    ordered = sorted(findings, key=lambda f: f.start)
    out = []
    cursor = 0
    for f in ordered:
        if f.start < cursor:
            continue  # overlapping match, skip
        out.append(text[cursor:f.start])
        tag = f.category.upper().replace(" ", "_").replace("/", "")
        out.append(f"[REDACTED-{tag}]")
        cursor = f.end
    out.append(text[cursor:])
    return "".join(out)
