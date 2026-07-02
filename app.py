import io
import os
import pandas as pd
import pdfplumber
import streamlit as st
from dotenv import load_dotenv

from detector import scan_text, compute_risk_score, generate_summary, redact_text, RISK_LEVELS
from llm_qa import ask_question

# Production-style credential loading: reads GROQ_API_KEY from a local .env
# file (never committed -- see .gitignore) or from the deployment platform's
# environment/secrets store. This is a FALLBACK ONLY -- if the user pastes
# their own key in the sidebar, that one is used instead (see below). Using
# each user's own key avoids one shared key's free-tier quota being spent by
# everyone who tries the deployed demo.
load_dotenv()
DEFAULT_GROQ_KEY = os.getenv("GROQ_API_KEY", "")

st.set_page_config(page_title="Sensitive Data Detection & Compliance Assistant", layout="wide")


# ---------------------------------------------------------------------
# File text extraction
# ---------------------------------------------------------------------
def extract_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        text_parts = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
        return "\n".join(text_parts)

    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        # Flatten into text, keeping column context so a scan can still work
        rows = []
        for _, row in df.iterrows():
            rows.append(" | ".join(f"{col}: {val}" for col, val in row.items()))
        return "\n".join(rows)

    # .txt or anything else plain-text
    raw = uploaded_file.read()
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="ignore")
    return str(raw)


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    groq_key = st.text_input(
        "Groq API key (for Q&A only)", type="password",
        value=DEFAULT_GROQ_KEY,
        help="Free key from console.groq.com. Loaded from a local .env if "
             "present, otherwise paste your own. Only used to answer "
             "questions about the document -- raw sensitive data is never "
             "sent to it."
    )
    st.markdown("---")
    st.markdown(
        "**Privacy note:** All detection happens locally with regex rules. "
        "The document is never uploaded anywhere. If you use the Q&A feature, "
        "only a *redacted* version of the text (sensitive values replaced "
        "with tags) is sent to the LLM."
    )

st.title("🔒 Sensitive Data Detection & Compliance Assistant")
st.caption("Upload a document → detect sensitive data → get a risk-classified compliance summary → ask questions about it.")

uploaded_file = st.file_uploader("Upload a document", type=["pdf", "txt", "csv"])

if "history" not in st.session_state:
    st.session_state.history = []

if uploaded_file is not None:
    with st.spinner("Extracting text..."):
        text = extract_text(uploaded_file)

    if not text.strip():
        st.error("Couldn't extract any text from this file. It may be a scanned/image PDF.")
        st.stop()

    with st.spinner("Scanning for sensitive data..."):
        findings = scan_text(text)
        risk_report = compute_risk_score(findings)
        summary = generate_summary(findings, risk_report, uploaded_file.name)
        redacted = redact_text(text, findings)

    # ---------------- Risk dashboard ----------------
    st.subheader("📊 Risk Dashboard")
    risk_color = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡", "CLEAN": "🟢"}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall Risk", f"{risk_color[risk_report['overall_risk']]} {risk_report['overall_risk']}")
    c2.metric("High Risk Items", risk_report["counts"]["HIGH"])
    c3.metric("Medium Risk Items", risk_report["counts"]["MEDIUM"])
    c4.metric("Low Risk Items", risk_report["counts"]["LOW"])

    if risk_report["by_category"]:
        st.bar_chart(risk_report["by_category"])

    # ---------------- Findings table ----------------
    st.subheader("🔍 Detected Sensitive Data")
    if findings:
        df_findings = pd.DataFrame(
            [
                {
                    "Category": f.category,
                    "Risk": f.risk,
                    "Masked Value": f.masked,
                    "Context": f.context,
                }
                for f in findings
            ]
        )
        st.dataframe(df_findings, use_container_width=True)
        show_raw = st.checkbox("⚠️ Show unmasked values (local only, use with caution)")
        if show_raw:
            df_raw = pd.DataFrame(
                [{"Category": f.category, "Risk": f.risk, "Raw Value": f.value} for f in findings]
            )
            st.dataframe(df_raw, use_container_width=True)
    else:
        st.success("No sensitive data detected in this document.")

    # ---------------- Compliance summary ----------------
    st.subheader("📝 Compliance Summary")
    st.text(summary)
    st.download_button("Download summary (.txt)", summary, file_name="compliance_summary.txt")

    # ---------------- Q&A ----------------
    st.subheader("💬 Ask Questions About This Document")
    st.caption("Answers are generated from a REDACTED copy of the document — sensitive values are never sent to the LLM.")

    question = st.text_input("Your question", placeholder="e.g. What kind of financial data does this document contain?")
    if st.button("Ask") and question:
        with st.spinner("Thinking..."):
            answer = ask_question(groq_key, redacted, summary, question)
        st.session_state.history.append((question, answer))

    for q, a in reversed(st.session_state.history):
        st.markdown(f"**Q: {q}**")
        st.markdown(a)
        st.markdown("---")

else:
    st.info("Upload a PDF, TXT, or CSV file to get started.")
    with st.expander("What does this app detect?"):
        for cat, risk in RISK_LEVELS.items():
            st.markdown(f"- **{cat}** — `{risk}` risk")