from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BillingSchedule(Base):

    __tablename__ = "billing_schedules"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    subscription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscriptions.id")
    )

    billing_period: Mapped[int] = mapped_column(Integer)

    billing_start_date: Mapped[str] = mapped_column(Date)

    billing_end_date: Mapped[str] = mapped_column(Date)

    billing_amount: Mapped[float] = mapped_column(Numeric)

    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))