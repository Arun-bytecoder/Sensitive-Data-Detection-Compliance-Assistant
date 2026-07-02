"""
theme.py
Design system for the Sensitive Data Detection & Compliance Assistant UI.

Token system:
  Background   #0A0E13   near-black, blue-slate (not pure black)
  Surface      #111720   card background
  Surface-2    #161D28   nested/inset surface
  Border       #1F2733
  Text         #E6EAF0
  Text-muted   #7C8695
  Brand accent #29D9C7   "scanner" teal -- distinct from risk-severity colors
  Risk HIGH    #FF5470
  Risk MEDIUM  #FFB454
  Risk LOW     #5FA8FF
  Risk CLEAN   #3ECF8E

Type: Archivo (display, condensed/tracked, uppercase) for headers and brand;
Inter for body copy; JetBrains Mono for data values, tags, and log-style text.
"""

RISK_COLORS = {
    "HIGH": "#FF5470",
    "MEDIUM": "#FFB454",
    "LOW": "#5FA8FF",
    "CLEAN": "#3ECF8E",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg: #0A0E13;
    --surface: #111720;
    --surface-2: #161D28;
    --border: #1F2733;
    --text: #E6EAF0;
    --text-muted: #7C8695;
    --brand: #29D9C7;
    --brand-dim: rgba(41, 217, 199, 0.12);
    --risk-high: #FF5470;
    --risk-medium: #FFB454;
    --risk-low: #5FA8FF;
    --risk-clean: #3ECF8E;
}

/* App shell */
.stApp {
    background: var(--bg);
    color: var(--text);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
    background: #080B10;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] > div { padding-top: 1.5rem; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

body, .stMarkdown, p, span, div { font-family: 'Inter', sans-serif; }

/* Brand mark */
.vl-brand {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 4px;
}
.vl-brand-mark {
    width: 30px; height: 30px; border-radius: 7px;
    background: linear-gradient(135deg, var(--brand), #14544F);
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
}
.vl-brand-name {
    font-family: 'Archivo', sans-serif; font-weight: 800;
    font-size: 19px; letter-spacing: 0.04em; color: var(--text);
}
.vl-brand-sub {
    font-family: 'Inter', sans-serif; font-size: 11px;
    color: var(--text-muted); letter-spacing: 0.08em;
    text-transform: uppercase; margin-left: 40px; margin-top: -6px;
}

/* Sidebar status panel */
.vl-status-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 12px; background: var(--surface);
    border: 1px solid var(--border); border-radius: 8px; margin-bottom: 8px;
}
.vl-status-label {
    font-family: 'Inter', sans-serif; font-size: 12.5px; color: var(--text);
}
.vl-status-pill {
    font-family: 'JetBrains Mono', monospace; font-size: 10.5px;
    font-weight: 600; padding: 3px 8px; border-radius: 20px;
    letter-spacing: 0.03em;
}
.vl-pill-on { background: rgba(62, 207, 142, 0.14); color: var(--risk-clean); }
.vl-pill-off { background: rgba(124, 134, 149, 0.14); color: var(--text-muted); }
.vl-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; margin-right: 6px; }

.vl-sidebar-note {
    font-family: 'Inter', sans-serif; font-size: 12px; line-height: 1.6;
    color: var(--text-muted); padding: 12px; background: var(--surface-2);
    border-radius: 8px; margin-top: 14px; border: 1px solid var(--border);
}
.vl-sidebar-note b { color: var(--text); }

/* Hero */
.vl-hero-eyebrow {
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: var(--brand); letter-spacing: 0.15em; text-transform: uppercase;
    display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
}
.vl-scan-bar {
    width: 34px; height: 2px; background: var(--brand);
    position: relative; overflow: hidden; border-radius: 2px;
}
.vl-scan-bar::after {
    content: ''; position: absolute; top: 0; left: -40%; width: 40%; height: 100%;
    background: linear-gradient(90deg, transparent, #fff, transparent);
    animation: vl-scan 1.6s ease-in-out infinite;
}
@keyframes vl-scan { 0% { left: -40%; } 100% { left: 100%; } }

.vl-hero-title {
    font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 34px;
    letter-spacing: -0.01em; color: var(--text); margin: 0 0 8px 0;
}
.vl-hero-sub {
    font-family: 'Inter', sans-serif; font-size: 14.5px; color: var(--text-muted);
    margin-bottom: 28px; max-width: 640px; line-height: 1.5;
}

/* File uploader restyle */
[data-testid="stFileUploaderDropzone"] {
    background: var(--surface) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--brand) !important; }

