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


def ask_question(api_key: str, redacted_text: str, risk_summary: str, question: str) -> str:
    if not api_key:
        return "Please enter a Groq API key in the sidebar to use Q&A (free at console.groq.com)."

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
