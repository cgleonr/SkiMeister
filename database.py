"""
Database initialization and management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
import config


# Create engine
engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    echo=config.DEBUG,
    connect_args={'check_same_thread': False}  # Needed for SQLite
)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def init_db():
    """Initialize the database (create all tables)"""
    Base.metadata.create_all(engine)
    print(f"✓ Database initialized at {config.DATABASE_PATH}")


def get_session():
    """Get a database session"""
    return Session()


def close_session():
    """Close the scoped session"""
    Session.remove()


if __name__ == '__main__':
    # Create database when run directly
    init_db()
