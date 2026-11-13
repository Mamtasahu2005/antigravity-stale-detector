import streamlit as st
import requests
import json
import re
import urllib.parse
from datetime import datetime

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Antigravity -- Stale Answer Detector",
    page_icon="[ship]",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CUSTOM CSS
# Dark theme with Space Grotesk font and JetBrains Mono for code.
# Gradient hero title, claim cards with colored left borders per status,
# confidence bars, PyPI result cards, and hidden Streamlit branding.
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

/* ---- Background ---- */
.stApp { background: #080B14; color: #E2E8F0; }

/* ---- Hero title with gradient ---- */
.hero-title {
    font-size: 3rem; font-weight: 700;
    background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #E879F9 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1.1; margin-bottom: 0.25rem;
}
.hero-sub { color: #64748B; font-size: 1rem; margin-bottom: 2rem; }

/* ---- Claim result cards ---- */
.claim-card {
    background: #0F172A; border-radius: 12px;
    padding: 1.25rem 1.5rem; margin-bottom: 1rem;
    border-left: 4px solid #334155;
}
/* Each status gets its own accent color on the left border */
.claim-card.verified     { border-left-color: #22C55E; }
.claim-card.stale        { border-left-color: #EF4444; }
.claim-card.review       { border-left-color: #F59E0B; }
.claim-card.unverifiable { border-left-color: #6366F1; }

.claim-status { font-size:0.75rem; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; margin-bottom:0.4rem; }
.status-verified     { color: #22C55E; }
.status-stale        { color: #EF4444; }
.status-review       { color: #F59E0B; }
.status-unverifiable { color: #818CF8; }

.claim-text     { font-family:'JetBrains Mono',monospace; font-size:0.85rem; color:#CBD5E1; margin-bottom:0.5rem; }
.claim-evidence { font-size:0.8rem; color:#64748B; line-height:1.5; }
.claim-correction {
    margin-top:0.5rem; padding:0.5rem 0.75rem;
    background:rgba(239,68,68,0.08); border-radius:6px;
    font-size:0.82rem; color:#FCA5A5;
}

/* ---- Confidence bar under each claim ---- */
.conf-bar-wrap { margin-top:0.6rem; background:#1E293B; border-radius:4px; height:5px; width:100%; }
.conf-bar-fill { height:5px; border-radius:4px; }

/* ---- Freshness score box ---- */
.score-box {
    background:#0F172A; border-radius:16px; padding:1.5rem;
    text-align:center; border:1px solid #1E293B;
}
.score-number { font-size:3.5rem; font-weight:700; line-height:1; }
.score-label  { font-size:0.8rem; color:#64748B; margin-top:0.25rem; text-transform:uppercase; letter-spacing:0.08em; }

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] { background:#0A0F1E; border-right:1px solid #1E293B; }

/* ---- History items in sidebar ---- */
.history-item {
    background:#0F172A; border-radius:8px; padding:0.6rem 0.9rem;
    margin-bottom:0.5rem; border:1px solid #1E293B; font-size:0.78rem; color:#94A3B8;
}

/* ---- Text inputs ---- */
.stTextArea textarea {
    background:#0F172A !important; color:#E2E8F0 !important;
    border:1px solid #1E293B !important; border-radius:10px !important;
    font-family:'JetBrains Mono',monospace !important; font-size:0.85rem !important;
}

/* ---- Primary buttons ---- */
.stButton > button {
    background:linear-gradient(135deg, #38BDF8, #818CF8) !important;
    color:#000 !important; font-weight:600 !important; border:none !important;
    border-radius:8px !important; padding:0.6rem 2rem !important;
    font-family:'Space Grotesk',sans-serif !important; font-size:0.95rem !important;
    transition:opacity 0.2s !important;
}
.stButton > button:hover { opacity:0.85 !important; }

/* ---- Tag pill ---- */
.tag-pill {
    display:inline-block; background:#1E293B; color:#94A3B8;
    border-radius:20px; padding:2px 10px; font-size:0.72rem;
    margin-right:4px; font-family:'JetBrains Mono',monospace;
}

/* ---- PyPI package cards ---- */
.pypi-card {
    background:#0F172A; border-radius:10px; padding:0.9rem 1.25rem;
    margin-bottom:0.75rem; border-left:4px solid #334155;
    display:flex; align-items:center; justify-content:space-between;
}
.pypi-card.ok     { border-left-color: #22C55E; }
.pypi-card.old    { border-left-color: #EF4444; }
.pypi-card.unknwn { border-left-color: #6366F1; }

/* ---- Tweet button ---- */
.tweet-btn {
    display:inline-block; background:#1DA1F2; color:white !important;
    padding:0.5rem 1.2rem; border-radius:8px; font-weight:600;
    font-size:0.9rem; text-decoration:none;
}
.tweet-btn:hover { opacity:0.85; }

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab"] { color:#64748B !important; font-weight:500; }
.stTabs [aria-selected="true"] { color:#38BDF8 !important; }

hr { border-color:#1E293B !important; }
#MainMenu, footer, header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE
# We use Streamlit session state to store the last 5 analysis runs so the
# user can review them in the sidebar without re-running the analysis.
# =============================================================================
if "history" not in st.session_state:
    st.session_state.history = []


# =============================================================================
# SIDEBAR -- API KEYS + MODEL SELECTION + HISTORY
# =============================================================================
with st.sidebar:
    st.markdown("### Antigravity")
    st.markdown("<p style='color:#475569;font-size:0.8rem;'>Stale Answer Detector</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### Configuration")

    # --- Bifrost (Maxim AI) settings ---
    # Bifrost is an LLM gateway that routes calls to multiple providers
    # (Groq, OpenAI, Anthropic...) with virtual keys and auto-fallback.
    bifrost_key = st.text_input(
        "Bifrost API Key",
        type="password",
        placeholder="bf-xxxx...",
        help="Get yours FREE at getmaxim.ai -> Settings -> API Keys"
    )
    bifrost_url = st.text_input(
        "Bifrost Base URL",
        value="http://localhost:8080",
        help="Your Bifrost gateway URL. Run locally with: docker run maximhq/bifrost"
    )

    # --- Tavily settings ---
    # Tavily is a search API built specifically for LLM agents.
    # It returns clean text (not raw HTML) and a synthesized answer,
    # making it much easier to feed into an LLM than Google Search.
    tavily_key = st.text_input(
        "Tavily API Key",
        type="password",
        placeholder="tvly-xxxx...",
        help="Free 1,000 credits/month at app.tavily.com -- no credit card!"
    )

    st.markdown("---")
    st.markdown("#### Model Settings")

    # We use TWO models via Bifrost:
    # 1. Fast/cheap model for claim extraction (doesn't need to be smart)
    # 2. Accurate model for judgment (needs to reason about evidence)
    extractor_model = st.selectbox(
        "Extractor Model (fast)",
        ["llama-3.1-8b-instant", "gemini-1.5-flash", "claude-haiku-5-5"],
        index=0,
        help="Fast, cheap model -- just extracts claims, no deep reasoning needed"
    )
    judge_model = st.selectbox(
        "Judge Model (accurate)",
        ["llama-3.3-70b-versatile", "gemini-1.5-pro", "claude-sonnet-5-5"],
        index=0,
        help="Stronger model -- compares claim to live evidence and reasons about it"
    )

    # --- History section ---
    # Shows last 5 analysis runs with score and timestamp.
    # Stored in st.session_state.history (persists across reruns in the same session).
    st.markdown("---")
    st.markdown("#### Recent Checks")
    if not st.session_state.history:
        st.markdown("<p style='color:#334155;font-size:0.78rem;'>No checks yet -- run your first analysis above!</p>", unsafe_allow_html=True)
    else:
        for h in reversed(st.session_state.history[-5:]):
            color = "#22C55E" if h["score"] >= 75 else "#F59E0B" if h["score"] >= 45 else "#EF4444"
            st.markdown(f"""
            <div class="history-item">
                <span style="color:{color};font-weight:700;">{h['score']}/100</span>
                &nbsp;|&nbsp; {h['claims_count']} claims
                &nbsp;|&nbsp; <span style="color:#475569;">{h['ts']}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p style='color:#334155;font-size:0.72rem;'>Built for Geek Room Global AI Hackathon 2026 | Team Antigravity</p>", unsafe_allow_html=True)


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def call_bifrost(prompt: str, model: str, system: str = "") -> str:
    """
    Send a chat completion request through the Bifrost LLM gateway.

    Why Bifrost?
    - Single endpoint for 100+ LLM providers (Groq, OpenAI, Anthropic, etc.)
    - Virtual keys: store provider keys centrally, hand out scoped virtual keys
    - Auto-fallback: if one provider is down, Bifrost retries another
    - Rate limiting and cost tracking built in

    Returns the model's text response, or "BIFROST_ERROR: ..." on failure.
    """
    headers = {
        "Content-Type": "application/json",
        "x-bf-provider": "groq",  # Route this call to Groq's inference API
    }
    if bifrost_key:
        headers["Authorization"] = f"Bearer {bifrost_key}"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 1500,
        "temperature": 0.1,  # Low temp = consistent, structured JSON output
    }

    try:
        resp = requests.post(
            f"{bifrost_url}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"BIFROST_ERROR: {str(e)}"


def search_tavily(query: str, days: int = 400) -> dict:
    """
    Search the live web using Tavily's AI-optimized search API.

    Why Tavily instead of Google?
    - Returns clean text content (not raw HTML to parse)
    - `include_answer=True` gives a synthesized answer ready for the LLM judge
    - `days` parameter limits results to recent content only
    - Built specifically for LLM agents -- no scraping, no captchas

    Returns the full Tavily response dict, or {"error": ..., "results": []} on failure.
    """
    if not tavily_key:
        return {"error": "No Tavily API key -- configure in sidebar", "results": []}

    payload = {
        "api_key": tavily_key,
        "query": query,
        "search_depth": "basic",   # basic = 1 Tavily credit; advanced = 2 credits
        "max_results": 3,          # Top 3 results per claim
        "days": days,              # Only look at pages updated in the last N days
        "include_answer": True,    # Get a synthesized answer, not just raw snippets
    }
    try:
        resp = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e), "results": []}


def extract_claims(answer_text: str) -> list:
    """
    Use Bifrost (fast model) to extract time-sensitive claims from AI-generated text.

    Strategy:
    - We deliberately use the FAST/CHEAP model here (llama-3.1-8b-instant)
      because extraction is a simple classification task, not deep reasoning.
    - We save the expensive model for the judgment step where accuracy matters.
    - If Bifrost fails, we fall back to regex-based heuristic extraction.

    Returns a list of: [{"claim": str, "type": "version|price|api|leadership|stat|other"}]
    """
    system = """You are a claim extractor. Given an AI-generated answer,
extract ONLY time-sensitive claims -- things that could become outdated:
versions, prices, CEO/leadership names, API method names, deprecation notices,
library names, stats, regulations.
Ignore timeless facts (math, definitions, historical events before 2020).
Return ONLY a valid JSON array -- no markdown fences, no explanation.
Format: [{"claim": "...", "type": "version|price|leadership|stat|api|other"}]
Maximum 8 claims."""

    prompt = f"Extract time-sensitive claims from this text:\n\n{answer_text}\n\nReturn JSON array only."

    result = call_bifrost(prompt, extractor_model, system)

    if result.startswith("BIFROST_ERROR"):
        # Bifrost unreachable -- use heuristic fallback
        return _heuristic_extract(answer_text)

    try:
        clean = result.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except Exception:
        return _heuristic_extract(answer_text)


def _heuristic_extract(text: str) -> list:
    """
    Fallback claim extractor using regex patterns (no LLM needed).
    Catches version numbers and time-sensitive keyword sentences.
    Used when Bifrost is unreachable.
    """
    claims = []
    version_pattern = r'version\s+[\d\.]+|v[\d\.]+\s+\w+|\d+\.\d+\.\d+'
    matches = re.findall(version_pattern, text, re.IGNORECASE)
    for m in matches[:5]:
        claims.append({"claim": m.strip(), "type": "version"})

    time_keywords = ['latest', 'current', 'now', 'today', 'recently', 'new',
                     'price', 'cost', 'ceo', 'deprecated', 'removed', 'introduced']
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    for s in sentences[:4]:
        if any(w in s.lower() for w in time_keywords):
            claims.append({"claim": s, "type": "other"})

    return claims if claims else [{"claim": text[:200], "type": "other"}]


def verify_claim(claim: str, claim_type: str) -> dict:
    """
    Full 2-step verification pipeline for a single claim:

    Step 1 -- Tavily search:
      Query the live web for evidence about this claim.
      We get back: source URL, content snippet, and a synthesized answer.

    Step 2 -- Bifrost judge:
      Feed the claim + live evidence to the ACCURATE/STRONG model.
      It compares them and returns: status (verified/stale/unverifiable),
      one-sentence reasoning, and a corrected fact if the claim is stale.

    Returns: {status, evidence, source_url, corrected_fact}
    """
    # --- Step 1: Get live evidence from Tavily ---
    search_result = search_tavily(f"{claim} {claim_type} 2024 2025 2026", days=400)

    tavily_evidence = ""
    source_url = ""

    if "error" not in search_result and search_result.get("results"):
        top = search_result["results"][0]
        tavily_evidence = top.get("content", "")[:500]
        source_url = top.get("url", "")
        # Tavily's synthesized answer is cleaner than raw content
        if search_result.get("answer"):
            tavily_evidence = search_result["answer"] + "\n\n" + tavily_evidence

    if not tavily_key:
        return {
            "status": "unverifiable",
            "evidence": "No Tavily API key -- configure in sidebar to enable live verification.",
            "source_url": "",
            "corrected_fact": None
        }

    if not tavily_evidence:
        return {
            "status": "unverifiable",
            "evidence": "No live web evidence found for this claim.",
            "source_url": source_url,
            "corrected_fact": None
        }

    # --- Step 2: Judge with the strong Bifrost model ---
    system = """You are a fact-checking judge. Given a claim and live web evidence,
determine if the claim is still accurate today.
Return ONLY valid JSON -- no markdown, no explanation outside the JSON:
{
  "status": "verified" | "stale" | "unverifiable",
  "reasoning": "one concise sentence explaining your verdict",
  "corrected_fact": "the accurate updated value if stale, else null"
}"""

    prompt = f"""Claim: {claim}
Claim type: {claim_type}
Live web evidence (retrieved today): {tavily_evidence}

Is this claim still accurate? Return JSON only."""

    judge_result = call_bifrost(prompt, judge_model, system)

    if judge_result.startswith("BIFROST_ERROR"):
        return {
            "status": "unverifiable",
            "evidence": tavily_evidence[:300],
            "source_url": source_url,
            "corrected_fact": None
        }

    try:
        clean = judge_result.strip().strip("```json").strip("```").strip()
        verdict = json.loads(clean)
        return {
            "status": verdict.get("status", "unverifiable"),
            "evidence": verdict.get("reasoning", tavily_evidence[:200]),
            "source_url": source_url,
            "corrected_fact": verdict.get("corrected_fact")
        }
    except Exception:
        return {
            "status": "unverifiable",
            "evidence": tavily_evidence[:300],
            "source_url": source_url,
            "corrected_fact": None
        }


def check_pypi_version(package: str, pinned_version: str) -> dict:
    """
    Code Mode: Query the public PyPI JSON API to get the latest version
    of a Python package, then compare it to the pinned version in the code.

    Why PyPI JSON API?
    - Public, no key required
    - Always up to date (official source)
    - Returns full release history, metadata, and latest stable version

    Returns: {status: "verified"|"stale"|"unknown", current, pinned, url}
    """
    try:
        resp = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=10)
        if resp.status_code == 404:
            return {"status": "unknown", "current": None, "url": f"https://pypi.org/project/{package}/"}
        resp.raise_for_status()
        data = resp.json()
        current = data["info"]["version"]
        is_old = pinned_version and pinned_version != current and _version_older(pinned_version, current)
        return {
            "status": "stale" if is_old else "verified",
            "current": current,
            "pinned": pinned_version,
            "url": f"https://pypi.org/project/{package}/"
        }
    except Exception as e:
        return {"status": "unknown", "current": None, "url": f"https://pypi.org/project/{package}/", "error": str(e)}


def _version_older(v1: str, v2: str) -> bool:
    """
    Compare two version strings. Returns True if v1 is strictly older than v2.
    Uses tuple comparison on numeric parts only (ignores pre-release suffixes).
    """
    try:
        def parse(v):
            return tuple(int(x) for x in re.sub(r'[^0-9.]', '', v).split('.') if x)
        return parse(v1) < parse(v2)
    except Exception:
        return v1 != v2


def extract_imports(code: str) -> list:
    """
    Parse Python code or requirements.txt to find package names and version pins.

    Handles:
    - requirements.txt style: numpy==1.24.0, pandas>=1.5, torch~=2.0
    - import statements: import numpy, from pandas import DataFrame
    - Skips Python stdlib modules (os, sys, json, re, etc.)

    Returns: [{"package": str, "pinned_version": str|None}, ...]
    """
    results = []
    seen = set()

    # Pattern 1: package==version or package>=version (requirements.txt style)
    req_pattern = r'([a-zA-Z][a-zA-Z0-9_\-\.]+)\s*(?:==|>=|<=|~=|!=)\s*([\d\.]+)'
    for match in re.finditer(req_pattern, code):
        pkg = match.group(1).lower().strip()
        ver = match.group(2).strip()
        if pkg not in seen:
            results.append({"package": pkg, "pinned_version": ver})
            seen.add(pkg)

    # Pattern 2: import statements (bare, without version)
    import_pattern = r'^(?:import|from)\s+([a-zA-Z][a-zA-Z0-9_]*)'
    # Python standard library modules to skip
    stdlib = {
        'os', 'sys', 'json', 're', 'math', 'datetime', 'time', 'random',
        'collections', 'itertools', 'functools', 'pathlib', 'typing', 'abc',
        'io', 'copy', 'enum', 'warnings', 'logging', 'threading', 'hashlib',
        'base64', 'urllib', 'http', 'email', 'html', 'xml', 'csv', 'sqlite3',
        'pickle', 'struct', 'socket', 'ssl', 'argparse', 'multiprocessing',
        'subprocess', 'shutil', 'glob', 'builtins', 'string', 'textwrap'
    }
    for match in re.finditer(import_pattern, code, re.MULTILINE):
        pkg = match.group(1).lower().strip()
        if pkg not in seen and pkg not in stdlib:
            results.append({"package": pkg, "pinned_version": None})
            seen.add(pkg)

    return results[:12]  # Cap at 12 to avoid hammering PyPI


def compute_freshness_score(results: list) -> int:
    """
    Compute a 0-100 Freshness Score for an overall answer or codebase.

    Scoring rationale:
    - verified     = 100 pts  (fully confirmed by live evidence)
    - review       = 50  pts  (partial/conflicting evidence)
    - unverifiable = 60  pts  (no evidence, but not proven wrong either)
    - stale        = 0   pts  (confirmed outdated)
    Score = average of all claim weights
    """
    if not results:
        return 0
    weights = {"verified": 100, "stale": 0, "review": 50, "unverifiable": 60}
    total = sum(weights.get(r.get("status", "unverifiable"), 50) for r in results)
    return round(total / len(results))


def score_color(score: int) -> str:
    """Return a hex color based on freshness score threshold."""
    if score >= 75: return "#22C55E"  # Green: trustworthy
    if score >= 45: return "#F59E0B"  # Amber: needs review
    return "#EF4444"                  # Red: stale / do not trust


def score_label(score: int) -> str:
    if score >= 75: return "Fresh [check]"
    if score >= 45: return "Needs Review [warning]"
    return "Stale [cross]"


def confidence_bar_html(status: str) -> str:
    """
    Render a small inline HTML progress bar under each claim card.
    Shows visually how confident we are in the verdict.
    verified=95%, review=55%, unverifiable=40%, stale=10%
    """
    config = {
        "verified":     {"pct": 95, "color": "#22C55E"},
        "stale":        {"pct": 10, "color": "#EF4444"},
        "review":       {"pct": 55, "color": "#F59E0B"},
        "unverifiable": {"pct": 40, "color": "#6366F1"},
    }
    c = config.get(status, {"pct": 40, "color": "#6366F1"})
    return f"""
    <div class="conf-bar-wrap">
        <div class="conf-bar-fill" style="width:{c['pct']}%;background:{c['color']};"></div>
    </div>
    <div style="font-size:0.68rem;color:#334155;margin-top:2px;">Confidence: {c['pct']}%</div>
    """


# Status display mappings
STATUS_ICONS  = {"verified": "[check]", "stale": "[cross]", "review": "[warning]", "unverifiable": "[crystal ball]"}
STATUS_CLASS  = {"verified": "verified", "stale": "stale", "review": "review", "unverifiable": "unverifiable"}
# Real emoji for display
STATUS_EMOJI  = {"verified": "✅", "stale": "❌", "review": "⚠️", "unverifiable": "🔮"}


# =============================================================================
# EXAMPLE CONTENT
# A realistic "stale AI answer" containing multiple outdated claims.
# Used for the Quick Demo button so judges can see the app in action instantly.
# =============================================================================
DEMO_TEXT = (
    "GPT-4 Turbo is currently the most capable AI model, priced at $0.01 per 1K input tokens. "
    "React 17 introduced concurrent rendering and is the latest stable version. "
    "Install with: npm install react@17. "
    "The CEO of OpenAI is Sam Altman. "
    "Python 3.10 is the latest stable release of Python. "
    "LangChain 0.0.150 is the version you should use -- it supports the legacy chain syntax. "
    "Use openai.ChatCompletion.create() to call GPT-4 from Python."
)

DEMO_CODE = (
    "import streamlit==1.20.0\n"
    "import langchain==0.0.150\n"
    "import openai==0.28.0\n"
    "import numpy==1.23.0\n"
    "import pandas==1.5.0\n"
    "import requests==2.28.0\n"
    "import torch==1.13.0\n"
    "from fastapi import FastAPI\n"
    "import transformers\n"
)

TEXT_EXAMPLES = {
    "Quick Demo (stale AI answer)": DEMO_TEXT,
    "React version claim": (
        "React 18.2 is the latest stable version, introducing concurrent rendering. "
        "Install with npm install react@18.2.0. "
        "The new root API replaces ReactDOM.render()."
    ),
    "Python library versions": (
        "LangChain 0.1.0 was recently released with breaking changes. "
        "Use langchain>=0.1.0 in requirements.txt. "
        "The new LCEL syntax replaces legacy chains."
    ),
    "AI Model comparison": (
        "GPT-4 Turbo is the most capable model, supporting 128K context. "
        "Claude 2 by Anthropic is priced at $8 per million tokens."
    ),
}

CODE_EXAMPLES = {
    "Stale Python libraries": DEMO_CODE,
    "Modern ML stack": (
        "import torch==2.1.0\n"
        "import transformers==4.35.0\n"
        "import datasets==2.14.0\n"
        "import accelerate==0.24.0\n"
    ),
}


# =============================================================================
# MAIN UI -- HEADER
# =============================================================================
st.markdown('<div class="hero-title">🛸 Antigravity</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Detect stale facts in AI-generated answers — powered by Bifrost + Tavily</div>',
    unsafe_allow_html=True
)


# =============================================================================
# TABS
# Tab 1: Text Mode -- fact-check any AI-generated text
# Tab 2: Code Mode -- check Python library versions against PyPI
# =============================================================================
tab_text, tab_code = st.tabs([
    "📝 Text Mode — Fact-Check AI Answers",
    "💻 Code Mode — Check Library Versions"
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 -- TEXT MODE
# ─────────────────────────────────────────────────────────────────────────────
with tab_text:
    st.markdown("#### Paste any AI-generated answer below and check if it is still accurate.")

    col_ex, col_demo = st.columns([3, 1])
    with col_ex:
        example_pick = st.selectbox(
            "Load an example", ["— choose —"] + list(TEXT_EXAMPLES.keys()), key="text_ex"
        )
    with col_demo:
        st.markdown("<br>", unsafe_allow_html=True)
        quick_demo = st.button(
            "⚡ Quick Demo",
            key="qdemo",
            help="Pre-fills a stale AI answer and runs the full analysis"
        )

    # Pre-fill the text area
    default_val = ""
    if quick_demo:
        default_val = DEMO_TEXT
    elif example_pick != "— choose —":
        default_val = TEXT_EXAMPLES[example_pick]

    answer_input = st.text_area(
        "AI Answer",
        value=default_val,
        height=160,
        placeholder=(
            "Paste any AI-generated answer here...\n"
            "Library docs, pricing info, API usage, tech comparisons, leadership claims"
        ),
        label_visibility="collapsed",
        key="answer_input"
    )

    run_col, _ = st.columns([1, 4])
    with run_col:
        run_btn = st.button("🔍 Analyze Freshness", use_container_width=True, key="run_text")

    st.markdown("---")

    # --- Run analysis ---
    should_run = run_btn or quick_demo

    if should_run and answer_input.strip():
        results = []

        with st.spinner("Step 1/3 — Extracting time-sensitive claims via Bifrost (fast model)..."):
            claims = extract_claims(answer_input)

        if not claims:
            st.warning("No time-sensitive claims detected. Try a more specific AI answer.")
            st.stop()

        st.markdown(f"**Found {len(claims)} time-sensitive claim(s) — running Tavily + Bifrost verification...**")
        progress_bar = st.progress(0)

        for i, claim_obj in enumerate(claims):
            claim_text = claim_obj.get("claim", "")
            claim_type = claim_obj.get("type", "other")
            status_msg = f"Step 2+3/{len(claims)+2} — Checking: *{claim_text[:55]}...*"

            with st.spinner(status_msg):
                verdict = verify_claim(claim_text, claim_type)

            results.append({"claim": claim_text, "type": claim_type, **verdict})
            progress_bar.progress((i + 1) / len(claims))

        # --- Compute overall score ---
        score = compute_freshness_score(results)
        color = score_color(score)
        label = score_label(score)

        verified_n   = sum(1 for r in results if r["status"] == "verified")
        stale_n      = sum(1 for r in results if r["status"] == "stale")
        unverif_n    = sum(1 for r in results if r["status"] == "unverifiable")

        # Save to session history (shown in sidebar)
        st.session_state.history.append({
            "ts": datetime.utcnow().strftime("%H:%M UTC"),
            "score": score,
            "label": label,
            "claims_count": len(results),
        })

        # --- Summary metrics ---
        st.markdown("### 📊 Freshness Report")
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f"""
            <div class="score-box">
                <div class="score-number" style="color:{color}">{score}</div>
                <div class="score-label">{label}</div>
            </div>""", unsafe_allow_html=True)
        with m2: st.metric("Claims Found", len(results))
        with m3: st.metric("✅ Verified", verified_n)
        with m4: st.metric("❌ Stale", stale_n)
        with m5: st.metric("🔮 Unverifiable", unverif_n)

        st.markdown("---")
        st.markdown("### 🧾 Claim-by-Claim Breakdown")

        # --- Render each claim card ---
        for r in results:
            icon       = STATUS_EMOJI.get(r["status"], "?")
            css_class  = STATUS_CLASS.get(r["status"], "")
            status_css = f"status-{css_class}"

            correction_html = ""
            if r.get("corrected_fact"):
                correction_html = f'<div class="claim-correction">💡 Correction: {r["corrected_fact"]}</div>'

            source_html = ""
            if r.get("source_url"):
                url_short = r["source_url"][:70]
                source_html = f'<br><a href="{r["source_url"]}" target="_blank" style="color:#38BDF8;font-size:0.78rem;">🔗 {url_short}...</a>'

            type_pill = f'<span class="tag-pill">{r["type"]}</span>'
            conf_bar  = confidence_bar_html(r["status"])

            st.markdown(f"""
            <div class="claim-card {css_class}">
                <div class="claim-status {status_css}">{icon} {r["status"].upper()}</div>
                <div class="claim-text">{r["claim"]}</div>
                {type_pill}
                <div class="claim-evidence">{r["evidence"]}{source_html}</div>
                {conf_bar}
                {correction_html}
            </div>
            """, unsafe_allow_html=True)

        # --- Export and Share ---
        st.markdown("---")
        exp_col, tweet_col = st.columns([1, 2])

        export_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "freshness_score": score,
            "summary": label,
            "powered_by": "Bifrost (Maxim AI) + Tavily",
            "claims": results
        }
        with exp_col:
            st.download_button(
                "⬇️ Export Report (JSON)",
                data=json.dumps(export_data, indent=2),
                file_name=f"antigravity_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

        with tweet_col:
            # Build a tweet that promotes the project and hackathon
            stale_desc = f"{stale_n} stale claims found" if stale_n else "all claims verified"
            tweet_text = (
                f"Just fact-checked an AI answer with Antigravity -- "
                f"Freshness Score: {score}/100 | {stale_desc} | "
                f"Powered by @maximhq Bifrost + @tavily "
                f"#GeekRoomHackathon #AIHackathon2026"
            )
            tweet_url = "https://x.com/intent/tweet?text=" + urllib.parse.quote(tweet_text)
            st.markdown(
                f'<a class="tweet-btn" href="{tweet_url}" target="_blank">🐦 Share on X</a>',
                unsafe_allow_html=True
            )

    elif should_run:
        st.warning("Please paste an AI-generated answer first, or click Quick Demo.")

    else:
        # Empty state
        st.markdown("""
        <div style='text-align:center;padding:3rem 2rem;color:#334155;'>
            <div style='font-size:3rem;margin-bottom:1rem;'>🛸</div>
            <div style='font-size:1.1rem;font-weight:600;color:#475569;'>
                Paste an AI answer above and hit Analyze
            </div>
            <div style='font-size:0.85rem;margin-top:0.5rem;'>
                Antigravity extracts time-sensitive claims and verifies each one<br>
                against the live web using Bifrost (LLM routing) + Tavily (live search)
            </div>
            <div style='margin-top:1rem;font-size:0.8rem;color:#334155;'>
                No keys? Hit <strong style="color:#818CF8;">Quick Demo</strong> to see it in action instantly
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 -- CODE MODE
# ─────────────────────────────────────────────────────────────────────────────
with tab_code:
    st.markdown("#### Paste Python code or a requirements.txt — Antigravity checks every library version against PyPI live.")
    st.markdown(
        "<p style='color:#64748B;font-size:0.85rem;'>"
        "No API keys needed for Code Mode — it queries the public PyPI JSON API directly (free, no limits)."
        "</p>",
        unsafe_allow_html=True
    )

    code_col_ex, _ = st.columns([3, 1])
    with code_col_ex:
        code_example = st.selectbox(
            "Load example", ["— choose —"] + list(CODE_EXAMPLES.keys()), key="code_ex"
        )

    code_default = CODE_EXAMPLES.get(code_example, "") if code_example != "— choose —" else ""

    code_input = st.text_area(
        "Code snippet",
        value=code_default,
        height=200,
        placeholder=(
            "Paste Python code or requirements.txt here...\n\n"
            "Examples:\n"
            "import langchain==0.0.150\n"
            "numpy>=1.23.0\n"
            "from openai import OpenAI\n"
        ),
        label_visibility="collapsed",
        key="code_input"
    )

    code_run_col, _ = st.columns([1, 4])
    with code_run_col:
        code_run_btn = st.button("🔍 Check Library Versions", use_container_width=True, key="run_code")

    st.markdown("---")

    if code_run_btn and code_input.strip():
        with st.spinner("Parsing imports..."):
            packages = extract_imports(code_input)

        if not packages:
            st.warning("No importable Python packages found. Try pasting a requirements.txt or Python file.")
            st.stop()

        st.markdown(f"**Found {len(packages)} package(s) — checking against PyPI live...**")
        code_progress = st.progress(0)
        code_results = []

        for i, pkg_obj in enumerate(packages):
            with st.spinner(f"Querying PyPI for: {pkg_obj['package']}..."):
                result = check_pypi_version(pkg_obj["package"], pkg_obj.get("pinned_version"))
            result["package"]        = pkg_obj["package"]
            result["pinned_version"] = pkg_obj.get("pinned_version")
            code_results.append(result)
            code_progress.progress((i + 1) / len(packages))

        # --- Code score ---
        ok_n      = sum(1 for r in code_results if r["status"] == "verified")
        stale_n_c = sum(1 for r in code_results if r["status"] == "stale")
        unknwn_n  = sum(1 for r in code_results if r["status"] == "unknown")
        code_score = round((ok_n / len(code_results)) * 100) if code_results else 0
        code_color = score_color(code_score)
        code_lbl   = score_label(code_score)

        st.markdown("### 📊 Library Freshness Report")
        cm1, cm2, cm3, cm4 = st.columns(4)
        with cm1:
            st.markdown(f"""
            <div class="score-box">
                <div class="score-number" style="color:{code_color}">{code_score}</div>
                <div class="score-label">{code_lbl}</div>
            </div>""", unsafe_allow_html=True)
        with cm2: st.metric("Packages Found", len(code_results))
        with cm3: st.metric("✅ Up to Date", ok_n)
        with cm4: st.metric("❌ Outdated", stale_n_c)

        st.markdown("---")
        st.markdown("### 📦 Package-by-Package Results")

        for r in code_results:
            status  = r["status"]
            css     = "ok" if status == "verified" else "old" if status == "stale" else "unknwn"
            icon    = "✅" if status == "verified" else "❌" if status == "stale" else "🔮"
            pinned  = r.get("pinned_version") or "not pinned"
            current = r.get("current") or "unknown"
            pkg     = r["package"]
            url     = r.get("url", f"https://pypi.org/project/{pkg}/")

            update_note = ""
            if status == "stale" and r.get("current"):
                update_note = f' &nbsp; <span style="color:#22C55E;font-weight:600;">&#8594; Update to {r["current"]}</span>'

            st.markdown(f"""
            <div class="pypi-card {css}">
                <div>
                    <span style="font-weight:700;color:#E2E8F0;font-family:'JetBrains Mono',monospace;">{pkg}</span>
                    &nbsp;&nbsp;
                    <span class="tag-pill">pinned: {pinned}</span>
                    <span class="tag-pill">latest: {current}</span>
                    {update_note}
                </div>
                <div>
                    {icon}&nbsp;
                    <a href="{url}" target="_blank" style="color:#38BDF8;font-size:0.78rem;">PyPI ↗</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- Export ---
        st.markdown("---")
        code_export = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "library_freshness_score": code_score,
            "total_packages": len(code_results),
            "outdated": stale_n_c,
            "up_to_date": ok_n,
            "unknown": unknwn_n,
            "packages": code_results
        }
        st.download_button(
            "⬇️ Export Code Report (JSON)",
            data=json.dumps(code_export, indent=2),
            file_name=f"antigravity_code_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

    elif code_run_btn:
        st.warning("Please paste some Python code or a requirements.txt first.")

    else:
        st.markdown("""
        <div style='text-align:center;padding:3rem 2rem;color:#334155;'>
            <div style='font-size:3rem;margin-bottom:1rem;'>💻</div>
            <div style='font-size:1.1rem;font-weight:600;color:#475569;'>Paste code or requirements.txt above</div>
            <div style='font-size:0.85rem;margin-top:0.5rem;'>
                Antigravity extracts every import and version pin,<br>
                then checks each one against the live PyPI registry
            </div>
        </div>
        """, unsafe_allow_html=True)
