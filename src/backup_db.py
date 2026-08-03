"""
Sprint 2 — automated SQLite backups.

leads.db is a single file with no redundancy of its own, so this script is
what actually protects the lead intake log and expense correction history
once BUSINESS_MODE starts writing real data to it. Built now, before
either table holds real rows, per docs/decision_log.md.

Uses sqlite3's online backup API rather than a plain file copy, so it's
safe to run while the app has the database open (works correctly with the
WAL mode enabled in database.py — a raw `cp` of a WAL database can copy a
half-written state).

Usage:
    python src/backup_db.py backup                       # take a backup now
    python src/backup_db.py backup --retention-days 30    # and prune older ones
    python src/backup_db.py list                          # list existing backups
    python src/backup_db.py restore <backup_file>          # restore a backup
    python src/backup_db.py restore <backup_file> --yes    # skip confirmation

Intended to run daily via a scheduled task (cron / Windows Task Scheduler),
per the Sprint 4/5 deployment plan — see docs/decision_log.md.
"""

import argparse
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_DB_PATH = Path("leads.db")
DEFAULT_BACKUP_DIR = Path("backups")
DEFAULT_RETENTION_DAYS = 30

TIMESTAMP_FMT = "%Y%m%d_%H%M%S"


def backup_db(db_path: Path = DEFAULT_DB_PATH, backup_dir: Path = DEFAULT_BACKUP_DIR) -> Path:
    """Take a consistent online backup of db_path into backup_dir. Safe to
    run while the database is open elsewhere (WAL-aware)."""
    if not db_path.exists():
        raise FileNotFoundError(f"No database found at {db_path} — nothing to back up.")

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime(TIMESTAMP_FMT)
    dest_path = backup_dir / f"{db_path.stem}_{timestamp}{db_path.suffix}"

    source_conn = sqlite3.connect(db_path)
    dest_conn = sqlite3.connect(dest_path)
    try:
        source_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        source_conn.close()

    return dest_path


def list_backups(backup_dir: Path = DEFAULT_BACKUP_DIR, db_stem: str = DEFAULT_DB_PATH.stem) -> list[Path]:
    if not backup_dir.exists():
        return []
    return sorted(backup_dir.glob(f"{db_stem}_*.db"))


def _backup_timestamp(path: Path) -> datetime:
    # filenames look like leads_20260715_143000.db
    stamp = path.stem.split("_", 1)[1]
    return datetime.strptime(stamp, TIMESTAMP_FMT)


def prune_old_backups(
    backup_dir: Path = DEFAULT_BACKUP_DIR,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    db_stem: str = DEFAULT_DB_PATH.stem,
) -> list[Path]:
    """Delete backups older than retention_days. Returns the list of files
    that were removed."""
    cutoff = datetime.now() - timedelta(days=retention_days)
    removed = []
    for backup_path in list_backups(backup_dir, db_stem):
        try:
            if _backup_timestamp(backup_path) < cutoff:
                backup_path.unlink()
                removed.append(backup_path)
        except ValueError:
            continue  # doesn't match the expected naming pattern - leave it alone
    return removed


def restore_backup(backup_path: Path, db_path: Path = DEFAULT_DB_PATH) -> None:
    """Restore db_path from a backup file. Overwrites the current database,
    so this is destructive by design — callers should confirm with the user
    first (the CLI below does)."""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    # Take a safety copy of whatever's currently live before overwriting it,
    # in case the restore itself was a mistake.
    if db_path.exists():
        safety_copy = db_path.with_name(f"{db_path.stem}_pre_restore_{datetime.now().strftime(TIMESTAMP_FMT)}{db_path.suffix}")
        shutil.copy2(db_path, safety_copy)

    backup_conn = sqlite3.connect(backup_path)
    dest_conn = sqlite3.connect(db_path)
    try:
        backup_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        backup_conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup and restore leads.db")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS)

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("backup", help="Take a backup now and prune old ones.")
    subparsers.add_parser("list", help="List existing backups.")
    restore_parser = subparsers.add_parser("restore", help="Restore from a backup file.")
    restore_parser.add_argument("backup_file", type=Path, help="Path to the backup .db file to restore.")
    restore_parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")

    args = parser.parse_args()

    if args.command == "backup":
        dest = backup_db(args.db_path, args.backup_dir)
        print(f"Backed up {args.db_path} -> {dest}")
        removed = prune_old_backups(args.backup_dir, args.retention_days, args.db_path.stem)
        if removed:
            print(f"Pruned {len(removed)} backup(s) older than {args.retention_days} days:")
            for path in removed:
                print(f"  {path}")

    elif args.command == "list":
        backups = list_backups(args.backup_dir, args.db_path.stem)
        if not backups:
            print(f"No backups found in {args.backup_dir}")
        for path in backups:
            print(path)

    elif args.command == "restore":
        if not args.yes:
            confirm = input(
                f"This will overwrite {args.db_path} with {args.backup_file}. "
                f"A safety copy of the current database will be made first. Continue? [y/N] "
            )
            if confirm.strip().lower() != "y":
                print("Restore cancelled.")
                return
        restore_backup(args.backup_file, args.db_path)
        print(f"Restored {args.db_path} from {args.backup_file}")


if __name__ == "__main__":
    main()
