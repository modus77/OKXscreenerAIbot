import sqlite3
from typing import List, Dict, Any
from datetime import datetime
import os

DB_PATH = os.getenv("DATABASE_URL", "backend/db/mipilot.db").replace("sqlite:///", "")

class PriceHistoryService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def save(self, symbol: str, price_cex: float, price_dex: float, spread_pct: float, timestamp: datetime = None,
             volume_cex: float = None, volume_dex: float = None, source_dex: str = None,
             is_valid: bool = True, error_message: str = None):
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        spread_pct = round(spread_pct, 4) if spread_pct is not None else None
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO price_history (symbol, price_cex, price_dex, spread_pct, volume_cex, volume_dex, source_dex, is_valid, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (symbol, price_cex, price_dex, spread_pct, volume_cex, volume_dex, source_dex, int(is_valid), error_message, timestamp)
            )
            conn.commit()

    def get_history(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                SELECT symbol, price_cex, price_dex, spread_pct, volume_cex, volume_dex, source_dex, is_valid, error_message, timestamp, created_at
                FROM price_history
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (symbol, limit)
            )
            rows = cur.fetchall()
        # Return as list of dicts, most recent first
        return [
            {
                "symbol": row[0],
                "price_cex": row[1],
                "price_dex": row[2],
                "spread_pct": row[3],
                "volume_cex": row[4],
                "volume_dex": row[5],
                "source_dex": row[6],
                "is_valid": bool(row[7]),
                "error_message": row[8],
                "timestamp": row[9],
                "created_at": row[10],
            }
            for row in rows
        ]
