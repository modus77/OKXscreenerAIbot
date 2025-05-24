"""
Utility for updating Solana token information in the database.

This script retrieves token information from the Helius API and updates
the data in the solana_tokens table.
"""
import os
import sys
import asyncio
import sqlite3
from pathlib import Path

# Add project root to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from backend.services.helius_service import HeliusService

# Load environment variables
load_dotenv()

# Get database path from environment variables
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("ERROR: DATABASE_URL not set in .env file")
    sys.exit(1)

# Extract file path from database URL
db_path = db_url.replace("sqlite:///", "")

async def update_token_info(helius: HeliusService, mint_address: str):
    """
    Updates token information in the database.

    Args:
        helius: HeliusService instance
        mint_address: Solana token mint address
    """
    try:
        # Retrieve token information from Helius API
        token_data = await helius.parse_solana_token(mint_address)

        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Update token data in the database
        cursor.execute("""
        UPDATE solana_tokens 
        SET 
            name = ?,
            symbol = ?,
            decimals = ?,
            holders = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE mint_address = ?
        """, (
            token_data["name"],
            token_data["symbol"],
            token_data["decimals"],
            token_data["holders"],
            mint_address
        ))

        conn.commit()
        conn.close()

        print(f"Updated token: {token_data['symbol']} ({token_data['name']})")
    except Exception as e:
        print(f"Error updating token {mint_address}: {str(e)}")

async def update_all_tokens():
    """
    Updates information for all Solana tokens in the database.
    """
    try:
        # Create HeliusService instance
        helius = HeliusService()

        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Retrieve all tokens from the database
        cursor.execute("SELECT mint_address FROM solana_tokens")
        tokens = cursor.fetchall()
        conn.close()

        # Update information for each token
        for token in tokens:
            mint_address = token[0]
            await update_token_info(helius, mint_address)
            # Add a small delay to comply with rate limit (10 requests per second)
            await asyncio.sleep(0.1)

        print("All tokens updated successfully")
    except Exception as e:
        print(f"Error updating tokens: {str(e)}")

if __name__ == "__main__":
    # Start updating all tokens
    asyncio.run(update_all_tokens())
