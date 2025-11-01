# Database Migration Setup Guide

## Installation

1. **Install Alembic** (if not already installed):

```bash
pip3 install -r server/requirements.txt
```

2. **Initialize your database** with migrations:

```bash
# Run the initial migration
pnpm migrate:up
```

That's it! Your database is now managed by migrations.

## What Changed?

### New Files Created

```
server/
├── alembic.ini                          # Alembic configuration
├── migrate.py                           # Migration CLI tool
├── migrations/
│   ├── README.md                        # Full migration documentation
│   ├── env.py                           # Alembic environment config
│   ├── script.py.mako                   # Migration template
│   └── versions/
│       └── 001_initial_schema.py        # Initial database schema
```

### Files Modified

- `server/requirements.txt` - Added `alembic==1.13.1`
- `package.json` - Added migration commands
- `server/modules/documents/documents_model.py` - Removed `_ensure_tables()`
- `server/modules/chats/chats_model.py` - Removed `_ensure_tables()` and old migration code
- `server/modules/messages/messages_model.py` - Removed `_ensure_tables()`

### New NPM Commands

```json
{
  "migrate:up": "Run pending migrations",
  "migrate:down": "Rollback last migration",
  "migrate:status": "Show migration status",
  "migrate:new": "Create new migration",
  "migrate:history": "Show migration history"
}
```

## Quick Start

### Check Current Status

```bash
pnpm migrate:status
```

### Run Migrations

```bash
pnpm migrate:up
```

### Create New Migration

```bash
pnpm migrate:new "add user settings table"
```

Then edit the generated file in `server/migrations/versions/` and run:

```bash
pnpm migrate:up
```

## Example: Creating a New Migration

Let's say you want to add a `user_settings` table:

```bash
# 1. Create migration
pnpm migrate:new "add user settings table"

# 2. Edit the generated file in server/migrations/versions/
# Add your table creation in upgrade() function

# 3. Run the migration
pnpm migrate:up

# 4. Verify
pnpm migrate:status
```

## Benefits

✅ **Version Control** - All schema changes tracked in git
✅ **Reproducible** - Recreate database on any machine
✅ **Team Friendly** - No more schema conflicts
✅ **Rollback Support** - Undo migrations safely
✅ **Production Ready** - Industry-standard tool

## Troubleshooting

### "Alembic not installed"

```bash
pip3 install alembic==1.13.1
```

### Migration already applied

Your existing database tables are compatible. The first migration will recognize existing tables.

### Need to start fresh?

```bash
# WARNING: This deletes all data
rm ~/Library/Application\ Support/murmur-brain/murmur-brain.db
pnpm migrate:up
```

## Next Steps

1. **Run the initial migration**: `pnpm migrate:up`
2. **Read the full docs**: `server/migrations/README.md`
3. **Start developing**: Create migrations as you add features

## Common Workflow

```bash
# Daily workflow
git pull                    # Get latest migrations
pnpm migrate:up            # Apply new migrations
pnpm dev:all               # Start development

# Adding a feature with schema changes
pnpm migrate:new "add feature X table"
# Edit migration file
pnpm migrate:up
# Test your feature
git add server/migrations/versions/
git commit -m "Add feature X migration"
```

## Resources

- Full documentation: `server/migrations/README.md`
- Alembic docs: https://alembic.sqlalchemy.org/
- Migration files: `server/migrations/versions/`

---

**Questions?** Check `server/migrations/README.md` for detailed documentation.
