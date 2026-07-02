import os
import re
import pandas as pd
import pdfplumber
import streamlit as st
from dotenv import load_dotenv

from detector import scan_text, compute_risk_score, generate_summary, redact_text, RISK_LEVELS
from llm_qa import ask_question
import theme

# ---------------------------------------------------------------------
# Credentials: production pattern. GROQ_API_KEY is read ONLY from the
# environment (.env locally, platform secrets when deployed). There is no
# UI field for it -- end users never see or enter a key, same as any real
# internal tool. If it's not configured, Q&A shows a quiet status instead
# of asking the visitor to supply their own credential.
# ---------------------------------------------------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

st.set_page_config(page_title="Secureguard — Sensitive Data Intelligence", layout="wide", page_icon="🛡️")
st.markdown(theme.CSS, unsafe_allow_html=True)


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
        rows = []
        for _, row in df.iterrows():
            rows.append(" | ".join(f"{col}: {val}" for col, val in row.items()))
        return "\n".join(rows)

    raw = uploaded_file.read()
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="ignore")
    return str(raw)


# ---------------------------------------------------------------------
# Sidebar — system status, not a credentials form
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        theme.clean("""
        <div class="vl-brand">
            <div class="vl-brand-mark">🛡️</div>
            <div class="vl-brand-name">Secureguard</div>
        </div>
        <div class="vl-brand-sub">Sensitive Data Intelligence</div>
        """),
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)

    st.markdown(
        theme.clean(f"""
        <div class="vl-status-row">
            <span class="vl-status-label"><span class="vl-dot" style="background:#3ECF8E;"></span>Detection engine</span>
            <span class="vl-status-pill vl-pill-on">ONLINE</span>
        </div>
        <div class="vl-status-row">
            <span class="vl-status-label"><span class="vl-dot" style="background:{'#3ECF8E' if GROQ_API_KEY else '#7C8695'};"></span>Document Q&A</span>
            <span class="vl-status-pill {'vl-pill-on' if GROQ_API_KEY else 'vl-pill-off'}">{'CONFIGURED' if GROQ_API_KEY else 'NOT CONFIGURED'}</span>
        </div>
        """),
        unsafe_allow_html=True,
    )

    st.markdown(
        theme.clean("""
        <div class="vl-sidebar-note">
        <b>How this works</b><br>
        Detection runs entirely with local pattern rules — nothing is uploaded
        to a server. If document Q&A is enabled, only a <b>redacted</b> copy
        of the text (sensitive values replaced with tags) is ever sent to the
        language model.
        </div>
        """),
        unsafe_allow_html=True,
    )

    if not GROQ_API_KEY:
        st.markdown(
            theme.clean("""
            <div class="vl-sidebar-note" style="margin-top:10px;">
            <b>For administrators</b><br>
            Set <code>GROQ_API_KEY</code> in a local <code>.env</code> file or
            as a platform secret to enable Q&A. Free key at
            console.groq.com.
            </div>
            """),
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------
st.markdown(
    theme.clean("""
    <div class="vl-hero-eyebrow"><div class="vl-scan-bar"></div>PATTERN-BASED DETECTION · POC</div>
    <div class="vl-hero-title">Sensitive Data & Compliance Scan</div>
    <div class="vl-hero-sub">Upload a document to detect identity, financial, and credential data,
    get a risk-classified compliance summary, and ask questions about what it contains.</div>
    """),
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader("Upload a document", type=["pdf", "txt", "csv"], label_visibility="collapsed")

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
    st.markdown(theme.section_head("01", "Risk Dashboard"), unsafe_allow_html=True)
    st.markdown(theme.metric_cards(risk_report["overall_risk"], risk_report["counts"]), unsafe_allow_html=True)

    if risk_report["by_category"]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.markdown(theme.category_bars(risk_report["by_category"], RISK_LEVELS), unsafe_allow_html=True)

    # ---------------- Findings table ----------------
    st.markdown(theme.section_head("02", "Detected Sensitive Data"), unsafe_allow_html=True)
    if findings:
        df_findings = pd.DataFrame(
            [
                {"Category": f.category, "Risk": f.risk, "Masked Value": f.masked, "Context": f.context}
                for f in findings
            ]
        )
        st.dataframe(df_findings, use_container_width=True, hide_index=True)
        show_raw = st.checkbox("Show unmasked values (local only)")
        if show_raw:
            df_raw = pd.DataFrame(
                [{"Category": f.category, "Risk": f.risk, "Raw Value": f.value} for f in findings]
            )
            st.dataframe(df_raw, use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="vl-empty">No sensitive data detected in this document.</div>', unsafe_allow_html=True)

    # ---------------- Compliance summary ----------------
    st.markdown(theme.section_head("03", "Compliance Summary"), unsafe_allow_html=True)
    summary_html = summary.replace("\n", "<br>")
    summary_html = re.sub(r"\bHIGH\b", '<span class="vl-t-high">HIGH</span>', summary_html)
    summary_html = re.sub(r"\bMEDIUM\b", '<span class="vl-t-medium">MEDIUM</span>', summary_html)
    summary_html = re.sub(r"\bLOW\b", '<span class="vl-t-low">LOW</span>', summary_html)
    st.markdown(f'<div class="vl-terminal">{summary_html}</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.download_button("Download summary (.txt)", summary, file_name="compliance_summary.txt")

    # ---------------- Redacted preview ----------------
    with st.expander("Preview redacted document (this is what the LLM sees)"):
        redacted_preview_html = theme.render_redacted_html(redacted[:4000]).replace("\n", "<br>")
        st.markdown(
            f'<div class="vl-terminal">{redacted_preview_html}</div>',
            unsafe_allow_html=True,
        )

    # ---------------- Q&A ----------------
    st.markdown(theme.section_head("04", "Ask About This Document"), unsafe_allow_html=True)

    if not GROQ_API_KEY:
        st.markdown(
            '<div class="vl-empty">Document Q&A is not configured. An administrator needs to set '
            '<code>GROQ_API_KEY</code> to enable this feature.</div>',
            unsafe_allow_html=True,
        )
    else:
        question = st.text_input(
            "Your question", placeholder="e.g. What kind of financial data does this document contain?",
            label_visibility="collapsed",
        )
        if st.button("Ask") and question:
            with st.spinner("Thinking..."):
                answer = ask_question(GROQ_API_KEY, redacted, summary, question)
            st.session_state.history.append((question, answer))

        for q, a in reversed(st.session_state.history):
            st.markdown(
                theme.clean(f'<div class="vl-qa-card"><div class="vl-qa-q">{q}</div><div class="vl-qa-a">{a}</div></div>'),
                unsafe_allow_html=True,
            )

else:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    cats_html = "".join(
        f'<span class="vl-risk-pill" style="background:{theme.RISK_COLORS[r]}22; color:{theme.RISK_COLORS[r]}; margin:3px 6px 3px 0;">{c}</span>'
        for c, r in RISK_LEVELS.items()
    )
    st.markdown(
        f'<div class="vl-empty">Upload a PDF, TXT, or CSV file to begin.<br><br>{cats_html}</div>',
        unsafe_allow_html=True,
    )