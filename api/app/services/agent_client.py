"""Vertex AI Reasoning Engine client.

Reusable SDK wrapper for invoking deployed Reasoning Engines. The API
layer uses this to proxy requests — all AI logic lives in the remote agent.

Per defensive-programming.md §6: all external calls have explicit timeouts.
Per architecture.md §4: Tier 2 communicates with Tier 3 via SDK only.
"""

import asyncio
import json
import logging
import re
import time

logger = logging.getLogger(__name__)


class AgentInvocationError(Exception):
    """Raised when a Reasoning Engine invocation fails."""


async def query_reasoning_engine(
    project_id: str,
    location: str,
    agent_id: str,
    input_text: str,
    timeout: int = 60,
) -> dict:
    """Invoke a deployed Vertex AI Reasoning Engine.

    Wraps the synchronous SDK call in asyncio.to_thread() to avoid
    blocking the FastAPI event loop.

    Args:
        project_id: GCP project ID.
        location: GCP region (e.g. us-central1).
        agent_id: Numeric Reasoning Engine resource ID.
        input_text: The prompt/data payload to send to the agent.
        timeout: Maximum seconds to wait for a response.

    Returns:
        Dict with keys: output (agent response dict), latency_ms (int).

    Raises:
        AgentInvocationError: If the agent call fails or times out.
    """
    start = time.monotonic()

    try:
        raw_response = await asyncio.wait_for(
            asyncio.to_thread(
                _invoke_sync, project_id, location, agent_id, input_text
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.error(
            "Agent invocation timed out after %dms",
            latency_ms,
            extra={"agent_id": agent_id, "latency_ms": latency_ms},
        )
        raise AgentInvocationError(
            f"Agent {agent_id} timed out after {timeout}s"
        )
    except Exception as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.error(
            "Agent invocation failed: %s",
            str(exc),
            extra={"agent_id": agent_id, "latency_ms": latency_ms},
        )
        raise AgentInvocationError(
            f"Agent {agent_id} invocation failed: {str(exc)}"
        ) from exc

    latency_ms = int((time.monotonic() - start) * 1000)
    parsed = _parse_agent_response(raw_response)

    logger.info(
        "Agent %s responded in %dms",
        agent_id,
        latency_ms,
        extra={"agent_id": agent_id, "latency_ms": latency_ms},
    )

    return {"output": parsed, "latency_ms": latency_ms}


def _invoke_sync(
    project_id: str,
    location: str,
    agent_id: str,
    input_text: str,
) -> dict:
    """Synchronous SDK call — runs in a thread via asyncio.to_thread().

    Args:
        project_id: GCP project ID.
        location: GCP region.
        agent_id: Reasoning Engine resource ID.
        input_text: Prompt payload.

    Returns:
        Raw response dict from the Reasoning Engine.
    """
    import vertexai
    from vertexai.preview import reasoning_engines

    vertexai.init(project=project_id, location=location)
    engine = reasoning_engines.ReasoningEngine(agent_id)
    return engine.query(input=input_text)


def _parse_agent_response(raw: object) -> dict:
    """Parse the Reasoning Engine response into a dict.

    Handles multiple response shapes:
    1. Direct dict with expected keys
    2. Wrapped in {"output": {...}}
    3. String response (JSON or raw text)

    Per defensive-programming.md §2: multi-strategy parsing with fallback.

    Args:
        raw: The raw response from the Reasoning Engine.

    Returns:
        Parsed dict with briefing fields.
    """
    if isinstance(raw, dict):
        if "output" in raw and isinstance(raw["output"], dict):
            return raw["output"]
        return raw

    if isinstance(raw, str):
        return _parse_json_string(raw)

    return {"briefing": str(raw)}


def _parse_json_string(text: str) -> dict:
    """Extract JSON from a string response using multiple strategies.

    Strategy order:
    1. Strip markdown code fences → direct parse
    2. Brace-matching extraction
    3. Return raw text as briefing fallback

    Args:
        text: Raw string response from the agent.

    Returns:
        Parsed dict or fallback with raw text.
    """
    cleaned = text.strip()

    # Strategy 1: Strip markdown fences
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 2: Brace-matching extraction
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    # Strategy 3: Return raw text as briefing content
    return {"briefing": text}
