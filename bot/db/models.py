"""
SQLAlchemy models for the Telegram bot database.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, CheckConstraint, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """
    User model for storing collected user information.

    Attributes:
        id: Auto-incrementing primary key
        telegram_user_id: Unique Telegram user ID
        name: User's full name (1-100 characters)
        age: User's age (13-120)
        address: User's address (1-255 characters)
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )

    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp()
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    __table_args__ = (
        CheckConstraint("age >= 13 AND age <= 120", name="age_range_check"),
    )

    def __repr__(self) -> str:
        """String representation of the User model."""
        return (
            f"<User(id={self.id}, telegram_user_id={self.telegram_user_id}, "
            f"name='{self.name[:20]}...', age={self.age})>"
        )
