"""
Quick script to update existing transcriptions with default category
"""
import sys
from sqlalchemy import create_engine, text

# Database URL
DATABASE_URL = "sqlite:////data/echonote.db"

def main():
    print("Connecting to database...")
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Update all transcriptions with NULL or empty category
        result = conn.execute(
            text("UPDATE transcriptions SET category = 'voice_memo' WHERE category IS NULL OR category = ''")
        )
        conn.commit()

        print(f"Updated {result.rowcount} transcriptions with default category 'voice_memo'")

        # Verify
        result = conn.execute(text("SELECT COUNT(*) FROM transcriptions WHERE category IS NULL OR category = ''"))
        null_count = result.scalar()
        print(f"Remaining transcriptions with NULL/empty category: {null_count}")

        # Show sample
        result = conn.execute(text("SELECT id, category FROM transcriptions LIMIT 5"))
        print("\nSample transcriptions:")
        for row in result:
            print(f"  ID {row[0]}: category={row[1]}")

    print("\nDone!")

if __name__ == "__main__":
    main()
