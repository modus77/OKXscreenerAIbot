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
db_dir = os.path.dirname(db_path)

# Create database directory if it does not exist
os.makedirs(db_dir, exist_ok=True)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables
cursor.executescript("""
-- Table for tokens
CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    chain TEXT NOT NULL,
    contract_address TEXT,
    decimals INTEGER,
    last_price REAL,
    market_cap REAL,
    volume_24h REAL,
    change_24h REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for Solana tokens
CREATE TABLE IF NOT EXISTS solana_tokens (
    mint_address TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    decimals INTEGER,
    holders INTEGER,
    supply REAL,
    last_price REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for signals
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    direction TEXT CHECK(direction IN ('BUY', 'SELL', 'HOLD')) NOT NULL,
    entry_price REAL,
    target_price REAL,
    stop_loss REAL,
    timeframe TEXT,
    confidence REAL,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for Telegram users
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for token analysis
CREATE TABLE IF NOT EXISTS token_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    sentiment TEXT CHECK(sentiment IN ('BULLISH', 'BEARISH', 'NEUTRAL')) NOT NULL,
    risk_level TEXT CHECK(risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'VERY HIGH')) NOT NULL,
    summary TEXT,
    pros TEXT,
    cons TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Remove old price_history table if it exists
DROP TABLE IF EXISTS price_history;

-- Table for price history
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    price_cex REAL,
    price_dex REAL,
    spread_pct REAL,
    volume_cex FLOAT,
    volume_dex FLOAT,
    source_dex TEXT,
    is_valid BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    timestamp TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (is_valid = FALSE) OR
        (is_valid = TRUE AND price_cex IS NOT NULL AND price_dex IS NOT NULL AND spread_pct IS NOT NULL)
    )
);
""")

conn.commit()
conn.close()

print("Database initialized successfully")
