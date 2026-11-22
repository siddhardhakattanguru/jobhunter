"""LLM calls: score a job against your profile, then draft application material.

Providers (set LLM_PROVIDER, or it is auto-picked from whichever key you set):
  - gemini    (default if GEMINI_API_KEY is set; has a free tier)
  - anthropic (if ANTHROPIC_API_KEY is set; paid API)

Guardrail baked into the prompts: the model may only use facts that appear in
profile.md. Anything missing becomes a [FILL] placeholder for you to complete,
so the agent never invents experience or numbers on your behalf.
"""
from __future__ import annotations

import json
import os
import re
import time

MAX_DESC_CHARS = 6000
MAX_ATTEMPTS = 6
_TRANSIENT = ("503", "429", "500", "UNAVAILABLE", "RESOURCE_EXHAUSTED",
              "overloaded", "high demand", "rate limit", "timed out", "timeout")

_client = None
_client_provider = None


def _provider() -> str:
    explicit = os.getenv("LLM_PROVIDER", "").strip().lower()
    if explicit in ("gemini", "anthropic"):
        return explicit
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    raise SystemExit(
        "No API key found. Put GEMINI_API_KEY (or ANTHROPIC_API_KEY) in your .env file."
    )


def _gemini_model() -> str:
    # Model names change; override in .env with GEMINI_MODEL if this one is retired
    # or not available on your free tier.
    return os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def _anthropic_model() -> str:
    return os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")


def _get_client(provider: str):
    global _client, _client_provider
    if _client is not None and _client_provider == provider:
        return _client
    if provider == "gemini":
        from google import genai  # pip install google-genai

        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        _client = genai.Client(api_key=key) if key else genai.Client()
    else:
        import anthropic  # pip install anthropic (optional)

        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    _client_provider = provider
    return _client


def _ask_gemini(system: str, user: str) -> str:
    client = _get_client("gemini")
    model = _gemini_model()
    # Current docs use the Interactions API; older SDKs use generate_content.
    if hasattr(client, "interactions"):
        interaction = client.interactions.create(
            model=model, system_instruction=system, input=user
        )
        return interaction.output_text or ""
    from google.genai import types

    resp = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(system_instruction=system),
    )
    return resp.text or ""


def _ask_anthropic(system: str, user: str, max_tokens: int) -> str:
    msg = _get_client("anthropic").messages.create(
        model=_anthropic_model(),
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")


def _ask_once(system: str, user: str, max_tokens: int) -> str:
    if _provider() == "gemini":
        return _ask_gemini(system, user)
    return _ask_anthropic(system, user, max_tokens)


def _ask(system: str, user: str, max_tokens: int = 1500) -> str:
    """Call the model, retrying with exponential backoff on busy/rate-limit errors."""
    delay = 5
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return _ask_once(system, user, max_tokens)
        except Exception as e:
            transient = any(t.lower() in str(e).lower() for t in _TRANSIENT)
            if not transient or attempt == MAX_ATTEMPTS:
                raise
            print(f"   [retry {attempt}/{MAX_ATTEMPTS - 1}] model busy, waiting {delay}s...", flush=True)
            time.sleep(delay)
            delay = min(delay * 2, 60)


def _job_block(job) -> str:
    return (
        f"Title: {job.title}\nCompany: {job.company}\nLocation: {job.location}\n"
        f"URL: {job.url}\n\nDescription:\n{job.description[:MAX_DESC_CHARS]}"
    )


SCORE_SYSTEM = """You are a blunt, technically grounded recruiter-matching assistant.
Score how well a job fits a candidate from 0-100 using ONLY the candidate profile
and stated preferences. Penalize: wrong seniority, wrong stack, unclear or low pay
signals, locations the candidate won't take. Respond with ONLY JSON:
{"score": <int 0-100>, "reason": "<one or two sentences>"}"""


def score_job(profile: str, preferences: str, job) -> tuple[int, str]:
    user = (
        f"<profile>\n{profile}\n</profile>\n\n<preferences>\n{preferences}\n</preferences>\n\n"
        f"<job>\n{_job_block(job)}\n</job>"
    )
    raw = _ask(SCORE_SYSTEM, user, max_tokens=300)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return 0, f"unparseable model output: {raw[:80]}"
    try:
        data = json.loads(m.group(0))
        return max(0, min(100, int(data.get("score", 0)))), str(data.get("reason", ""))
    except (ValueError, TypeError):
        return 0, f"bad JSON from model: {raw[:80]}"


TAILOR_SYSTEM = """You help an engineer apply for a job. Use ONLY facts present in
the candidate profile. NEVER invent employers, metrics, technologies, titles or
dates. If something the job wants is not in the profile, do not claim it; list it
under 'Gaps'. Where a number would strengthen a bullet but the profile lacks it,
write [FILL: what number]. Tone: direct and technically specific, no generic
enthusiasm or buzzwords. Output Markdown with exactly these sections:

## Fit summary
2-3 sentences on why this role matches (or doesn't).

## Resume bullets to emphasize
4-6 bullets rewritten to match this job's language, strongest first.

## Cover note
Max 120 words, first person, specific to this company and role.

## Gaps and questions
Requirements the profile doesn't cover, and questions the candidate should answer
before applying."""


def tailor(profile: str, job) -> str:
    user = f"<profile>\n{profile}\n</profile>\n\n<job>\n{_job_block(job)}\n</job>"
    return _ask(TAILOR_SYSTEM, user, max_tokens=1800)