/* Section headers */
.vl-section-head {
    display: flex; align-items: baseline; gap: 10px; margin: 34px 0 16px 0;
}
.vl-section-num {
    font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--brand);
}
.vl-section-title {
    font-family: 'Archivo', sans-serif; font-weight: 700; font-size: 15px;
    letter-spacing: 0.06em; text-transform: uppercase; color: var(--text);
}
.vl-section-line {
    flex: 1; height: 1px; background: var(--border);
}

/* Metric cards */
.vl-card-row { display: flex; gap: 14px; margin-bottom: 6px; }
.vl-card {
    flex: 1; background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 18px 20px; position: relative; overflow: hidden;
}
.vl-card-label {
    font-family: 'JetBrains Mono', monospace; font-size: 10.5px;
    letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted);
    margin-bottom: 10px;
}
.vl-card-value {
    font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 30px;
    color: var(--text); display: flex; align-items: center; gap: 8px;
}
.vl-card-accent {
    position: absolute; top: 0; left: 0; width: 3px; height: 100%;
}

/* Category bars */
.vl-bar-row { margin-bottom: 13px; }
.vl-bar-top {
    display: flex; justify-content: space-between; margin-bottom: 5px;
    font-family: 'Inter', sans-serif; font-size: 12.5px; color: var(--text);
}
.vl-bar-count { font-family: 'JetBrains Mono', monospace; color: var(--text-muted); font-size: 12px; }
.vl-bar-track {
    width: 100%; height: 6px; background: var(--surface-2); border-radius: 4px; overflow: hidden;
}
.vl-bar-fill { height: 100%; border-radius: 4px; }

/* Findings / redaction chip */
.vl-chip {
    display: inline-flex; align-items: center; gap: 6px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600;
    padding: 2px 9px 2px 2px; border-radius: 4px; color: #0A0E13;
    background: #000; margin: 1px 2px;
}
.vl-chip-bar {
    background: #000; color: #fff; font-size: 9.5px; letter-spacing: 0.04em;
    padding: 3px 6px; border-radius: 3px 0 0 3px;
}
.vl-chip-tag {
    font-family: 'JetBrains Mono', monospace; font-size: 9.5px; font-weight: 700;
    letter-spacing: 0.03em;
}

/* Terminal / log block */
.vl-terminal {
    background: #05070A; border: 1px solid var(--border); border-radius: 10px;
    padding: 20px 22px; font-family: 'JetBrains Mono', monospace; font-size: 12.5px;
    color: #C7D0DB; line-height: 1.75; white-space: pre-wrap; word-break: break-word;
}
.vl-terminal .vl-t-high { color: var(--risk-high); }
.vl-terminal .vl-t-medium { color: var(--risk-medium); }
.vl-terminal .vl-t-low { color: var(--risk-low); }
.vl-terminal .vl-t-head { color: var(--brand); font-weight: 600; }

/* Risk pill for table */
.vl-risk-pill {
    font-family: 'JetBrains Mono', monospace; font-size: 10.5px; font-weight: 700;
    padding: 2px 8px; border-radius: 20px; letter-spacing: 0.03em;
}

/* Dataframe restyle */
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }

/* Buttons */
.stButton > button {
    background: var(--brand) !important; color: #05100E !important;
    border: none !important; font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; border-radius: 7px !important;
}
.stButton > button:hover { opacity: 0.88; }
.stDownloadButton > button {
    background: var(--surface) !important; color: var(--text) !important;
    border: 1px solid var(--border) !important; font-family: 'Inter', sans-serif !important;
    border-radius: 7px !important;
}

/* Text inputs */
.stTextInput input {
    background: var(--surface) !important; color: var(--text) !important;
    border: 1px solid var(--border) !important; font-family: 'Inter', sans-serif !important;
}

