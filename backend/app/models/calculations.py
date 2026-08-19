from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SubscriptionCalculation(Base):

    __tablename__ = "subscription_calculations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    subscription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscriptions.id")
    )

    calculation_type: Mapped[str] = mapped_column(String)

    total_revenue: Mapped[float] = mapped_column(Numeric)

    contract_term_months: Mapped[int] = mapped_column(Integer)

    version: Mapped[int] = mapped_column(Integer)

    is_active: Mapped[bool] = mapped_column(Boolean)

    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))