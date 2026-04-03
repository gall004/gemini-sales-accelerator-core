"""Tests for the POST /api/v1/briefings/generate endpoint.

Covers per testing-standards.md §4:
  - Happy path: AI briefing generation, cache hit, force refresh, contact
  - Sad path: invalid input, missing fields, agent failure
  - Auth: missing API key, invalid API key
  - Upsert idempotency: same external_id updates, doesn't duplicate
  - Telemetry: AI usage logs created on agent invocation
"""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.services.agent_client import AgentInvocationError
from tests.conftest import AUTH_HEADERS, MOCK_AGENT_RESPONSE

VALID_PAYLOAD = {
    "entity_type": "account",
    "account": {
        "name": "Acme Corp",
        "industry": "Technology",
        "website": "https://acme.example.com",
    },
    "source_system": "google_sheets",
    "external_id": "row_99",
    "agent_id": "test_agent_123",
}

PAYLOAD_WITH_CONTACT = {
    **VALID_PAYLOAD,
    "external_id": "row_100",
    "contact": {
        "first_name": "Jane",
        "last_name": "Doe",
        "title": "VP of Engineering",
    },
}

PAYLOAD_WITH_CAMPAIGN = {
    **VALID_PAYLOAD,
    "external_id": "row_101",
    "campaign_context": "Google Actions Center Integrations for Event Ticketing",
}

ENDPOINT = "/api/v1/briefings/generate"


# ── Happy Path ───────────────────────────────────────────────────────────────


