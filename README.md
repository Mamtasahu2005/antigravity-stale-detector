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

1. **Extract** — Bifrost routes to a fast LLM (`groq/llama-3.1-8b-instant`) that pulls _only_ time-sensitive claims
2. **Search** — Tavily searches the live web for real evidence per claim with source URLs
3. **Judge** — A stronger LLM (`groq/llama-3.3-70b-versatile` via Bifrost) compares claim to evidence
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
  │  Claim Extractor    │    Model: groq/llama-3.1-8b-instant (fast)
  └─────────────────────┘
           │
           ▼  [list of time-sensitive claims]
  ┌─────────────────────┐
  │   Tavily Search     │◄── Live web, max_results=3, time_range=year
  │   (Per claim)       │    Returns: URL + snippet + synthesized answer
  └─────────────────────┘
           │
           ▼  [live evidence]
  ┌─────────────────────┐
  │   Bifrost Gateway   │◄── Provider: Groq | Fallback: auto
  │   Judge LLM         │    Model: groq/llama-3.3-70b-versatile (accurate)
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

# 3. Start Bifrost locally (free Groq key from console.groq.com/keys)
docker run -p 8080:8080 -e GROQ_API_KEY=gsk_your_key maximhq/bifrost

# 4. Run the app
streamlit run app.py
# → Open http://localhost:8501
```

**Configure in the sidebar:**

| Field | Where to get it |
|-------|----------------|
| Bifrost Base URL | `http://localhost:8080` locally, or your Render URL |
| Bifrost API Key | Optional — only if `enforce_auth_on_inference` is enabled (`sk-bf-...`) |
| Tavily API Key | [app.tavily.com](https://app.tavily.com) — free, no credit card |
| Groq API key | [console.groq.com/keys](https://console.groq.com/keys) — free, used by Bifrost |

> Bifrost is self-hosted (there is no vendor SaaS gateway), so a cloud deployment
> needs a public gateway URL. `render.yaml` in this repo deploys one in ~5 minutes.

---

## ☁️ Deploy (free tier)

**1. Deploy Bifrost to Render**

1. Push this repo to GitHub (already done).
2. Render Dashboard → **New → Blueprint** → select this repo → **Apply**.
3. When prompted, paste your `GROQ_API_KEY`.
4. Copy the service URL, e.g. `https://antigravity-bifrost.onrender.com`.
   Verify it: `curl https://antigravity-bifrost.onrender.com/health`

> Render's free tier sleeps after ~15 minutes idle. The first request can take
> 30–60 seconds (the app's Bifrost timeout is 60s and it falls back to regex
> extraction if the gateway is still cold).

**2. Deploy the UI to Streamlit Cloud**

1. [share.streamlit.io](https://share.streamlit.io) → **New app** → pick this repo.
2. Main file: `app.py` · Branch: `main`.
3. **Advanced settings → Python 3.12**.
4. **Secrets** — paste (top-level keys, no `[secrets]` section):

```toml
BIFROST_URL = "https://antigravity-bifrost.onrender.com"
BIFROST_KEY = ""
TAVILY_KEY  = "tvly-your-key"
```

`app.py` reads Streamlit secrets first, then environment variables, so the same
code works locally, on Streamlit Cloud, and in Docker.

**3. Verify both keys before recording the demo**

```powershell
$env:BIFROST_URL = "https://antigravity-bifrost.onrender.com"
$env:BIFROST_KEY = ""                 # only if auth is enabled
$env:TAVILY_KEY  = "tvly-your-key"
python check_keys.py
```

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
├── app.py                       # Main Streamlit application
├── requirements.txt             # Python dependencies
├── render.yaml                  # One-click Bifrost gateway deploy (Render)
├── bifrost/
│   ├── Dockerfile               # Bifrost image + file-only config
│   └── config.json              # Groq provider, no database needed
├── .streamlit/
│   ├── config.toml              # Dark theme
│   └── secrets.toml.example     # Cloud secrets template
├── .env.example                 # Local environment template
└── README.md
```

---

## 👩‍💻 Team

Built by **Mamta Sahu** ([@Mamtasahu2005](https://github.com/Mamtasahu2005))  
B.Tech CSE (AI & Data Science)

---

*Geek Room Global AI Hackathon 2026 · HackCulture · Team Antigravity 🛸*
