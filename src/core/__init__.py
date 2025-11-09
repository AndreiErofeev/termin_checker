"""Core modules for appointment checking and database management"""

from .appointment_checker import AppointmentChecker, CheckResult, AppointmentSlot
from .database import Database, init_database, get_db
from .models import (
    Base,
    User, UserPlan,
    Service,
    Subscription,
    Check, CheckStatus,
    Appointment,
    Notification,
    SystemConfig,
    AuditLog
)

__all__ = [
    # Appointment checker
    'AppointmentChecker',
    'CheckResult',
    'AppointmentSlot',

    # Database
    'Database',
    'init_database',
    'get_db',

    # Models
    'Base',
    'User',
    'UserPlan',
    'Service',
    'Subscription',
    'Check',
    'CheckStatus',
    'Appointment',
    'Notification',
    'SystemConfig',
    'AuditLog',
]
