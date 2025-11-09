"""
Database Models for Düsseldorf Appointment Checker

This module defines the SQLAlchemy models for:
- Users (Telegram users)
- Services (available appointment services)
- Subscriptions (user subscriptions to services)
- Checks (appointment check history)
- Appointments (found appointment slots)
- Notifications (sent notifications)
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Boolean, Column, DateTime, Integer, String, Text, ForeignKey,
    UniqueConstraint, Index, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class UserPlan(str, enum.Enum):
    """User subscription plans"""
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"


class CheckStatus(str, enum.Enum):
    """Status of appointment checks"""
    SUCCESS = "success"
    NO_APPOINTMENTS = "no_appointments"
    APPOINTMENTS_FOUND = "appointments_found"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class User(Base):
    """Telegram user model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)

    # Account settings
    plan = Column(SQLEnum(UserPlan), default=UserPlan.FREE, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    language = Column(String(10), default="de", nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


class Service(Base):
    """Available appointment services"""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)

    # Service identification
    category = Column(String(500), nullable=False)
    service_name = Column(String(500), nullable=False)

    # Configuration
    base_url = Column(String(500), default="https://termine.duesseldorf.de/select2?md=3")
    active = Column(Boolean, default=True, nullable=False)

    # Metadata
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=0)  # Higher = more important

    # Statistics
    total_checks = Column(Integer, default=0)
    appointments_found_count = Column(Integer, default=0)
    last_check_at = Column(DateTime, nullable=True)
    last_appointments_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="service", cascade="all, delete-orphan")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('category', 'service_name', name='uix_category_service'),
        Index('idx_service_active', 'active'),
    )

    def __repr__(self):
        return f"<Service(id={self.id}, category={self.category[:30]}..., service={self.service_name[:30]}...)>"


class Subscription(Base):
    """User subscriptions to services"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)

    # Settings
    active = Column(Boolean, default=True, nullable=False)
    interval_hours = Column(Integer, default=1, nullable=False)  # Check frequency
    quantity = Column(Integer, default=1, nullable=False)  # Number of appointments needed

    # Notification preferences
    notify_telegram = Column(Boolean, default=True, nullable=False)
    notify_on_found = Column(Boolean, default=True, nullable=False)
    notify_on_error = Column(Boolean, default=False, nullable=False)

    # State
    last_checked_at = Column(DateTime, nullable=True)
    last_status = Column(SQLEnum(CheckStatus), nullable=True)
    last_appointment_count = Column(Integer, default=0)
    consecutive_errors = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    service = relationship("Service", back_populates="subscriptions")
    checks = relationship("Check", back_populates="subscription", cascade="all, delete-orphan")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'service_id', name='uix_user_service'),
        Index('idx_subscription_active', 'active'),
        Index('idx_subscription_last_checked', 'last_checked_at'),
    )

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, service_id={self.service_id}, active={self.active})>"


class Check(Base):
    """Appointment check history"""
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)

    # Check details
    status = Column(SQLEnum(CheckStatus), nullable=False)
    available = Column(Boolean, default=False, nullable=False)
    appointment_count = Column(Integer, default=0)

    # Error information
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)

    # Metadata
    screenshot_path = Column(String(500), nullable=True)
    page_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Timestamp
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="checks")
    appointments = relationship("Appointment", back_populates="check", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="check", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_check_subscription_date', 'subscription_id', 'checked_at'),
        Index('idx_check_status', 'status'),
    )

    def __repr__(self):
        return f"<Check(id={self.id}, subscription_id={self.subscription_id}, status={self.status}, available={self.available})>"


class Appointment(Base):
    """Found appointment slots"""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    check_id = Column(Integer, ForeignKey("checks.id", ondelete="CASCADE"), nullable=False)

    # Appointment details
    appointment_date = Column(String(20), nullable=False)  # ISO format: YYYY-MM-DD
    appointment_time = Column(String(10), nullable=False)  # 24h format: HH:MM
    raw_text = Column(Text, nullable=True)

    # Metadata
    location = Column(String(500), nullable=True)
    booking_url = Column(String(500), nullable=True)

    # Notification tracking
    notified = Column(Boolean, default=False, nullable=False)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    check = relationship("Check", back_populates="appointments")

    __table_args__ = (
        Index('idx_appointment_date', 'appointment_date'),
        Index('idx_appointment_check', 'check_id'),
    )

    def __repr__(self):
        return f"<Appointment(id={self.id}, date={self.appointment_date}, time={self.appointment_time})>"


class Notification(Base):
    """Sent notifications"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    check_id = Column(Integer, ForeignKey("checks.id", ondelete="SET NULL"), nullable=True)

    # Notification details
    notification_type = Column(String(50), nullable=False)  # appointments_found, error, reminder
    message = Column(Text, nullable=False)

    # Delivery
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")
    check = relationship("Check", back_populates="notifications")

    __table_args__ = (
        Index('idx_notification_user_date', 'user_id', 'sent_at'),
        Index('idx_notification_type', 'notification_type'),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.notification_type}, success={self.success})>"


# Additional helper models

class SystemConfig(Base):
    """System-wide configuration"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SystemConfig(key={self.key}, value={self.value[:50] if self.value else None})>"


class AuditLog(Base):
    """Audit log for important system events"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Event details
    event_type = Column(String(100), nullable=False)  # user_created, subscription_created, etc.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Event data
    description = Column(Text, nullable=False)
    event_metadata = Column(Text, nullable=True)  # JSON string
    ip_address = Column(String(50), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_audit_type_date', 'event_type', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, created_at={self.created_at})>"