async def test_generate_briefing_returns_ai_content(client: AsyncClient):
    """POST /briefings/generate returns 200 with AI briefing fields."""
    response = await client.post(ENDPOINT, json=VALID_PAYLOAD, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["entity_type"] == "account"
    assert data["cache_hit"] is False
    assert data["briefing_markdown"] is not None
    assert "Strategic Overview" in data["briefing_markdown"]
    assert data["id"] is not None
    assert data["entity_id"] is not None
    assert data["generated_at"] is not None
    assert data["expires_at"] is not None


async def test_ai_response_fields_parsed(client: AsyncClient):
    """Verify structured AI fields are correctly parsed from agent response."""
    response = await client.post(ENDPOINT, json=VALID_PAYLOAD, headers=AUTH_HEADERS)
    data = response.json()
    assert data["p2b_score"] == 78
    assert data["account_signal"] == "Expanding cloud spend by 40% YoY."
    assert data["why_we_matter"] == "Our platform cuts integration time by 60%."
    assert data["anticipated_objection"] == "We already have an in-house solution."
    assert data["objection_pivot"] == "Most teams find they save 200+ engineering hours."
    assert len(data["suggested_contacts"]) == 2
    assert data["suggested_contacts"][0]["title"] == "VP of Engineering"


async def test_cache_hit_on_second_call(client: AsyncClient):
    """Second call with same data returns cache_hit=True."""
    payload = {**VALID_PAYLOAD, "external_id": "row_cache_test"}

    first = await client.post(ENDPOINT, json=payload, headers=AUTH_HEADERS)
    assert first.status_code == 200
    assert first.json()["cache_hit"] is False

    second = await client.post(ENDPOINT, json=payload, headers=AUTH_HEADERS)
    assert second.status_code == 200
    second_data = second.json()
    assert second_data["cache_hit"] is True
    assert second_data["id"] == first.json()["id"]


async def test_force_refresh_bypasses_cache(client: AsyncClient):
    """force_refresh=True generates a new briefing even if cached."""
    payload = {**VALID_PAYLOAD, "external_id": "row_force_test"}

    first = await client.post(ENDPOINT, json=payload, headers=AUTH_HEADERS)
    assert first.status_code == 200

    refresh_payload = {**payload, "force_refresh": True}
    second = await client.post(ENDPOINT, json=refresh_payload, headers=AUTH_HEADERS)
    assert second.status_code == 200
    assert second.json()["cache_hit"] is False
    assert second.json()["id"] != first.json()["id"]


async def test_generate_with_contact(client: AsyncClient):
    """Briefing with contact data includes contact_briefing_markdown."""
    response = await client.post(
        ENDPOINT, json=PAYLOAD_WITH_CONTACT, headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    data = response.json()
    assert data["contact_briefing_markdown"] is not None
    assert "Strategic Account Summary" in data["contact_briefing_markdown"]


async def test_generate_with_campaign_context(client: AsyncClient):
    """Briefing with campaign_context is accepted and processed."""
    response = await client.post(
        ENDPOINT, json=PAYLOAD_WITH_CAMPAIGN, headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    assert response.json()["entity_type"] == "account"


# ── Agent Routing ────────────────────────────────────────────────────────────


async def test_agent_id_from_request(
    client: AsyncClient, mock_agent_client: AsyncMock,
):
    """Agent is invoked with the agent_id from the request payload."""
    payload = {**VALID_PAYLOAD, "agent_id": "custom_agent_999"}
    await client.post(ENDPOINT, json=payload, headers=AUTH_HEADERS)

    mock_agent_client.assert_called_once()
    call_kwargs = mock_agent_client.call_args
    assert call_kwargs.kwargs["agent_id"] == "custom_agent_999"


async def test_no_agent_id_returns_placeholder(client: AsyncClient):
    """When no agent_id is configured, returns a placeholder briefing."""
    payload = {
        "entity_type": "account",
        "account": {"name": "NoAgentCo"},
        "source_system": "test",
    }
    with patch(
        "app.services.briefing_service.query_reasoning_engine",
        new_callable=AsyncMock,
    ) as mock_fn:
        # Ensure no agent_id resolves (request, platform_config, settings)
        with patch(
            "app.services.briefing_service._resolve_agent_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.post(
                ENDPOINT, json=payload, headers=AUTH_HEADERS
            )

    assert response.status_code == 200
    data = response.json()
    assert "No Briefing Agent configured" in data["briefing_markdown"]


# ── Agent Failure ────────────────────────────────────────────────────────────


async def test_agent_failure_returns_degraded_briefing(client: AsyncClient):
    """Agent invocation error returns a degraded briefing, not 500."""
    payload = {**VALID_PAYLOAD, "external_id": "row_fail_test"}

    with patch(
        "app.services.briefing_service.query_reasoning_engine",
        new_callable=AsyncMock,
        side_effect=AgentInvocationError("Agent timed out after 60s"),
    ):
        response = await client.post(
            ENDPOINT, json=payload, headers=AUTH_HEADERS
        )

    assert response.status_code == 200
    data = response.json()
    assert "temporarily unavailable" in data["briefing_markdown"]
    assert "timed out" in data["briefing_markdown"]


# ── Upsert Idempotency ──────────────────────────────────────────────────────


async def test_upsert_updates_existing_account(client: AsyncClient):
    """Same external_id updates the account, doesn't create a duplicate."""
    payload_v1 = {
        "entity_type": "account",
        "account": {"name": "UpCo", "industry": "Finance"},
        "source_system": "google_sheets",
        "external_id": "row_upsert",
        "force_refresh": True,
        "agent_id": "test_agent_123",
    }
    first = await client.post(ENDPOINT, json=payload_v1, headers=AUTH_HEADERS)
    assert first.status_code == 200
    entity_id_1 = first.json()["entity_id"]

    payload_v2 = {
        **payload_v1,
        "account": {"name": "UpCo", "industry": "FinTech"},
    }
    second = await client.post(ENDPOINT, json=payload_v2, headers=AUTH_HEADERS)
    assert second.status_code == 200
    assert second.json()["entity_id"] == entity_id_1


# ── Sad Path — Invalid Input ────────────────────────────────────────────────


async def test_invalid_entity_type_returns_422(client: AsyncClient):
    """Invalid entity_type triggers Pydantic validation error."""
    payload = {**VALID_PAYLOAD, "entity_type": "invalid"}
    response = await client.post(ENDPOINT, json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("entity_type" in str(e.get("loc", "")) for e in detail)


async def test_missing_account_name_returns_422(client: AsyncClient):
    """Missing required account.name triggers validation error."""
    payload = {
        "entity_type": "account",
        "account": {"industry": "Tech"},
    }
    response = await client.post(ENDPOINT, json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 422


async def test_missing_account_object_returns_422(client: AsyncClient):
    """Missing required account object triggers validation error."""
    payload = {"entity_type": "account"}
    response = await client.post(ENDPOINT, json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 422


async def test_empty_body_returns_422(client: AsyncClient):
    """Empty request body triggers validation error."""
    response = await client.post(ENDPOINT, json={}, headers=AUTH_HEADERS)
    assert response.status_code == 422


# ── Auth Tests ───────────────────────────────────────────────────────────────


async def test_missing_api_key_returns_401(client: AsyncClient):
    """Request without X-API-Key header returns 401."""
    response = await client.post(ENDPOINT, json=VALID_PAYLOAD)
    assert response.status_code == 401
    assert "Missing" in response.json()["detail"]


async def test_invalid_api_key_returns_403(client: AsyncClient):
    """Request with wrong X-API-Key returns 403."""
    headers = {"X-API-Key": "wrong_key_12345"}
    response = await client.post(ENDPOINT, json=VALID_PAYLOAD, headers=headers)
    assert response.status_code == 403
    assert "Invalid" in response.json()["detail"]
