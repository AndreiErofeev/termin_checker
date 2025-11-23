"""
Database Connection and Session Management

This module provides database connection handling, session management,
and initialization utilities.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base, Service, SystemConfig

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""

    def __init__(self, database_url: str = "sqlite:///appointments.db", echo: bool = False):
        """
        Initialize database connection

        Args:
            database_url: SQLAlchemy database URL
            echo: Whether to echo SQL statements (for debugging)
        """
        self.database_url = database_url
        self.echo = echo

        # Create engine
        if database_url.startswith("sqlite"):
            # SQLite-specific settings
            self.engine = create_engine(
                database_url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )

            # Enable foreign key constraints for SQLite
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        else:
            # PostgreSQL or other databases
            self.engine = create_engine(
                database_url,
                echo=echo,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info(f"Database initialized: {database_url}")

    def create_tables(self):
        """Create all database tables"""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self):
        """Drop all database tables (USE WITH CAUTION!)"""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")

    def reset_database(self):
        """Reset database (drop and recreate all tables)"""
        self.drop_tables()
        self.create_tables()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions

        Usage:
            with db.get_session() as session:
                user = session.query(User).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def init_default_data(self):
        """Initialize database with default data"""
        logger.info("Initializing default data...")

        with self.get_session() as session:
            # Check if data already exists
            service_count = session.query(Service).count()

            if service_count > 0:
                logger.info(f"Database already contains {service_count} services. Skipping initialization.")
                return

            # Add default services
            default_services = [
                {
                    "category": "Umschreibung ausländische Fahrerlaubnis / Dienstfahrerlaubnis",
                    "service_name": "Umschreibung ausländischer Führerschein (sonstige Staaten)",
                    "description": "Driver's license conversion from non-EU countries",
                    "priority": 10
                },
                {
                    "category": "Abholung Führerschein / Rückfragen",
                    "service_name": "Abholung Führerschein",
                    "description": "Driver's license pickup",
                    "priority": 5
                },
                {
                    "category": "Umschreibung ausländische Fahrerlaubnis / Dienstfahrerlaubnis",
                    "service_name": "Umschreibung ausländischer Führerschein (EU+EWR)",
                    "description": "Driver's license conversion from EU/EEA countries",
                    "priority": 8
                },
                {
                    "category": "Ersterteilung / Erweiterung",
                    "service_name": "Antrag auf Ersterteilung Fahrerlaubnis",
                    "description": "First-time driver's license application",
                    "priority": 7
                },
                {
                    "category": "Pflichtumtausch/Ersatzführerschein",
                    "service_name": "Pflichtumtausch Führerschein",
                    "description": "Mandatory driver's license exchange",
                    "priority": 6
                },
            ]

            for service_data in default_services:
                service = Service(**service_data)
                session.add(service)

            # Add system configuration
            config_items = [
                {
                    "key": "version",
                    "value": "1.0.0",
                    "description": "System version"
                },
                {
                    "key": "max_checks_per_user_hour",
                    "value": "10",
                    "description": "Maximum manual checks per user per hour"
                },
                {
                    "key": "default_check_interval",
                    "value": "60",
                    "description": "Default check interval in minutes"
                },
                {
                    "key": "max_subscriptions_free",
                    "value": "1",
                    "description": "Maximum subscriptions for free users"
                },
                {
                    "key": "max_subscriptions_premium",
                    "value": "5",
                    "description": "Maximum subscriptions for premium users"
                },
            ]

            for config_data in config_items:
                config = SystemConfig(**config_data)
                session.add(config)

            session.commit()
            logger.info(f"Added {len(default_services)} default services and {len(config_items)} config items")

    def get_stats(self) -> dict:
        """Get database statistics"""
        with self.get_session() as session:
            from .models import User, Service, Subscription, Check, Appointment

            stats = {
                "users": session.query(User).count(),
                "active_users": session.query(User).filter(User.active == True).count(),
                "services": session.query(Service).count(),
                "active_services": session.query(Service).filter(Service.active == True).count(),
                "subscriptions": session.query(Subscription).count(),
                "active_subscriptions": session.query(Subscription).filter(Subscription.active == True).count(),
                "total_checks": session.query(Check).count(),
                "total_appointments_found": session.query(Appointment).count(),
            }

            return stats


# Global database instance
db: Optional[Database] = None


def init_database(database_url: str = "sqlite:///appointments.db", echo: bool = False) -> Database:
    """
    Initialize global database instance

    Args:
        database_url: SQLAlchemy database URL
        echo: Whether to echo SQL statements

    Returns:
        Database instance
    """
    global db
    db = Database(database_url, echo)
    return db


def get_db() -> Database:
    """
    Get global database instance

    Returns:
        Database instance

    Raises:
        RuntimeError: If database not initialized
    """
    if db is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db


# Convenience function for getting sessions
def get_session() -> Generator[Session, None, None]:
    """
    Get database session (convenience wrapper)

    Yields:
        SQLAlchemy session
    """
    return get_db().get_session()


if __name__ == "__main__":
    """CLI for database management"""
    import sys

    logging.basicConfig(level=logging.INFO)

    # Parse command line arguments
    command = sys.argv[1] if len(sys.argv) > 1 else "init"

    # Initialize database
    database = init_database(echo=True)

    if command == "init":
        # Create tables and add default data
        database.create_tables()
        database.init_default_data()
        print("\n✓ Database initialized successfully")

        # Print stats
        stats = database.get_stats()
        print("\nDatabase Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    elif command == "reset":
        # Reset database
        confirm = input("⚠️  This will DELETE ALL DATA. Type 'yes' to confirm: ")
        if confirm.lower() == "yes":
            database.reset_database()
            database.init_default_data()
            print("\n✓ Database reset successfully")
        else:
            print("Cancelled")

    elif command == "stats":
        # Show statistics
        stats = database.get_stats()
        print("\nDatabase Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    elif command == "create":
        # Just create tables
        database.create_tables()
        print("\n✓ Tables created")

    else:
        print(f"""
Database Management CLI

Usage: python database.py [command]

Commands:
  init    - Initialize database with tables and default data (default)
  create  - Create tables only
  reset   - Reset database (WARNING: deletes all data!)
  stats   - Show database statistics

Examples:
  python database.py init
  python database.py stats
  python database.py reset
""")
