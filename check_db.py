#!/usr/bin/env python3
"""
Check database tables.
"""

from app.core.database import engine
from sqlalchemy import text

def check_tables():
    """Check if account_deletion_requests table exists."""
    
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'account_deletion_requests'"
        ))
        table_exists = bool(result.fetchone())
        print(f"account_deletion_requests table exists: {table_exists}")
        
        # List all tables
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
        ))
        tables = [row[0] for row in result.fetchall()]
        print(f"All tables: {tables}")

if __name__ == "__main__":
    check_tables()
