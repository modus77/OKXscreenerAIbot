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

# Извлекаем путь к файлу базы данных из URL
db_path = db_url.replace("sqlite:///", "")

# Подключаемся к базе данных
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Получаем все записи из таблицы solana_tokens
cursor.execute("SELECT * FROM solana_tokens")
tokens = cursor.fetchall()

# Выводим информацию о токенах
print("Solana tokens in the database:")
print("-" * 60)
print(f"{'Symbol':<10} {'Name':<20} {'Mint Address':<45}")
print("-" * 60)
for token in tokens:    print(f"{token['symbol']:<10} {token['name']:<20} {token['mint_address']}")
print("-" * 60)

conn.close()

# Пауза для просмотра результатов
input("Press Enter to exit...")
