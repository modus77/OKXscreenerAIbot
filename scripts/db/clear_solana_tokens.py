import os
import sys
import sqlite3
from pathlib import Path

# Add project root to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database path from environment variables
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("ERROR: DATABASE_URL not set in .env file")
    sys.exit(1)

db_path = db_url.replace("sqlite:///", "")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Remove all Solana tokens from the database
deleted = cursor.execute("DELETE FROM solana_tokens").rowcount
conn.commit()
conn.close()

print(f"Removed {deleted} Solana tokens from the database.")
