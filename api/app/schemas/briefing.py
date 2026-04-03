"""Pydantic schemas for the /briefings endpoints.

Strict validation ensures malformed requests from any frontend (Google Sheets,
Salesforce, custom apps) are rejected with clear 422 errors before touching
the database or Vertex AI.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ── Nested Input Models ──────────────────────────────────────────────────────


class AccountInput(BaseModel):
    """Account context passed inline from the frontend.

    The API upserts this into the `accounts` table using
    (source_system, external_id) as the natural key.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Company name (required)",
        examples=["Ford Motor Company"],
    )
    industry: str | None = Field(
        default=None,
        max_length=255,
        description="Industry vertical",
        examples=["Automotive"],
    )
    type: str | None = Field(
        default=None,
        max_length=50,
        description="Account type",
        examples=["Prospect", "Customer", "Partner"],
    )
    annual_revenue: float | None = Field(
        default=None,
        ge=0,
        description="Annual revenue in USD (no symbols)",
        examples=[176000000000],
    )
    number_of_employees: int | None = Field(
        default=None,
        ge=0,
        description="Employee count",
        examples=[177000],
    )
    website: str | None = Field(
        default=None,
        max_length=500,
        description="Company website URL",
        examples=["https://ford.com"],
    )
    phone: str | None = Field(
        default=None,
        max_length=50,
        description="Company phone number",
    )
    billing_address: str | None = Field(
        default=None,
        description="Billing address (JSON or free text)",
    )


class ContactInput(BaseModel):
    """Contact context passed inline from the frontend.

    Used to personalize the briefing (discovery questions, recommended
    opening, objection handling).
    """

    first_name: str | None = Field(
        default=None,
        max_length=255,
        description="Contact first name",
        examples=["Jim"],
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Contact last name (required)",
        examples=["Farley"],
    )
    title: str | None = Field(
        default=None,
        max_length=255,
        description="Job title",
        examples=["President & CEO"],
    )
    email: str | None = Field(
        default=None,
        max_length=255,
        description="Email address",
    )


class SuggestedContact(BaseModel):
    """A single buying committee suggestion from the AI."""

    title: str = Field(..., description="Suggested job title")
    reason: str = Field(..., description="Why this person matters to the deal")


# ── Request Models ───────────────────────────────────────────────────────────


class BriefingGenerateRequest(BaseModel):
    """POST /api/v1/briefings/generate — Request body.

    The frontend passes account and contact context inline. The API upserts
    the account/contact and either returns a cached briefing or generates
    a fresh one via Vertex AI.
    """

    entity_type: str = Field(
        ...,
        description="Type of entity to brief",
        examples=["account", "contact", "opportunity"],
    )
    account: AccountInput = Field(
        ...,
        description="Account context (always required — contacts/opps are scoped to an account)",
    )
    contact: ContactInput | None = Field(
        default=None,
        description="Contact context (required when entity_type is 'contact')",
    )
    force_refresh: bool = Field(
        default=False,
        description="If true, bypass cache and force a new Vertex AI callout",
    )
    source_system: str = Field(
        default="google_sheets",
        max_length=50,
        description="Originating system identifier",
        examples=["google_sheets", "salesforce", "api"],
    )
    external_id: str | None = Field(
        default=None,
        max_length=255,
        description="Record ID from the source system (used for upsert matching)",
        examples=["row_42", "001Dn00000ABC123"],
    )
    campaign_context: str | None = Field(
        default=None,
        max_length=2000,
        description=(
            "Campaign or product focus for the briefing. Drives dynamic AI "
            "personalization of 'Why We Matter' and objection handling. "
            "Example: 'Google Actions Center Integrations for Event Ticketing'"
        ),
        examples=[
            "Google Actions Center Integrations for Event Ticketing",
            "Cisco Contact Center Modernization with AI Agent Assist",
        ],
    )
    agent_id: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Vertex AI Reasoning Engine ID to invoke. If omitted, the API "
            "resolves from platform_config (key: default_briefing_agent_id) "
            "or the BRIEFING_AGENT_ENGINE_ID environment variable."
        ),
        examples=["5864266157464223744"],
    )

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        allowed = {"account", "contact", "opportunity"}
        if v.lower() not in allowed:
            raise ValueError(
                f"entity_type must be one of {allowed}, got '{v}'"
            )
        return v.lower()


# ── Response Models ──────────────────────────────────────────────────────────


class BriefingResponse(BaseModel):
    """POST /api/v1/briefings/generate — Response body.

    Matches the output_schema defined in the Briefing Agent's system prompt
    with additional API-layer metadata (cache status, timestamps).
    """

    # ── Identifiers ──────────────────────────────────────────────────────
    id: uuid.UUID = Field(..., description="Briefing cache record ID")
    entity_type: str = Field(..., description="account, contact, or opportunity")
    entity_id: uuid.UUID = Field(..., description="ID of the briefed entity")

    # ── Briefing Content ─────────────────────────────────────────────────
    briefing_markdown: str | None = Field(
        default=None,
        description="Account-level strategic briefing in Markdown",
    )
    contact_briefing_markdown: str | None = Field(
        default=None,
        description="Contact-specific executive briefing in Markdown",
    )

    # ── AI Enrichment ────────────────────────────────────────────────────
    p2b_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Propensity to Buy score (0-100)",
    )
    account_signal: str | None = Field(
        default=None,
        description="1-2 sentence strategic account signal",
    )
    why_we_matter: str | None = Field(
        default=None,
        description="Value proposition tying our differentiators to their pain",
    )
    anticipated_objection: str | None = Field(
        default=None,
        description="Most likely executive objection",
    )
    objection_pivot: str | None = Field(
        default=None,
        description="Strategic pivot to redirect the objection",
    )
    suggested_contacts: list[SuggestedContact] | None = Field(
        default=None,
        description="AI-suggested buying committee personas",
    )

    # ── Cache Metadata ───────────────────────────────────────────────────
    generated_at: datetime = Field(
        ..., description="When this briefing was generated"
    )
    expires_at: datetime = Field(
        ..., description="When this briefing cache expires"
    )
    cache_hit: bool = Field(
        default=False, description="Whether this response was served from cache"
    )

    model_config = {"from_attributes": True}


class BriefingCacheHitResponse(BaseModel):
    """Lightweight response when a valid cached briefing exists."""

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    briefing_markdown: str | None = None
    contact_briefing_markdown: str | None = None
    p2b_score: int | None = None
    account_signal: str | None = None
    why_we_matter: str | None = None
    generated_at: datetime
    expires_at: datetime
    cache_hit: bool = True

    model_config = {"from_attributes": True}
