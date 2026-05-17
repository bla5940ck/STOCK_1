"""
Initialize database from command line.
"""

import asyncio
import sys
from src.db.database import init_db_sync


def main():
    """Initialize database"""
    try:
        init_db_sync()
        print("✅ Database initialization complete!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
