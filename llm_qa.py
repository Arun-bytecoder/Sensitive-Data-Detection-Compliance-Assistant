"""
llm_qa.py
Conversational Q&A over the uploaded document, powered by Groq's free API
(OpenAI-compatible endpoint, Llama 3.1 model).

IMPORTANT: this module is only ever given REDACTED document text (see
detector.redact_text). Raw sensitive values are never sent to a third-party
API -- this is a deliberate compliance/security design decision, not an
oversight.
"""

import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = (
    "You are a compliance assistant. You are given a REDACTED version of a "
    "document -- sensitive values have already been replaced with tags like "
    "[REDACTED-AADHAAR_NUMBER]. Answer the user's question using only the "
    "redacted document content and the risk summary provided. Never invent "
    "sensitive values. If asked to reveal a redacted value, explain that it "
    "has been redacted for security and cannot be shown."
)

SUMMARY_SYSTEM_PROMPT = (
    "You are a data compliance and security analyst. You are given a "
    "REDACTED document (sensitive values already replaced with tags like "
    "[REDACTED-AADHAAR_NUMBER]) and a rule-based risk report with counts per "
    "category. Write a concise, structured compliance summary with exactly "
    "these three sections, each as a markdown heading followed by 2-4 short "
    "bullet points:\n"
    "## Compliance Observations\n"
    "## Security Risks\n"
    "## Suggested Remediation Steps\n"
    "Base your analysis on the risk report and redaction tags only -- never "
    "guess or reconstruct an actual redacted value. Be specific to what was "
    "actually found (e.g. reference categories and counts from the risk "
    "report), not generic boilerplate."
)


def ask_question(api_key: str, redacted_text: str, risk_summary: str, question: str) -> str:
    if not api_key:
        return "Document Q&A is not configured. An administrator needs to set GROQ_API_KEY."

    truncated = redacted_text[:12000]  # keep prompt small / fast / cheap

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"RISK SUMMARY:\n{risk_summary}\n\n"
                    f"REDACTED DOCUMENT:\n{truncated}\n\n"
                    f"QUESTION: {question}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 500,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        return f"API error: {e}. Check that your Groq API key is valid."
    except Exception as e:
        return f"Something went wrong calling the LLM: {e}"


def generate_ai_summary(api_key: str, redacted_text: str, risk_summary: str) -> str:
    """
    Produces a narrative compliance summary with three sections: Compliance
    Observations, Security Risks, Suggested Remediation Steps. Only ever
    given the REDACTED document + the rule-based risk report -- never raw
    sensitive values. Returns None (caller should fall back to the
    deterministic summary) if no key is configured or the call fails.
    """
    if not api_key:
        return None

    truncated = redacted_text[:12000]

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"RISK REPORT:\n{risk_summary}\n\n"
                    f"REDACTED DOCUMENT:\n{truncated}"
                ),
            },
        ],
        "temperature": 0.3,
        "max_tokens": 600,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None  # caller falls back to the rule-based summary