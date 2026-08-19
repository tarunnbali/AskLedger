from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Subscription(Base):

    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    subscription_id: Mapped[str] = mapped_column(String(50))

    subscription_name: Mapped[str] = mapped_column(String(255))

    plan_type: Mapped[str] = mapped_column(String(50))

    status: Mapped[str] = mapped_column(String(50))

    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))

    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
    )