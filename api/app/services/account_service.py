"""Account upsert service — idempotent account creation/update.

Per defensive-programming.md §3: non-null overwrites only.
Per defensive-programming.md §4: upsert idempotency via (source_system, external_id).
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.schemas.briefing import BriefingGenerateRequest

logger = logging.getLogger(__name__)


async def upsert_account(
    db: AsyncSession, request: BriefingGenerateRequest,
) -> Account:
    """Upsert by (source_system, external_id). Non-null fields only."""
    account: Account | None = None

    if request.external_id:
        result = await db.execute(
            select(Account).where(
                Account.source_system == request.source_system,
                Account.external_id == request.external_id,
            )
        )
        account = result.scalar_one_or_none()

    if account is None:
        account = Account(
            external_id=request.external_id,
            source_system=request.source_system,
            name=request.account.name,
            industry=request.account.industry,
            type=request.account.type,
            annual_revenue=request.account.annual_revenue,
            number_of_employees=request.account.number_of_employees,
            website=request.account.website,
            phone=request.account.phone,
            billing_address=request.account.billing_address,
        )
        db.add(account)
        await db.flush()
        await db.refresh(account)
    else:
        account.name = request.account.name
        if request.account.industry is not None:
            account.industry = request.account.industry
        if request.account.type is not None:
            account.type = request.account.type
        if request.account.annual_revenue is not None:
            account.annual_revenue = request.account.annual_revenue
        if request.account.number_of_employees is not None:
            account.number_of_employees = request.account.number_of_employees
        if request.account.website is not None:
            account.website = request.account.website
        await db.flush()
        await db.refresh(account)

    return account
