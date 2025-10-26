#!/usr/bin/env python3
"""
Database migration management CLI for Local Brain.

Provides a simplified interface for common Alembic operations.
"""
import sys
import subprocess
from pathlib import Path


def run_alembic_command(args: list[str]) -> int:
    """
    Run an Alembic command with proper configuration.

    Args:
        args: List of Alembic command arguments

    Returns:
        Exit code from Alembic command
    """
    # Change to server directory for proper alembic.ini resolution
    server_dir = Path(__file__).parent
    cmd = ["alembic", "-c", str(server_dir / "alembic.ini")] + args

    try:
        result = subprocess.run(cmd, cwd=server_dir)
        return result.returncode
    except FileNotFoundError:
        print("Error: Alembic is not installed.")
        print("Please run: pip3 install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"Error running migration command: {e}")
        return 1


def show_help():
    """Display help information."""
    print("""
Local Brain Migration Manager

Usage:
    python3 server/migrate.py <command> [options]

Commands:
    up              Run all pending migrations (upgrade to head)
    down            Rollback the last migration
    status          Show current migration status
    history         Show migration history
    new <message>   Create a new migration file
    current         Show current revision
    heads           Show head revisions
    help            Show this help message

Examples:
    # Run pending migrations
    python3 server/migrate.py up

    # Create a new migration
    python3 server/migrate.py new "add user preferences table"

    # Check current status
    python3 server/migrate.py status

    # Rollback last migration
    python3 server/migrate.py down

For more advanced usage, use Alembic directly:
    cd server && alembic --help
""")


def main():
    """Main entry point for migration CLI."""
    if len(sys.argv) < 2:
        show_help()
        return 1

    command = sys.argv[1].lower()

    if command in ["help", "-h", "--help"]:
        show_help()
        return 0

    elif command == "up":
        print("Running pending migrations...")
        return run_alembic_command(["upgrade", "head"])

    elif command == "down":
        print("Rolling back last migration...")
        return run_alembic_command(["downgrade", "-1"])

    elif command == "status":
        print("Current migration status:")
        return run_alembic_command(["current", "-v"])

    elif command == "history":
        print("Migration history:")
        return run_alembic_command(["history", "-v"])

    elif command == "current":
        return run_alembic_command(["current"])

    elif command == "heads":
        return run_alembic_command(["heads"])

    elif command == "new":
        if len(sys.argv) < 3:
            print("Error: Migration message required")
            print("Usage: python3 server/migrate.py new \"migration message\"")
            return 1

        message = " ".join(sys.argv[2:])
        print(f"Creating new migration: {message}")
        return run_alembic_command(["revision", "-m", message])

    else:
        print(f"Error: Unknown command '{command}'")
        print("Run 'python3 server/migrate.py help' for usage information")
        return 1


if __name__ == "__main__":
    sys.exit(main())
