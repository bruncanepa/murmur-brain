"""
Automatic database migration management.

Handles running Alembic migrations automatically on application startup.
"""
import sys
from pathlib import Path
from typing import Optional, Tuple
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext


def get_alembic_config() -> Config:
    """Get Alembic configuration with correct paths for both dev and PyInstaller."""
    # Handle both development and PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)
        server_path = base_path
    else:
        # Running in development
        server_path = Path(__file__).parent.parent

    alembic_ini_path = server_path / "alembic.ini"

    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"alembic.ini not found at {alembic_ini_path}")

    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(server_path / "migrations"))

    return config


def get_current_revision(db_path: str) -> Optional[str]:
    """Get the current database revision, or None if not initialized."""
    try:
        from sqlalchemy import create_engine
        engine = create_engine(f"sqlite:///{db_path}")

        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            return current_rev
    except Exception:
        # Database doesn't exist or alembic_version table doesn't exist
        return None


def get_head_revision() -> str:
    """Get the head (latest) migration revision."""
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)
    return script.get_current_head()


def needs_migration(db_path: str) -> bool:
    """Check if database needs migration."""
    current = get_current_revision(db_path)
    head = get_head_revision()

    # Need migration if:
    # - No current revision (fresh database)
    # - Current revision is behind head
    return current is None or current != head


def run_migrations(db_path: str) -> Tuple[bool, str]:
    """
    Run database migrations to head revision.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        config = get_alembic_config()

        # Set the database URL in config
        config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

        # Run upgrade to head
        command.upgrade(config, "head")

        return True, "Database migrations completed successfully"

    except Exception as e:
        error_msg = f"Failed to run migrations: {str(e)}"
        print(f"ERROR: {error_msg}")
        return False, error_msg


def auto_migrate(db_path: str, force: bool = False) -> bool:
    """
    Automatically run migrations if needed.

    Args:
        db_path: Path to SQLite database file
        force: If True, run migrations even if not needed

    Returns:
        True if successful or no migration needed, False on error
    """
    try:
        if force or needs_migration(db_path):
            current = get_current_revision(db_path)
            head = get_head_revision()

            if current is None:
                print(f"📦 Initializing new database with schema revision {head}...")
            else:
                print(f"🔄 Migrating database from {current} to {head}...")

            success, message = run_migrations(db_path)

            if success:
                print(f"✓ {message}")
                return True
            else:
                print(f"✗ {message}")
                return False
        else:
            # No migration needed
            current = get_current_revision(db_path)
            print(f"✓ Database is up to date (revision: {current})")
            return True

    except Exception as e:
        print(f"ERROR: Auto-migration failed: {e}")
        return False
