from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SubscriptionFinancialTerms(Base):

    __tablename__ = "subscription_financial_terms"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    subscription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscriptions.id")
    )

    billing_amount: Mapped[float] = mapped_column(Numeric)

    billing_frequency: Mapped[str] = mapped_column(String(50))

    discount_rate: Mapped[float] = mapped_column(Numeric)

    currency: Mapped[str] = mapped_column(String(10))

    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))