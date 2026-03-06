# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Import all model modules to register tables with Base.metadata
from .base import Base


def create_all_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Drop all database tables"""
    Base.metadata.drop_all(engine)
