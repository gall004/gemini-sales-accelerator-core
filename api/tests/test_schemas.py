"""Tests for Pydantic schema validation.

Validates request/response models enforce constraints correctly —
independent of the API layer.
"""

import pytest
from pydantic import ValidationError

from app.schemas.briefing import (
    AccountInput,
    BriefingGenerateRequest,
    ContactInput,
)


# ── AccountInput ─────────────────────────────────────────────────────────────


def test_account_input_valid():
    """AccountInput accepts valid data."""
    account = AccountInput(name="Test Corp", industry="Tech")
    assert account.name == "Test Corp"
    assert account.industry == "Tech"


def test_account_input_requires_name():
    """AccountInput rejects missing name."""
    with pytest.raises(ValidationError) as exc_info:
        AccountInput(industry="Tech")
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("name",) for e in errors)


def test_account_input_rejects_empty_name():
    """AccountInput rejects empty string name."""
    with pytest.raises(ValidationError):
        AccountInput(name="")


def test_account_input_rejects_negative_revenue():
    """AccountInput rejects negative annual_revenue."""
    with pytest.raises(ValidationError):
        AccountInput(name="Test", annual_revenue=-1)


# ── ContactInput ─────────────────────────────────────────────────────────────


def test_contact_input_requires_last_name():
    """ContactInput rejects missing last_name."""
    with pytest.raises(ValidationError) as exc_info:
        ContactInput(first_name="Jane")
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("last_name",) for e in errors)


def test_contact_input_valid():
    """ContactInput accepts valid data with optional fields."""
    contact = ContactInput(last_name="Doe", title="CTO")
    assert contact.last_name == "Doe"
    assert contact.first_name is None


# ── BriefingGenerateRequest ──────────────────────────────────────────────────


def test_request_valid_minimal():
    """Minimal valid request with only required fields."""
    req = BriefingGenerateRequest(
        entity_type="account",
        account=AccountInput(name="Test Corp"),
    )
    assert req.entity_type == "account"
    assert req.force_refresh is False
    assert req.campaign_context is None


def test_request_valid_full():
    """Fully populated request with all optional fields."""
    req = BriefingGenerateRequest(
        entity_type="account",
        account=AccountInput(name="Full Corp", industry="Tech"),
        contact=ContactInput(first_name="J", last_name="D"),
        force_refresh=True,
        source_system="salesforce",
        external_id="001ABC",
        campaign_context="Cisco Contact Center Modernization",
    )
    assert req.campaign_context == "Cisco Contact Center Modernization"
    assert req.contact.last_name == "D"


def test_request_rejects_invalid_entity_type():
    """Invalid entity_type is rejected by the validator."""
    with pytest.raises(ValidationError) as exc_info:
        BriefingGenerateRequest(
            entity_type="invalid",
            account=AccountInput(name="Test"),
        )
    assert "entity_type" in str(exc_info.value)


def test_request_normalizes_entity_type_case():
    """entity_type is normalized to lowercase."""
    req = BriefingGenerateRequest(
        entity_type="Account",
        account=AccountInput(name="Test"),
    )
    assert req.entity_type == "account"


def test_campaign_context_max_length():
    """campaign_context rejects strings exceeding 2000 characters."""
    with pytest.raises(ValidationError):
        BriefingGenerateRequest(
            entity_type="account",
            account=AccountInput(name="Test"),
            campaign_context="x" * 2001,
        )


def test_campaign_context_accepts_max_length():
    """campaign_context accepts exactly 2000 characters."""
    req = BriefingGenerateRequest(
        entity_type="account",
        account=AccountInput(name="Test"),
        campaign_context="x" * 2000,
    )
    assert len(req.campaign_context) == 2000
