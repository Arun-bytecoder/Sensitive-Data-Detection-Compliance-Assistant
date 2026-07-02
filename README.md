# Sensitive Data Detection & Compliance Assistant

An AI-powered app that scans uploaded documents (PDF / TXT / CSV) for sensitive
information, classifies it by risk level, generates a compliance summary, and
lets you ask questions about the document.


---

## Setup Instructions

```bash
git clone <your-repo-url>
cd sensitive-data-assistant
pip install -r requirements.txt
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

To use the **Q&A** feature, get a free API key at [console.groq.com](https://console.groq.com)
and paste it into the sidebar. Detection and risk scoring work fully offline
without any key.

A sample file with fake test data is included at `sample_data/sample.txt` —
upload it to see the app in action immediately.

---

## Architecture Overview

```
Upload (PDF/TXT/CSV)
        │
        ▼
  extract_text()          -- pdfplumber / pandas / plain read
        │
        ▼
  detector.scan_text()    -- regex + validation rules → Finding objects
        │
        ├──► compute_risk_score()   -- HIGH/MEDIUM/LOW aggregation
        ├──► generate_summary()     -- human-readable compliance report
        └──► redact_text()          -- replaces sensitive spans with tags
                    │
                    ▼
            llm_qa.ask_question()   -- Groq LLM, sees ONLY redacted text
                    │
                    ▼
              Streamlit UI (app.py)
```

**Files:**
- `app.py` – Streamlit UI: upload, dashboard, findings table, Q&A
- `detector.py` – detection engine (regex patterns, Luhn validation, risk
  classification, summary generation, redaction)
- `llm_qa.py` – Groq API wrapper for the Q&A feature
- `sample_data/sample.txt` – test document with fake sensitive data

---

## AI/ML Approach Used

Detection is **rule-based (regex + validation), not LLM-based**, by
deliberate choice:

- **Explainability** – every flag can be traced to an exact pattern match,
  which matters for a compliance tool (you need to justify *why* something
  was flagged, not just trust a black box).
- **Reliability & cost** – no API dependency, no hallucination risk, works
  fully offline, zero marginal cost per document.
- **Validation, not just pattern matching** – e.g. credit card numbers are
  verified with the **Luhn checksum algorithm** so random 16-digit numbers
  aren't falsely flagged.

Categories detected: Aadhaar Number, PAN Number, Email, Phone Number, Credit
Card Number (Luhn-validated), Bank Account/IFSC, API Keys/Passwords,
Employee ID, and Confidential Business Info (keyword-based).

**Risk classification** is a weighted rule: identity/financial data
(Aadhaar, PAN, card numbers, bank details, credentials) = HIGH; internal
references (phone, employee ID, confidentiality keywords) = MEDIUM;
low-sensitivity/public-facing (email) = LOW. Overall document risk = highest
individual risk level present.

The one place an **LLM is used** is the conversational Q&A layer (Groq,
Llama 3.1 8B — free tier). Deliberately, the LLM is only ever given a
**redacted** copy of the document (sensitive spans replaced with tags like
`[REDACTED-AADHAAR_NUMBER]`) plus the risk summary — raw PII is never sent
to a third-party API. This was a specific design decision to make the
"AI-powered" part of the app not undermine the "compliance assistant" part
of it.

---

## Challenges Faced

- **Overlapping matches** – a 16-digit credit card number's first 12 digits
  also satisfy the Aadhaar regex, causing double-flagging. Solved with an
  overlap-deduplication pass that keeps the longer/more specific match.
- **False positives on generic numbers** – added Luhn validation for credit
  cards instead of a plain digit-count regex, to avoid flagging arbitrary
  12–16 digit numbers.
- **Keeping the LLM from seeing PII** – had to build the redaction step
  *before* the Q&A feature, not after, since the whole point of "AI-powered"
  here needed to not conflict with the compliance goal of the tool.
- **CSV structure** – flattening rows into text for scanning while still
  keeping column context readable in the findings table.

## Future Improvements

- Named Entity Recognition (spaCy) as a second pass to catch names/addresses
  that pure regex can't reliably detect.
- Configurable/custom regex rules per organization (e.g. company-specific
  employee ID formats).
- Batch mode for scanning multiple files / a folder at once.
- Audit log of scans for compliance record-keeping.
- OCR support (pytesseract) for scanned/image-based PDFs.

---

## Deployment (Streamlit Community Cloud — free)

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → "New app" →
   select the repo → set main file to `app.py` → Deploy.
3. Copy the live URL into this README and your submission.

No Groq key needs to be set as a deployment secret — users enter their own
in the sidebar, so the deployed app costs you nothing to host or run.
