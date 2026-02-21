from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.base import Base

metric_record_tags = Table(
    "metric_record_tags",
    Base.metadata,
    Column("record_id", ForeignKey("metric_records.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    metrics: Mapped[list["Metric"]] = relationship(back_populates="user")

    def __str__(self) -> str:
        return self.email


class Metric(Base):
    __tablename__ = "metrics"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_metrics_user_name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="metrics")
    records: Mapped[list["MetricRecord"]] = relationship(
        back_populates="metric", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return self.name


class MetricRecord(Base):
    __tablename__ = "metric_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    metric_id: Mapped[UUID] = mapped_column(
        ForeignKey("metrics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    metric: Mapped["Metric"] = relationship(back_populates="records")
    tags: Mapped[list["Tag"]] = relationship(secondary=metric_record_tags, back_populates="records")

    def __str__(self) -> str:
        timestamp_iso = self.timestamp.replace(microsecond=0).isoformat()
        return f"{self.metric_id} @ {timestamp_iso}"


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    records: Mapped[list["MetricRecord"]] = relationship(
        secondary=metric_record_tags,
        back_populates="tags",
    )

    def __str__(self) -> str:
        return self.name
