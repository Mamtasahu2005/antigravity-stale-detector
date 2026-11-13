# 🛸 Antigravity — Stale Answer Detector

> Built for **Geek Room Global AI Hackathon 2026** | PS 04 (Bifrost) + PS 06 (Tavily)

**Antigravity** catches outdated, hallucinated, or time-sensitive facts in AI-generated answers — in real time, with cited sources. Because AI answers that _look_ confident can be dangerously wrong.

🎬 **[Watch Demo Video](https://youtube.com/YOUR_LINK_HERE)**  
🚀 **[Live App](https://your-app.streamlit.app)**  
📦 **[GitHub](https://github.com/Mamtasahu2005/antigravity-stale-detector)**

---

## 🔥 The Problem

Every day, developers ask AI and get confidently wrong answers:

| Developer asks... | AI says... | Reality |
|-------------------|------------|---------|
| "Latest React version?" | React 17 | React 18+ |
| "GPT-4 Turbo pricing?" | \$0.01/1K tokens | Pricing has changed |
| "How to use OpenAI API?" | `openai.ChatCompletion.create()` | Deprecated — use `client.chat.completions.create()` |
| "Latest Python?" | Python 3.10 | Python 3.12+ |

AI models are trained on old data. They answer with **confidence but zero freshness guarantee.**

Antigravity is the solution.

---

## ✨ What It Does

1. **Extract** — Bifrost routes to a fast LLM (llama-3.1-8b) that pulls _only_ time-sensitive claims
2. **Search** — Tavily searches the live web for real evidence per claim with source URLs
3. **Judge** — A stronger LLM (llama-3.3-70b via Bifrost) compares claim to evidence
4. **Score** — A 0–100 Freshness Score tells you how much to trust the answer
5. **Code Mode** — Paste Python code; checks every library version against PyPI live

---

## 🏗️ Architecture

```
User Input (AI Answer or Code Snippet)
           │
           ▼
  ┌─────────────────────┐
  │   Bifrost Gateway   │◄── Provider: Groq | Fallback: auto
  │  Claim Extractor    │    Model: llama-3.1-8b-instant (fast)
  └─────────────────────┘
           │
           ▼  [list of time-sensitive claims]
  ┌─────────────────────┐
  │   Tavily Search     │◄── Live web, max_results=3, days=400
  │   (Per claim)       │    Returns: URL + snippet + synthesized answer
  └─────────────────────┘
           │
           ▼  [live evidence]
  ┌─────────────────────┐
  │   Bifrost Gateway   │◄── Provider: Groq | Fallback: auto
  │   Judge LLM         │    Model: llama-3.3-70b-versatile (accurate)
  └─────────────────────┘
           │
           ▼
  Verdict: verified | stale | unverifiable | needs review
  Freshness Score: 0–100  |  Corrections: auto-generated for stale claims
```

---

## 🏆 Sponsor Track Coverage

| Track | Sponsor | Integration |
|-------|---------|-------------|
| **PS 04** | Bifrost (Maxim AI) | Dual LLM routing — extractor + judge models with auto-fallback |
| **PS 06** | Tavily | Real-time web search per claim with cited source URLs |

---

## ⚡ Quick Start

```bash
# 1. Clone
git clone https://github.com/Mamtasahu2005/antigravity-stale-detector
cd antigravity-stale-detector

# 2. Install
pip install -r requirements.txt

# 3. Run
streamlit run app.py
# → Open http://localhost:8501
```

**Configure in the sidebar:**

| Field | Where to get it |
|-------|----------------|
| Bifrost API Key | [getmaxim.ai](https://www.getmaxim.ai) → Settings → API Keys |
| Bifrost Base URL | `http://localhost:8080` (self-hosted) or your gateway URL |
| Tavily API Key | [app.tavily.com](https://app.tavily.com) — free, no credit card |

---

## 📊 Verdict Legend

| Status | Meaning |
|--------|---------|
| ✅ Verified | Confirmed accurate by live web sources |
| ❌ Stale | Outdated — corrected fact is provided |
| ⚠️ Needs Review | Partial or conflicting evidence |
| 🔮 Unverifiable | No live evidence found — treat with caution |

---

## 🛠️ Tech Stack

| Technology | Role |
|-----------|------|
| **Bifrost (Maxim AI)** | LLM gateway — dual model routing (fast extractor + accurate judge) with auto-fallback |
| **Tavily** | Live web search — real, cited evidence per claim |
| **Streamlit** | Frontend UI — dark mode, animated cards, progress bars |
| **Python** | Backend pipeline — claim extraction, verification, scoring |
| **PyPI JSON API** | Library version checks in Code Mode |

---

## 📁 Project Structure

```
antigravity/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── README.md           # This file
```

---

## 👩‍💻 Team

Built by **Mamta Sahu** ([@Mamtasahu2005](https://github.com/Mamtasahu2005))  
B.Tech CSE (AI & Data Science)

---

*Geek Room Global AI Hackathon 2026 · HackCulture · Team Antigravity 🛸*
