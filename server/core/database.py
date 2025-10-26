"""
Database connection and base repository for Local Brain.

Provides a singleton database connection and base repository class
for all feature modules to extend.
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class DatabaseConnection:
    """Manages SQLite database connection with WAL mode enabled."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use standard application support directory
            home = Path.home()
            db_dir = home / "Library" / "Application Support" / "local-brain"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / "local-brain.db")

        self.db_path = db_path
        self.conn = None
        self.initialize()

    def initialize(self):
        """Initialize database connection and enable WAL mode."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # Enable WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")

        print(f"Database initialized at: {self.db_path}")

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor operations."""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()

    def execute(self, query: str, params: tuple = ()):
        """Execute a query and return cursor."""
        return self.conn.execute(query, params)

    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute query and fetch one result."""
        cursor = self.conn.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute query and fetch all results."""
        cursor = self.conn.execute(query, params)
        return cursor.fetchall()

    def commit(self):
        """Commit current transaction."""
        self.conn.commit()

    def rollback(self):
        """Rollback current transaction."""
        self.conn.rollback()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


class BaseRepository:
    """
    Base repository class providing common database operations.

    Feature modules should extend this class for their specific repositories.
    """

    def __init__(self, db: DatabaseConnection):
        self.db = db

    def _dict_from_row(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        """Convert sqlite3.Row to dictionary."""
        if row is None:
            return None
        return dict(row)

    def _dicts_from_rows(self, rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
        """Convert list of sqlite3.Row to list of dictionaries."""
        return [dict(row) for row in rows]


# Singleton database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """Get or create the singleton database connection."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def close_db_connection():
    """Close the singleton database connection."""
    global _db_connection
    if _db_connection is not None:
        _db_connection.close()
        _db_connection = None
