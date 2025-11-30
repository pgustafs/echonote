#!/usr/bin/env python3
"""
Fix partially applied migration 005 (MinIO object storage).

This script manually rolls back the minio_object_path column and index
that were added before the migration failed on the ALTER COLUMN step.
"""
import sqlite3
import sys

DB_PATH = "echonote.db"

def main():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check current state
        cursor.execute("PRAGMA table_info(transcriptions)")
        columns = {col[1]: col for col in cursor.fetchall()}

        print("\nCurrent columns:")
        for col_name in columns:
            print(f"  - {col_name}")

        # Check if minio_object_path exists
        has_minio_col = 'minio_object_path' in columns
        print(f"\nminio_object_path exists: {has_minio_col}")

        if not has_minio_col:
            print("\n✅ Database is clean - no rollback needed")
            return 0

        print("\n🔧 Rolling back partial migration...")

        # Drop the index if it exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index'
            AND name='ix_transcriptions_minio_object_path'
        """)
        if cursor.fetchone():
            print("  - Dropping index ix_transcriptions_minio_object_path...")
            cursor.execute("DROP INDEX ix_transcriptions_minio_object_path")

        # For SQLite, we need to recreate the table without minio_object_path
        print("  - Recreating table without minio_object_path...")

        # Get all other columns except minio_object_path
        other_cols = [col for col in columns.keys() if col != 'minio_object_path']
        cols_str = ', '.join(other_cols)

        # Recreate table
        cursor.execute(f"""
            CREATE TABLE transcriptions_backup AS
            SELECT {cols_str} FROM transcriptions
        """)
        cursor.execute("DROP TABLE transcriptions")
        cursor.execute(f"ALTER TABLE transcriptions_backup RENAME TO transcriptions")

        # Recreate all indexes (except the MinIO one)
        cursor.execute("""
            SELECT name, sql FROM sqlite_master
            WHERE type='index'
            AND tbl_name='transcriptions'
            AND name NOT LIKE 'sqlite_%'
        """)
        indexes = cursor.fetchall()
        for idx_name, idx_sql in indexes:
            if idx_name != 'ix_transcriptions_minio_object_path' and idx_sql:
                print(f"  - Recreating index {idx_name}...")
                cursor.execute(idx_sql)

        # Mark migration as not run
        print("  - Updating alembic version...")
        cursor.execute("""
            UPDATE alembic_version
            SET version_num = 'd304647e9bc3'
            WHERE version_num = '005_add_minio_object_storage'
        """)

        conn.commit()
        print("\n✅ Rollback complete! You can now run 'alembic upgrade head' again.")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
