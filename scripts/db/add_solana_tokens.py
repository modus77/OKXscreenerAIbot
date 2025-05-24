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

# Extract database file path from URL
db_path = db_url.replace("sqlite:///", "")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Clear existing tokens
cursor.execute("DELETE FROM solana_tokens")

# New list of tokens with their mint addresses
tokens = [
    ("WIF", "Dogwifhat", "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm", 6),
    ("BONK", "Bonk", "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", 5),
    ("JUP", "Jupiter", "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN", 6),
    ("PYTH", "Pyth Network", "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3", 6),
    ("JTO", "Jito", "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL", 6),
    ("PNUT", "Peanut the Squirrel", "2qEHjDLDLbuBgRYvsxhc5D6uDWAivNFZGan56P1tpump", 6),
    ("DOGE", "Dogecoin", "9TY6DUg1VSssYH5tFE95qoq5hnAGFak4w3cn72sJNCoV", 6),
    ("CATI", "Catizen", "6vrEZV86doP7VB2uqX4th8KB3dbd2QgcQh56RvEPx713", 6),
    ("SHIB", "Shiba Inu", "7wz31sC5z979UMtiqrtxsYYQ6bJzpjUTgPsZvXuZhso", 6),
    ("TURBO", "Turbo", "GzsbQRBskvt1UALGWBEj5cpqddvDPz2QqMysooGxCLRW", 6),
    ("APE", "ApeCoin", "HhWF8y1z23DkAMKjkSauddyQqG7SngEy7yBTmZ8rmoon", 6),
    ("DOGS", "Solana Dogs", "GkUrsDJSKYUbsip2n9ARy9EyNWvfXu4s9mJWRcF1EW1s", 6),
    ("MOODENG", "Moo Deng", "ED5nyyWEzpPPiWimP8vYm7sD7TD3LAt3Q3gRTWHzPJBY", 6)
]

# Insert new tokens
cursor.executemany(
    """
    INSERT INTO solana_tokens (mint_address, symbol, name, decimals)
    VALUES (?, ?, ?, ?)
    """,
    [(mint, symbol, name, decimals) for symbol, name, mint, decimals in tokens]
)

conn.commit()
conn.close()

print("Solana tokens updated successfully")
