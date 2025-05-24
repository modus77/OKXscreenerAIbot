import os
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI
from backend.api.routes import router as api_router

# Импортируем наш сервис Helius
from backend.services.helius import HeliusClient

# Загружаем переменные окружения
load_dotenv()

# Создаем приложение FastAPI
app = FastAPI(
    title="OKX Screener AI bot API",
    description="Cryptocurrency trading assistant API",
    version="0.1.0"
)

app.include_router(api_router, prefix="/api")

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class Token(BaseModel):
    symbol: str
    name: str
    chain: str
    contract_address: Optional[str] = None
    decimals: Optional[int] = None
    last_price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    updated_at: Optional[datetime] = None

class SolanaToken(BaseModel):
    mint_address: str
    symbol: str
    name: str
    decimals: int
    holders: Optional[int] = None
    supply: Optional[float] = None
    last_price: Optional[float] = None
    updated_at: Optional[datetime] = None

class Signal(BaseModel):
    symbol: str
    direction: str  # BUY, SELL, HOLD
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    timeframe: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    created_at: Optional[datetime] = None

class TokenAnalysis(BaseModel):
    symbol: str
    sentiment: str  # BULLISH, BEARISH, NEUTRAL
    risk_level: str  # LOW, MEDIUM, HIGH, VERY HIGH
    summary: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    created_at: Optional[datetime] = None

# Получаем соединение с базой данных
def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not set")
    
    db_path = db_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Маршруты для API
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/tokens", response_model=List[Token])
async def get_tokens():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tokens")
    tokens = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tokens

@app.get("/solana/tokens", response_model=List[SolanaToken])
async def get_solana_tokens():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM solana_tokens")
    tokens = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tokens

@app.get("/solana/token/info/{mint_address}")
async def get_solana_token_info(mint_address: str):
    """
    Получение подробной информации о токене Solana через Helius API.
    
    Args:
        mint_address: Mint-адрес токена Solana
        
    Returns:
        Информация о токене из Helius API
    """
    try:
        # Создаем экземпляр HeliusService
        helius = HeliusClient()
        
        # Получаем информацию о токене
        token_info = await helius.get_token_info(mint_address)
        
        return {
            "status": "success",
            "data": token_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching token info: {str(e)}")

@app.get("/solana/token/holders/{mint_address}")
async def get_solana_token_holders(mint_address: str, limit: int = 10):
    """
    Получение информации о держателях токена Solana.
    
    Args:
        mint_address: Mint-адрес токена Solana
        limit: Максимальное количество держателей
        
    Returns:
        Список держателей токена
    """
    try:
        # Создаем экземпляр HeliusService
        helius = HeliusClient()
        
        # Получаем держателей токена
        holders = await helius.get_token_holders(mint_address, limit=limit)
        
        return {
            "status": "success",
            "data": {
                "mint_address": mint_address,
                "total_holders": len(holders),
                "holders": holders
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching token holders: {str(e)}")

@app.post("/solana/token/update/{mint_address}")
async def update_solana_token(mint_address: str):
    """
    Обновление информации о токене Solana в базе данных.
    
    Args:
        mint_address: Mint-адрес токена Solana
        
    Returns:
        Результат обновления
    """
    try:
        # Создаем экземпляр HeliusService
        helius = HeliusClient()
        
        # Получаем информацию о токене
        token_data = await helius.parse_solana_token(mint_address)
        
        # Подключаемся к базе данных
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем, существует ли токен в базе
        cursor.execute("SELECT * FROM solana_tokens WHERE mint_address = ?", (mint_address,))
        existing_token = cursor.fetchone()
        
        if existing_token:
            # Обновляем существующий токен
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
        else:
            # Добавляем новый токен
            cursor.execute("""
            INSERT INTO solana_tokens (mint_address, symbol, name, decimals, holders, supply, last_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                token_data["mint_address"],
                token_data["symbol"],
                token_data["name"],
                token_data["decimals"],
                token_data["holders"],
                token_data["supply"],
                token_data["last_price"]
            ))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Token {token_data['symbol']} updated successfully",
            "data": token_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating token: {str(e)}")

@app.get("/signals/recent", response_model=List[Signal])
async def get_recent_signals(limit: int = 10):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM signals ORDER BY created_at DESC LIMIT ?", (limit,))
    signals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return signals

# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
