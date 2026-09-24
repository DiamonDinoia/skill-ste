"""Minimal OpenAI-compatible chat client with a JSON result cache, stdlib only.

Endpoint: LLM_BASE_URL (for example https://api.openai.com/v1), key: LLM_API_KEY, model: LLM_MODEL.
"""
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path

BASE = os.environ.get("LLM_BASE_URL")
MODEL = os.environ.get("LLM_MODEL", "moonshotai/Kimi-K3")


def chat(system: str, user: str, cache: Path, max_tokens: int = 2000) -> dict:
    """Return {"text", "in", "out"}; the cache key is the model, system and user text."""
    key = hashlib.sha256(json.dumps([MODEL, system, user]).encode()).hexdigest()[:20]
    f = cache / f"{key}.json"
    if f.exists():
        return json.loads(f.read_text())
    if not BASE:
        raise SystemExit("error: set LLM_BASE_URL to an OpenAI-compatible endpoint")
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    body = {"model": MODEL, "messages": msgs, "max_tokens": max_tokens, "temperature": 0.6}
    # Thinking off, per provider: Kimi takes a flag, GLM takes a type map, Mistral rejects the field.
    if MODEL.startswith("moonshotai/"):
        body["chat_template_kwargs"] = {"thinking": False}
    elif MODEL.startswith("zai-org/"):
        body["chat_template_kwargs"] = {"thinking": {"type": "disabled"}}
    body = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}/chat/completions", body, {
        "Authorization": f"Bearer {os.environ['LLM_API_KEY']}", "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=300))
            break
        except (OSError, ValueError) as e:
            print(f"retry {attempt + 1}: {e}")
            time.sleep(5 * 2**attempt)
    else:
        d = json.load(urllib.request.urlopen(req, timeout=300))
    r = {"text": d["choices"][0]["message"]["content"].strip(), "in": d["usage"]["prompt_tokens"],
         "out": d["usage"]["completion_tokens"]}
    cache.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")  # atomic: a concurrent reader never sees half a JSON
    tmp.write_text(json.dumps(r))
    tmp.rename(f)
    return r