/* Q&A cards */
.vl-qa-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 18px; margin-bottom: 12px;
}
.vl-qa-q {
    font-family: 'Inter', sans-serif; font-weight: 600; font-size: 13.5px;
    color: var(--brand); margin-bottom: 8px;
}
.vl-qa-a {
    font-family: 'Inter', sans-serif; font-size: 13.5px; color: var(--text);
    line-height: 1.6;
}

/* Empty state */
.vl-empty {
    border: 1px dashed var(--border); border-radius: 12px; padding: 36px;
    text-align: center; color: var(--text-muted); font-family: 'Inter', sans-serif;
    font-size: 13.5px; margin-top: 20px;
}
</style>
"""


def clean(html: str) -> str:
    """
    Strip leading whitespace from every line and drop blank lines before
    handing HTML to st.markdown(). Streamlit's markdown parser runs BEFORE
    the unsafe_allow_html pass -- a line indented 4+ spaces (or a blank
    line splitting an HTML block) gets treated as a CommonMark code block
    and rendered as literal text (with a copy-button UI), even with
    unsafe_allow_html=True. Python's natural multi-line f-string
    indentation triggers this constantly. Lines are joined with a single
    space (not "") so wrapped sentence text doesn't get glued together --
    this matches how browsers collapse whitespace in rendered HTML anyway.
    """
    lines = [line.strip() for line in html.strip().splitlines()]
    lines = [line for line in lines if line]
    return " ".join(lines)


def section_head(num: str, title: str) -> str:
    return clean(f"""
    <div class="vl-section-head">
        <span class="vl-section-num">{num}</span>
        <span class="vl-section-title">{title}</span>
        <div class="vl-section-line"></div>
    </div>
    """)


def metric_cards(overall_risk: str, counts: dict) -> str:
    color = RISK_COLORS.get(overall_risk, "#7C8695")
    cards = [
        ("OVERALL RISK", overall_risk, color),
        ("HIGH RISK ITEMS", str(counts["HIGH"]), RISK_COLORS["HIGH"]),
        ("MEDIUM RISK ITEMS", str(counts["MEDIUM"]), RISK_COLORS["MEDIUM"]),
        ("LOW RISK ITEMS", str(counts["LOW"]), RISK_COLORS["LOW"]),
    ]
    html = '<div class="vl-card-row">'
    for label, value, c in cards:
        html += f"""
        <div class="vl-card">
            <div class="vl-card-accent" style="background:{c};"></div>
            <div class="vl-card-label">{label}</div>
            <div class="vl-card-value" style="color:{c};">{value}</div>
        </div>
        """
    html += "</div>"
    return clean(html)


def category_bars(by_category: dict, risk_levels: dict) -> str:
    if not by_category:
        return ""
    max_count = max(by_category.values())
    html = ""
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        risk = risk_levels.get(cat, "LOW")
        color = RISK_COLORS.get(risk, "#7C8695")
        pct = max(8, int((count / max_count) * 100))
        html += f"""
        <div class="vl-bar-row">
            <div class="vl-bar-top">
                <span>{cat}</span>
                <span class="vl-bar-count">{count}</span>
            </div>
            <div class="vl-bar-track">
                <div class="vl-bar-fill" style="width:{pct}%; background:{color};"></div>
            </div>
        </div>
        """
    return clean(html)


def risk_pill(risk: str) -> str:
    color = RISK_COLORS.get(risk, "#7C8695")
    return f'<span class="vl-risk-pill" style="background:{color}22; color:{color};">{risk}</span>'


def redaction_chip(tag: str) -> str:
    return f'<span class="vl-chip"><span class="vl-chip-bar">████</span><span class="vl-chip-tag" style="color:#29D9C7;">{tag}</span></span>'


def render_redacted_html(redacted_text: str) -> str:
    """Turn [REDACTED-XXX] tags in text into censor-bar chips for display."""
    import re
    def repl(m):
        tag = m.group(1).replace("_", " ")
        return redaction_chip(tag)
    escaped = (
        redacted_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    out = re.sub(r"\[REDACTED-([A-Z_]+)\]", repl, escaped)
    return out