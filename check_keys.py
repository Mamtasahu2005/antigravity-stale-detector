"""
Smoke-test the Bifrost gateway and Tavily key before a demo.

Usage (PowerShell):
    $env:BIFROST_URL = "https://your-gateway.onrender.com"
    $env:BIFROST_KEY = "sk-bf-..."      # optional if auth is disabled
    $env:TAVILY_KEY  = "tvly-..."
    python check_keys.py

Exits 0 only if every configured check passes.
"""
import os
import sys

import requests


def check_bifrost() -> bool:
    url = os.getenv("BIFROST_URL", "http://localhost:8080").rstrip("/")
    key = os.getenv("BIFROST_KEY", "")

    print(f"[Bifrost] {url}")
    headers = {"Content-Type": "application/json"}
    if key.startswith("sk-bf-"):
        headers["x-bf-vk"] = key
    elif key:
        headers["Authorization"] = f"Bearer {key}"

    payload = {
        "model": "groq/llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
        "max_tokens": 10,
        "temperature": 0,
    }
    try:
        resp = requests.post(f"{url}/v1/chat/completions", headers=headers, json=payload, timeout=90)
        if resp.status_code != 200:
            print(f"  FAILED [{resp.status_code}] {resp.text[:300]}")
            return False
        reply = resp.json()["choices"][0]["message"]["content"].strip()
        print(f"  OK -> {reply!r}")
        return True
    except Exception as exc:
        print(f"  FAILED: {exc}")
        return False


def check_tavily() -> bool:
    key = os.getenv("TAVILY_KEY", "")
    print("[Tavily] https://api.tavily.com/search")
    if not key:
        print("  SKIPPED: TAVILY_KEY is not set")
        return False

    payload = {
        "api_key": key,
        "query": "latest stable Python version",
        "search_depth": "basic",
        "max_results": 1,
        "include_answer": True,
        "time_range": "year",
    }
    try:
        resp = requests.post("https://api.tavily.com/search", json=payload, timeout=30)
        if resp.status_code != 200:
            print(f"  FAILED [{resp.status_code}] {resp.text[:300]}")
            return False
        data = resp.json()
        answer = (data.get("answer") or data.get("results", [{}])[0].get("content", ""))[:120]
        print(f"  OK -> {answer!r}")
        return True
    except Exception as exc:
        print(f"  FAILED: {exc}")
        return False


if __name__ == "__main__":
    results = [check_bifrost(), check_tavily()]
    sys.exit(0 if all(results) else 1)
