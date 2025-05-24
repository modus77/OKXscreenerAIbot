import os
import sys
import asyncio
import logging
from pathlib import Path
import aiohttp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
from selenium.webdriver.common.by import By
import shutil
from datetime import datetime, timedelta
import chromedriver_autoinstaller
import httpx
import openai
import sentry_sdk
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import signal
from telegram.health import app, BOT_MESSAGES, BOT_ERRORS

# Configure Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger.add(
    "/data/bot.log",
    rotation="500 MB",
    retention="10 days",
    compression="zip",
    level=os.getenv("LOG_LEVEL", "INFO"),
)

# Add project root to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv
from backend.services.price_comparator_service import PriceComparatorService
from backend.ai.alpha_insight_service import AlphaInsightService
from backend.services.price_history import PriceHistoryService

# Load environment variables
load_dotenv()

# Get bot token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set in .env file")
    sys.exit(1)

# Create necessary directories
CHARTS_DIR = Path("/data/charts")
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# Services
price_service = PriceComparatorService()
ai_service = AlphaInsightService()
history_service = PriceHistoryService()

# User data storage
user_data = {}

# List of supported OKX tokens (lowercase)
OKX_SUPPORTED_TOKENS = [
    "jup", "moodeng", "pnut", "pyth", "wif"
]

# Add this near the top of the file, after imports and before any handlers
DISCLAIMER = ("\n____\n"
    "⚠️ Disclaimer: This AI insight is for informational purposes only and does not constitute financial advice. "
    "Always DYOR (Do Your Own Research) before making any investment decisions. Trading crypto assets involves significant risk.")

# Main menu keyboard
def get_main_keyboard():
    keyboard = [
        [KeyboardButton(text="🔁 Refresh"), KeyboardButton(text="📊 Top Arbitrage")],
        [KeyboardButton(text="⚙️ Settings"), KeyboardButton(text="🧠 AI Insight")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Settings keyboard
def get_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(text="📈 Spread Threshold", callback_data="settings_threshold"),
            InlineKeyboardButton(text="🧪 Test Signal", callback_data="test_signal")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def cleanup_old_charts(max_age_hours=24):
    """Clean up charts older than max_age_hours."""
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    for chart_file in CHARTS_DIR.glob("*.png"):
        if datetime.fromtimestamp(chart_file.stat().st_mtime) < cutoff_time:
            chart_file.unlink()

def ensure_charts_dir():
    """Ensure charts directory exists and is writable."""
    try:
        CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        # Test if directory is writable
        test_file = CHARTS_DIR / ".test"
        test_file.touch()
        test_file.unlink()
        return True
    except Exception as e:
        logger.error(f"Error creating/accessing charts directory: {e}")
        return False

def screenshot_okx_chart(url, out_file=None):
    """Takes a screenshot of the OKX chart (TradingView chart only)."""
    if not ensure_charts_dir():
        logger.error("Cannot access charts directory")
        return False

    try:
        # Generate unique filename with timestamp if not provided
        if out_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_file = f"chart_{timestamp}.png"
        
        # Ensure out_file is just the filename, not a full path
        out_file = Path(out_file).name
        full_path = CHARTS_DIR / out_file

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Disable unnecessary features
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-webrtc")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-geolocation")
        # Reduce network errors
        options.add_argument("--dns-prefetch-disable")
        options.add_argument("--no-proxy-server")
        options.add_argument("--disable-web-security")
        # Set user agent
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)
            time.sleep(12)  # Wait for the page to load

            # Find all iframes
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            found = False
            for iframe in iframes:
                name = iframe.get_attribute("name") or ""
                id_ = iframe.get_attribute("id") or ""
                src = iframe.get_attribute("src") or ""
                if "tradingview" in name or "tradingview" in id_ or "tradingview" in src:
                    driver.switch_to.frame(iframe)
                    time.sleep(2)
                    try:
                        # Try to find the chart div
                        chart = driver.find_element(By.CSS_SELECTOR, ".chart-container, .tv-lightweight-charts, .tradingview-widget-container")
                        chart.screenshot(str(full_path))
                    except Exception:
                        # If the div is not found, screenshot the entire iframe
                        driver.save_screenshot(str(full_path))
                    found = True
                    break

            if not found:
                raise Exception("TradingView chart iframe not found!")

            # Verify the file was created
            if not full_path.exists():
                raise Exception(f"Screenshot file was not created: {full_path}")

            return str(full_path)
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
        finally:
            driver.quit()
    except Exception as e:
        logger.error(f"Error in screenshot process: {e}")
        return None

# Utility functions
def format_volume(vol):
    """Format volume with appropriate suffix (K, M)."""
    if vol >= 1_000_000:
        return f"${vol/1_000_000:.1f}M"
    elif vol >= 1_000:
        return f"${vol/1_000:.1f}K"
    else:
        return f"${vol:.1f}"

def get_user_id(message_or_callback):
    """Extract user_id from message or callback query."""
    if hasattr(message_or_callback, 'from_user') and hasattr(message_or_callback.from_user, 'id'):
        return message_or_callback.from_user.id
    elif hasattr(message_or_callback, 'chat') and hasattr(message_or_callback.chat, 'id'):
        return message_or_callback.chat.id
    return None

def get_okx_trading_url(symbol):
    """Generate OKX trading URL for a symbol."""
    return f"https://www.okx.com/trade-spot/{symbol.lower()}-usdc"

async def safe_delete_message(bot, chat_id, message_id):
    """Safely delete a message with error handling."""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.warning(f"Could not delete message: {e}")

def format_price_message(data, include_insight=False):
    """Format price message with all details."""
    spread_emoji = "🔺" if data['spread_pct'] > 0 else "🔻"
    trend_emoji = "📈" if data.get('trend', 0) > 0 else "📉"
    trend_str = f" | {trend_emoji} <b>24h:</b> {data.get('trend', 0):+.2f}%" if data.get('trend') is not None else ""
    
    okx_link = get_okx_trading_url(data['token'])
    time_str = data['timestamp'].split()[1] + " (UTC)"
    
    message = (
        f"💥 <b>Token: {data['token']}</b>\n"
        f"💰 <b>Price:</b> CEX: <code>${data['price_cex']:.4f}</code> | DEX: <code>${data['price_dex']:.4f}</code>\n"
        f"📊 <b>Spread:</b> <u>{data['spread_pct']:+.2f}%</u> {spread_emoji}{trend_str}\n"
        f"📦 <b>Volume:</b> OKX: {format_volume(data['volume_cex'])} | JUP: {format_volume(data['volume_dex'])}\n"
        f"🕒 {time_str}\n"
    )
    
    if include_insight and 'insight' in data:
        message += f"{data['insight']}\n"
    
    message += f"👉 <a href='{okx_link}'>Trade on OKX</a>\n"
    message += f"{'─' * 40}\n\n"
    
    return message

# Create bot instance at module level for global access
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Message counter middleware
async def message_counter_middleware(handler, event, data):
    """Middleware to count bot messages"""
    BOT_MESSAGES.inc()
    return await handler(event, data)

# Error handler
@dp.error()
async def error_handler(update: types.Update, exception: Exception) -> bool:
    BOT_ERRORS.inc()
    logger.exception(f"Error handling update {update}: {exception}")
    sentry_sdk.capture_exception(exception)
    return True

# Graceful shutdown handler
async def shutdown(dispatcher: Dispatcher):
    logger.info("Shutting down...")
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()
    session = await dispatcher.bot.get_session()
    if session:
        await session.close()

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}")
    asyncio.create_task(shutdown(dp))

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Message handlers
async def send_welcome(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {
            'notify_enabled': True,
            'spread_threshold': 1.0,
            'mode': 'safe'
        }
    await message.answer(
        f"👋 Welcome to OKX Screener AI bot, {message.from_user.first_name}!\n\n"
        f"I provide real-time trading signals based on price spreads between OKX (CEX) and Jupiter (DEX), "
        f"with AI-powered insights to help you make better trading decisions.\n\n"
        f"Use the menu below or type /help to see all commands.",
        reply_markup=get_main_keyboard()
    )

async def refresh_now(message: Message):
    user_id = get_user_id(message)
    tracked_tokens = user_data.get(user_id, {}).get('tracked_tokens', set(price_service.tokens.keys()))
    await message.answer("🔄 Analyzing market opportunities...")
    results = []
    for symbol in tracked_tokens:
        try:
            data = await price_service.compare(symbol)
            if data.get('is_valid'):
                insight = await ai_service.get_insight(
                    price_cex=data['price_cex'],
                    price_dex=data['price_dex'],
                    spread=data['spread_pct'],
                    token=symbol,
                    volume=data.get('volume_dex', 0),
                    slippage=data.get('slippage', 0),
                    trend=data.get('trend', 0),
                    detailed=False
                )
                data['insight'] = insight
                results.append(data)
        except Exception as e:
            logger.error(f"Error for {symbol}: {e}")
            continue

    if not results:
        await message.answer("No valid arbitrage opportunities found.")
        return

    results.sort(key=lambda x: abs(x['spread_pct']), reverse=True)
    text = ""
    for result in results:
        text += format_price_message(result, include_insight=True)
    
    text += DISCLAIMER
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

async def show_token_selection(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {'tracked_tokens': set(price_service.tokens.keys())}
    
    keyboard = []
    for symbol in sorted(price_service.tokens.keys()):
        is_tracked = symbol.upper() in user_data[user_id].get('tracked_tokens', set())
        emoji = "✅" if is_tracked else "⭕️"
        keyboard.append([InlineKeyboardButton(
            text=f"{emoji} {symbol}",
            callback_data=f"toggle_{symbol}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="« Back to Settings", callback_data="back_to_settings")])
    
    await callback_query.answer()
    await callback_query.message.answer(
        "📋 <b>Select Tokens to Track</b>\n\n"
        "✅ - Token is being tracked\n"
        "⭕️ - Token is not tracked\n\n"
        "Click on a token to toggle tracking:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )

# Notifications button handler
@dp.message(F.text == "🔔 Notifications")
async def notifications(message: Message):
    user_id = get_user_id(message)
    if user_id is None:
        return
    if user_id not in user_data:
        user_data[user_id] = {'notify_enabled': False}
    status = "ON" if user_data[user_id]['notify_enabled'] else "OFF"
    keyboard = [[
        InlineKeyboardButton(text=f"Turn {status}", callback_data=f"notify_toggle_{status.lower()}")
    ]]
    await message.answer(
        f"🔔 Notifications are currently {status}\n"
        f"Toggle notifications to receive alerts about significant price spreads.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

# Settings button handler
@dp.message(F.text == "⚙️ Settings")
async def settings(message: Message):
    if hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
        user_id = message.from_user.id
    elif hasattr(message, 'chat') and hasattr(message.chat, 'id'):
        user_id = message.chat.id
    else:
        user_id = None
    if user_id is None:
        return
    if user_id not in user_data:
        user_data[user_id] = {
            'spread_threshold': 1.0,
            'notify_enabled': True,  # Default ON
            'tracked_tokens': set(price_service.tokens.keys())
        }
    notify_status = "ON" if user_data[user_id].get('notify_enabled', False) else "OFF"
    keyboard = [
        [
            InlineKeyboardButton(text=f"🔔 {notify_status}", callback_data="toggle_notify"),
            InlineKeyboardButton(text=f"📈 {user_data[user_id].get('spread_threshold', 1.0)}%", callback_data="settings_threshold")
        ],
        [InlineKeyboardButton(text="📋 Select Tokens", callback_data="select_tokens")],
        [InlineKeyboardButton(text="ℹ️ About", callback_data="show_about")]
    ]
    await message.answer(
        "⚙️ <b>Settings</b>\n\n"
        "Configure your preferences:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )

# Token toggle handler
@dp.callback_query(lambda c: c.data.startswith('toggle_'))
async def process_token_toggle(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {'tracked_tokens': set(price_service.tokens.keys())}
    
    if callback_query.data == 'toggle_notify':
        # Toggle notifications
        current_state = user_data[user_id].get('notify_enabled', False)
        user_data[user_id]['notify_enabled'] = not current_state
        new_state = "ON" if not current_state else "OFF"
        await callback_query.answer(
            f"Notifications turned {new_state}"
        )
        await settings(callback_query.message)
    else:
        # Toggle token
        symbol = callback_query.data.split('_')[1].upper()
        if 'tracked_tokens' not in user_data[user_id]:
            user_data[user_id]['tracked_tokens'] = set(price_service.tokens.keys())
        
        if symbol in user_data[user_id]['tracked_tokens']:
            user_data[user_id]['tracked_tokens'].remove(symbol)
            await callback_query.answer(
                f"Stopped tracking {symbol}"
            )
        else:
            user_data[user_id]['tracked_tokens'].add(symbol)
            await callback_query.answer(
                f"Started tracking {symbol}"
            )
        
        # Refresh token selection menu
        await show_token_selection(callback_query)

# Spread threshold settings handler
@dp.callback_query(lambda c: c.data == "settings_threshold")
async def spread_threshold(callback_query: CallbackQuery):
    thresholds = [0.5, 1.0, 2.0, 3.0, 5.0]
    keyboard = []
    for threshold in thresholds:
        keyboard.append([InlineKeyboardButton(
            text=f"{threshold}%",
            callback_data=f"threshold_{threshold}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="« Back", callback_data="back_to_settings")])
    
    await callback_query.answer()
    await callback_query.message.answer(
        "Select spread threshold:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

# Back to settings handler
@dp.callback_query(lambda c: c.data == "back_to_settings")
async def back_to_settings(callback_query: CallbackQuery):
    await callback_query.answer()
    await settings(callback_query.message)

# Threshold selection handler
@dp.callback_query(lambda c: c.data.startswith("threshold_"))
async def set_threshold(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    threshold = float(callback_query.data.split("_")[1])
    
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['spread_threshold'] = threshold
    
    await callback_query.answer(
        f"Spread threshold set to {threshold}%"
    )
    await back_to_settings(callback_query)

# Test signal handler
@dp.callback_query(lambda c: c.data == "test_signal")
async def test_signal(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer(
        "💡 Example signal:\n\n"
        "Token: $WIF\n"
        "DEX: $1.35 (Vol: $12,000)\n"
        "CEX: $1.30 (Vol: $15,000)\n"
        "📈 Spread: +3.8%\n"
        "💬 DEX price sharply increased — pump in progress."
    )

# Notification toggle handler
@dp.callback_query(lambda c: c.data.startswith("notify_toggle_"))
async def toggle_notifications(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    current_state = callback_query.data.split("_")[-1]
    new_state = "off" if current_state == "on" else "on"
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['notify_enabled'] = (new_state == "on")
    # After toggling, show the settings menu with the correct user_id
    await callback_query.answer()
    await settings(callback_query)

# /help command handler
async def help_command(message: Message):
    help_text = (
        "🤖 <b>OKX Screener AI bot Commands</b>\n\n"
        "/start - Start interaction with the bot and show menu\n"
        "/help - Show this help message\n"
        "\nYou can also use the menu buttons for quick access to common functions."
    )
    await message.answer(help_text, parse_mode="HTML")

# Trading Signals button handler
async def trading_signals(message: Message):
    await message.answer(
        "📊 Trading Signals\n\n"
        "Use /signal <asset> to get a specific trading signal or use /signals to view recent signals.\n\n"
        "Example: /signal BTC"
    )

# Crypto Prices button handler
async def crypto_prices(message: Message):
    await message.answer(
        "💰 Crypto Prices\n\n"
        "Use /price <symbol> to get the current price of a token.\n\n"
        "Example: /price BTC"
    )

# Analyze Token button handler
async def analyze_token(message: Message):
    await message.answer(
        "🔍 Analyze Token\n\n"
        "Use /analyze <symbol> to get an AI-powered analysis of a token's prospects.\n\n"
        "Example: /analyze ETH"
    )

# Solana Explorer button handler
async def solana_explorer(message: Message):
    await message.answer(
        "🌐 Solana Explorer\n\n"
        "Use /solana <address> to get information about a Solana token by its mint address.\n\n"
        "Example: /solana EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    )

# /alpha command handler (Top-3 signals with AI analysis)
async def alpha_command(message: Message):
    await message.answer("🔍 Analyzing market opportunities...")
    results = []
    for symbol in ["WIF", "JUP", "PYTH", "PNUT", "MOODENG"]:
        try:
            data = await price_service.compare(symbol)
            if data.get('is_valid'):
                insight = await ai_service.get_insight(
                    price_cex=data['price_cex'],
                    price_dex=data['price_dex'],
                    spread=data['spread_pct'],
                    token=symbol,
                    volume=data.get('volume_dex', 0),
                    slippage=data.get('slippage', 0),
                    trend=data.get('trend', 0)
                )
                data['insight'] = insight
                results.append(data)
        except Exception as e:
            logger.error(f"Error for {symbol}: {e}")
            continue
    if not results:
        await message.answer("No valid arbitrage opportunities found.")
        return
    results.sort(key=lambda x: abs(x['spread_pct']), reverse=True)
    text = "🔥 Top-3 Arbitrage Opportunities\n\n"
    for result in results[:3]:
        text += (
            f"📊 <b>{result['token']}</b>\n"
            f"CEX (OKX): ${result['price_cex']:.4f} (Vol: ${result.get('volume_cex', 0):,.0f})\n"
            f"DEX ({result['source']}): ${result['price_dex']:.4f} (Vol: ${result.get('volume_dex', 0):,.0f})\n"
            f"Spread: {result['spread_pct']:+.2f}%\n"
            f"Slippage: {result.get('slippage', 0):.2f}%\n"
            f"24h Trend: {result.get('trend', 0):+.2f}%\n\n"
            f"🤖 <i>{result.get('insight', 'No AI analysis available')}</i>\n\n"
        )
    text += DISCLAIMER
    await message.answer(text, parse_mode="HTML")

# Callback for 'More' button
async def process_alpha_more(callback_query: CallbackQuery):
    symbol = callback_query.data.split('_')[-1]
    try:
        data = await price_service.compare(symbol)
        insight = await ai_service.get_insight(
            price_cex=data['price_cex'],
            price_dex=data['price_dex'],
            spread=data['spread_pct'],
            token=symbol,
            volume=data.get('volume_dex') or 0,
            trend=0    # Optionally fetch real trend
        )
        await callback_query.answer()
        insight_text = insight + DISCLAIMER
        await callback_query.message.answer(f"AI Insight for <b>{symbol}</b>:\n{insight_text}", parse_mode="HTML")
    except Exception as e:
        await callback_query.answer()
        await callback_query.message.answer(f"Error: {e}")

# /token <symbol> command handler (detailed signal, English)
async def token_command(message: Message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.reply("Usage: /token <symbol> (e.g. /token WIF)")
        return
    symbol = parts[1].upper()
    if symbol not in price_service.tokens:
        await message.reply(f"Token {symbol} is not supported.")
        return
    try:
        data = await price_service.compare(symbol)
        if data.get('is_valid'):
            spread_emoji = "🔺" if data['spread_pct'] > 0 else "🔻"
            trend_emoji = "📈" if data.get('trend', 0) > 0 else "📉"
            trend_str = f" | {trend_emoji} <b>24h:</b> {data.get('trend', 0):+.2f}%" if data.get('trend') is not None else ""
            
            def format_volume(vol):
                if vol >= 1_000_000:
                    return f"${vol/1_000_000:.1f}M"
                elif vol >= 1_000:
                    return f"${vol/1_000:.1f}K"
                else:
                    return f"${vol:.1f}"
            
            okx_link = f"https://www.okx.com/trade-spot/{symbol.lower()}-usdc"
            
            text = (
                f"💥 <b>Token: {symbol}</b>\n"
                f"💰 <b>Price:</b> CEX: <code>${data['price_cex']:.4f}</code> | DEX: <code>${data['price_dex']:.4f}</code>\n"
                f"📊 <b>Spread:</b> <u>{data['spread_pct']:+.2f}%</u> {spread_emoji}{trend_str}\n"
                f"📦 <b>Volume:</b> OKX: {format_volume(data['volume_cex'])} | JUP: {format_volume(data['volume_dex'])}\n"
                f"🕒 <i>{data['timestamp'].split()[1]}</i>\n"
                f"👉 <a href='{okx_link}'>Trade on OKX</a>\n"
                f"{'─' * 40}"
            )
        else:
            text = f"💥 <b>Token: {symbol}</b>\nError: {data.get('error')}"
        keyboard = [
            [InlineKeyboardButton(text="📈 History", callback_data=f"history_{symbol}")],
            [InlineKeyboardButton(text="💱 Swap", callback_data=f"swap_{symbol}")]
        ]
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            disable_web_page_preview=True
        )
    except Exception as e:
        await message.reply(f"Error: {e}")

# /set_mode command handler (Safe/Degen mode selection)
from aiogram.types import ReplyKeyboardRemove

async def set_mode_command(message: Message):
    keyboard = [
        [InlineKeyboardButton(text="🧠 Safe mode", callback_data="mode_safe")],
        [InlineKeyboardButton(text="⚔️ Degen mode", callback_data="mode_degen")]
    ]
    await message.answer(
        "Choose your trading style:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

async def process_mode_select(callback_query: CallbackQuery):
    mode = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id]['mode'] = mode
    await callback_query.answer()
    await callback_query.message.answer(f"Trading mode set to: {mode.capitalize()} mode.", reply_markup=ReplyKeyboardRemove())

# /history_<symbol> handler (PNG chart or text summary)
import matplotlib.pyplot as plt
import io

async def history_command(message: Message):
    symbol = message.text.split('_', 1)[-1].upper()
    data = history_service.get_history(symbol)
    if not data:
        await message.reply(f"No history found for {symbol}.")
        return
    # Try to plot PNG chart
    try:
        times = [d['timestamp'] for d in reversed(data)]
        spreads = [d['spread_pct'] for d in reversed(data)]
        plt.figure(figsize=(6,3))
        plt.plot(times, spreads, marker='o')
        plt.title(f"Spread history for {symbol}")
        plt.xlabel("Time")
        plt.ylabel("Spread (%)")
        plt.xticks(rotation=45, fontsize=8)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        await message.reply_photo(buf, caption=f"Spread history for {symbol}")
    except Exception as e:
        # Fallback: text summary
        summary = '\n'.join([
            f"{d['timestamp']}: {d['spread_pct']:+.2f}%"
            for d in data[-10:]
        ])
        await message.reply(f"Recent spread changes for {symbol}:\n{summary}")

# /swap_<symbol> handler (Jupiter/OKX links)
async def swap_command(message: Message):
    symbol = message.text.split('_', 1)[-1].upper()
    if symbol not in price_service.tokens:
        await message.reply(f"Token {symbol} is not supported.")
        return
    # Jupiter swap link (prefilled)
    jupiter_url = f"https://jup.ag/swap/SOL-{symbol}"
    # OKX spot trading link
    okx_url = f"https://www.okx.com/trade-spot/{symbol.lower()}-usdc"
    text = (f"Swap {symbol} on Jupiter: {jupiter_url}\n"
            f"Trade {symbol} on OKX: {okx_url}")
    await message.reply(text)

# /tokens command handler (list supported tokens)
async def tokens_command(message: Message):
    text = "📋 List of supported tokens:\n\n"
    text += "Token | Symbol | Mint\n"
    text += "-------------------\n"
    
    for symbol, (mint, _, _) in price_service.tokens.items():
        # Get token name from database or use symbol as name
        name = symbol  # You might want to get the actual name from your database
        text += f"{name} | {symbol} | {mint}\n"
    
    await message.reply(text)

# /mode command handler (show current mode)
async def mode_command(message: Message):
    mode = user_data.get(message.from_user.id, {'mode': 'safe'})['mode']
    await message.reply(f"Your current trading mode: {mode.capitalize()} mode.")

# /refresh command handler (manual price refresh)
async def refresh_command(message: Message):
    await message.reply("Prices refreshed. Use /alpha or /token <symbol> to see updated signals.")

# /check command handler
async def check_command(message: Message):
    await message.answer("🔍 Scanning for arbitrage opportunities...")
    opportunities = []
    for symbol in price_service.tokens.keys():
        try:
            data = await price_service.compare(symbol)
            if data.get('is_valid') and abs(data['spread_pct']) >= 1.0:
                opportunities.append(data)
            elif not data.get('is_valid'):
                opportunities.append({'symbol': symbol, 'error': data.get('error')})
        except Exception as e:
            logger.error(f"Error checking {symbol}: {e}")
            opportunities.append({'symbol': symbol, 'error': str(e)})
    if not opportunities:
        await message.answer("No arbitrage opportunities found (threshold: 1%)")
        return
    # Sort by absolute spread
    opportunities.sort(key=lambda x: abs(x['spread_pct']), reverse=True)
    text = ""
    for opp in opportunities:
        if 'error' in opp:
            text += f"💥 <b>Token: {opp['symbol']}</b>\nError: {opp['error']}\n\n"
        else:
            spread_emoji = "🔺" if opp['spread_pct'] > 0 else "🔻"
            trend_emoji = "📈" if opp.get('trend', 0) > 0 else "📉"
            trend_str = f" | {trend_emoji} <b>24h:</b> {opp.get('trend', 0):+.2f}%" if opp.get('trend') is not None else ""
            
            # Format volumes
            def format_volume(vol):
                if vol >= 1_000_000:
                    return f"${vol/1_000_000:.1f}M"
                elif vol >= 1_000:
                    return f"${vol/1_000:.1f}K"
                else:
                    return f"${vol:.1f}"
            
            direction = "Buy on OKX → Sell on DEX" if opp['spread_pct'] > 0 else "Buy on DEX → Sell on OKX"
            okx_link = f"https://www.okx.com/trade-spot/{opp['symbol'].lower()}-usdc"
            
            text += (
                f"💥 <b>Token: {opp['symbol']}</b>\n"
                f"💰 <b>Price:</b> CEX: <code>${opp['price_cex']:.4f}</code> | DEX: <code>${opp['price_dex']:.4f}</code>\n"
                f"📊 <b>Spread:</b> <u>{opp['spread_pct']:+.2f}%</u> {spread_emoji}{trend_str}\n"
                f"📦 <b>Volume:</b> OKX: {format_volume(opp['volume_cex'])} | JUP: {format_volume(opp['volume_dex'])}\n"
                f"🕒 <i>{opp['timestamp'].split()[1]}</i>\n"
                f"Route: {direction}\n"
                f"👉 <a href='{okx_link}'>Trade on OKX</a>\n\n"
            )
    await message.answer(text or "No arbitrage opportunities found.", parse_mode="HTML", disable_web_page_preview=True)

# About handler
async def show_about(callback_query: CallbackQuery):
    text = (
        "🤖 <b>OKX Screener AI bot</b>\n\n"
        "Real-time price monitoring and arbitrage opportunities between OKX (CEX) and Jupiter (DEX).\n\n"
        "Supported tokens:\n"
        "• WIF\n"
        "• JUP\n"
        "• PYTH\n"
        "• PNUT\n"
        "• MOODENG\n\n"
        "Features:\n"
        "• Real-time price comparison\n"
        "• Volume monitoring\n"
        "• Spread alerts\n"
        "• Trading signals\n"
        "• Price history\n\n"
        "Use /help to see all available commands."
    )
    await callback_query.answer()
    await callback_query.message.answer(text, parse_mode="HTML")

# Top Arbitrage handler
async def top_arbitrage(message: Message):
    await message.answer("🔍 Scanning for arbitrage opportunities...")
    results = []
    for symbol in OKX_SUPPORTED_TOKENS:
        try:
            data = await price_service.compare(symbol.upper())
            if data.get('is_valid'):
                insight = await ai_service.get_insight(
                    price_cex=data['price_cex'],
                    price_dex=data['price_dex'],
                    spread=data['spread_pct'],
                    token=symbol.upper(),
                    volume=data.get('volume_dex', 0),
                    slippage=data.get('slippage', 0),
                    trend=data.get('trend', 0),
                    detailed=False
                )
                data['insight'] = insight
                results.append(data)
            else:
                results.append({
                    'symbol': symbol.upper(),
                    'error': data.get('error')
                })
        except Exception as e:
            logger.error(f"Error for {symbol}: {e}")
            results.append({'symbol': symbol.upper(), 'error': str(e)})
    # Separate valid and error results
    valid_results = [r for r in results if r.get('is_valid') and 'spread_pct' in r]
    error_results = [r for r in results if not (r.get('is_valid') and 'spread_pct' in r)]
    valid_results.sort(key=lambda x: abs(x['spread_pct']), reverse=True)
    text = "🔥 <b>Top Arbitrage Opportunities</b>\n\n"
    if valid_results:
        for t in valid_results[:3]:
            spread_emoji = "🔺" if t['spread_pct'] > 0 else "🔻"
            trend_emoji = "📈" if t.get('trend', 0) > 0 else "📉"
            trend_str = f" | {trend_emoji} <b>24h:</b> {t.get('trend', 0):+.2f}%" if t.get('trend') is not None else ""
            def format_volume(vol):
                if vol >= 1_000_000:
                    return f"${vol/1_000_000:.1f}M"
                elif vol >= 1_000:
                    return f"${vol/1_000:.1f}K"
                else:
                    return f"${vol:.1f}"
            okx_link = f"https://www.okx.com/trade-spot/{t['token'].lower()}-usdc"
            time_str = t['timestamp'].split()[1] + " (UTC)"
            text += (
                f"💥 <b>Token: {t['token']}</b>\n"
                f"💰 <b>Price:</b> CEX: <code>${t['price_cex']:.4f}</code> | DEX: <code>${t['price_dex']:.4f}</code>\n"
                f"📊 <b>Spread:</b> <u>{t['spread_pct']:+.2f}%</u> {spread_emoji}{trend_str}\n"
                f"📦 <b>Volume:</b> OKX: {format_volume(t['volume_cex'])} | JUP: {format_volume(t['volume_dex'])}\n"
                f"🕒 {time_str}\n"
                f"👉 <a href='{okx_link}'>Trade on OKX</a>\n"
                f"{'─' * 40}\n\n"
            )
    else:
        for t in error_results[:3]:
            symbol = t.get('symbol', 'Unknown')
            text += f"💥 <b>Token: {symbol}</b>\nError: {t.get('error', 'Unknown error')}\n\n"
    text += DISCLAIMER
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

# AI Insight handler
async def ai_insight_start(message: Message):
    keyboard = []
    for symbol in sorted(price_service.tokens.keys()):
        keyboard.append([InlineKeyboardButton(text=symbol, callback_data=f"ai_insight_{symbol}")])
    
    await message.answer(
        "🔍 Select token for deep analysis:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

# AI Insight callback handler
async def process_ai_insight(callback_query: CallbackQuery):
    symbol = callback_query.data.split('_')[-1].lower()
    if symbol not in OKX_SUPPORTED_TOKENS:
        await callback_query.answer()
        await callback_query.message.answer(
            f"❌ No OKX chart or insight available for {symbol.upper()}"
        )
        return

    await callback_query.answer()
    waiting_msg = await callback_query.message.answer(
        f"⏳ Forming deep analysis for {symbol.upper()}...\nThis may take a few seconds."
    )

    try:
        # Get price data first
        data = await price_service.compare(symbol.upper())
        if not data.get('is_valid'):
            await callback_query.message.edit_text(
                f"❌ Error getting data for {symbol.upper()}: {data.get('error')}",
                reply_markup=None
            )
            return

        # Generate unique filename for this screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_filename = f"chart_{symbol}_{timestamp}.png"
        chart_path = screenshot_okx_chart(get_okx_trading_url(symbol), out_file=chart_filename)
        
        if chart_path:
            await safe_delete_message(bot, callback_query.from_user.id, waiting_msg.message_id)
            
            # Create FSInputFile instance for the photo
            photo = FSInputFile(chart_path)
            await callback_query.message.answer_photo(
                photo,
                caption=f"📊 OKX Chart for {symbol.upper()}"
            )
            # Clean up the chart file after sending
            try:
                Path(chart_path).unlink()
            except Exception as e:
                logger.warning(f"Could not delete chart file {chart_path}: {e}")
        else:
            await safe_delete_message(bot, callback_query.from_user.id, waiting_msg.message_id)
            await callback_query.message.answer(
                f"❌ Could not get OKX chart for {symbol.upper()}"
            )
            return

        # Get AI insight with actual data
        insight = await ai_service.get_insight(
            price_cex=data['price_cex'],
            price_dex=data['price_dex'],
            spread=data['spread_pct'],
            token=symbol.upper(),
            volume=data.get('volume_dex', 0),
            slippage=data.get('slippage', 0),
            trend=data.get('trend', 0),
            detailed=True
        )

        keyboard = [
            [
                InlineKeyboardButton(text="💱 Trade on OKX", url=get_okx_trading_url(symbol)),
                InlineKeyboardButton(text="« Back", callback_data="ai_back_to_tokens")
            ]
        ]

        # Format the message with disclaimer
        message_text = (
            f"{insight}\n\n"
            f"{DISCLAIMER}"
        )

        await callback_query.message.answer(
            message_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

    except Exception as e:
        logger.error(f"Error in AI insight for {symbol.upper()}: {e}")
        try:
            await callback_query.message.edit_text(
                f"❌ Error in AI analysis for {symbol.upper()}: {str(e)}",
                reply_markup=None
            )
        except Exception as edit_error:
            logger.error(f"Could not edit error message: {edit_error}")
            await callback_query.message.answer(
                f"❌ Error in AI analysis for {symbol.upper()}: {str(e)}"
            )

# AI Insight back button handler
async def ai_back_to_tokens(callback_query: CallbackQuery):
    keyboard = []
    for symbol in sorted(price_service.tokens.keys()):
        keyboard.append([InlineKeyboardButton(text=symbol, callback_data=f"ai_insight_{symbol}")])
    await callback_query.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

def normalize_symbol(symbol: str) -> str:
    """Normalizes the token symbol for use in URLs."""
    return symbol.lower()

async def chart_command(message: Message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer("Usage: /chart SYMBOL")
            return
        symbol = parts[1].lower()
        if symbol not in OKX_SUPPORTED_TOKENS:
            await message.answer(f"❌ No OKX chart available for {symbol.upper()}")
            return
        pair_url = await get_okx_pair(symbol)
        await message.answer(f"🔍 Looking for {symbol.upper()}/USDC pair on OKX...")
        
        # Generate unique filename for this screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_file = CHARTS_DIR / f"chart_{symbol}_{timestamp}.png"
        
        if screenshot_okx_chart(pair_url, out_file=chart_file):
            with open(chart_file, "rb") as photo:
                await message.answer_photo(photo, caption=f"📊 OKX Chart for {symbol.upper()}")
            # Clean up the chart file after sending
            try:
                chart_file.unlink()
            except Exception as e:
                logger.warning(f"Could not delete chart file {chart_file}: {e}")
        else:
            await message.answer(f"❌ Could not get OKX chart for {symbol.upper()}")
    except Exception as e:
        logger.error(f"Error in chart command: {e}")
        await message.answer("Error getting chart.")

async def get_okx_pair(symbol: str) -> str:
    """Get the OKX trading pair URL for a given symbol."""
    return f"https://www.okx.com/trade-spot/{symbol.lower()}-usdc"

# Start the bot
async def main():
    # Initialize bot and dispatcher
    dp = Dispatcher()

    # Add middleware
    dp.message.middleware(message_counter_middleware)

    # Register message handlers
    dp.message.register(send_welcome, Command(commands=["start"]))
    dp.message.register(help_command, Command(commands=["help"]))
    dp.message.register(alpha_command, Command(commands=["alpha"]))
    dp.message.register(tokens_command, Command(commands=["tokens"]))
    dp.message.register(mode_command, Command(commands=["mode"]))
    dp.message.register(refresh_command, Command(commands=["refresh"]))
    dp.message.register(check_command, Command(commands=["check"]))
    dp.message.register(chart_command, Command(commands=["chart"]))
    dp.message.register(set_mode_command, Command(commands=["set_mode"]))
    dp.message.register(token_command, lambda msg: msg.text and msg.text.lower().startswith('/token'))
    dp.message.register(history_command, lambda msg: msg.text and msg.text.lower().startswith('/history_'))
    dp.message.register(swap_command, lambda msg: msg.text and msg.text.lower().startswith('/swap_'))

    # Register text handlers
    dp.message.register(refresh_now, F.text == "🔁 Refresh")
    dp.message.register(trading_signals, F.text == "📊 Trading Signals")
    dp.message.register(crypto_prices, F.text == "💰 Crypto Prices")
    dp.message.register(analyze_token, F.text == "🔍 Analyze Token")
    dp.message.register(solana_explorer, F.text == "🌐 Solana Explorer")
    dp.message.register(top_arbitrage, F.text == "📊 Top Arbitrage")
    dp.message.register(ai_insight_start, F.text == "🧠 AI Insight")
    dp.message.register(notifications, F.text == "🔔 Notifications")
    dp.message.register(settings, F.text == "⚙️ Settings")

    # Register callback query handlers
    dp.callback_query.register(show_token_selection, F.data == "select_tokens")
    dp.callback_query.register(process_token_toggle, lambda c: c.data and c.data.startswith('toggle_'))
    dp.callback_query.register(spread_threshold, F.data == "settings_threshold")
    dp.callback_query.register(back_to_settings, F.data == "back_to_settings")
    dp.callback_query.register(set_threshold, lambda c: c.data and c.data.startswith("threshold_"))
    dp.callback_query.register(test_signal, F.data == "test_signal")
    dp.callback_query.register(toggle_notifications, lambda c: c.data and c.data.startswith("notify_toggle_"))
    dp.callback_query.register(process_alpha_more, lambda c: c.data and c.data.startswith('alpha_more_'))
    dp.callback_query.register(process_mode_select, lambda c: c.data and c.data.startswith('mode_'))
    dp.callback_query.register(show_about, F.data == "show_about")
    dp.callback_query.register(process_ai_insight, lambda c: c.data and c.data.startswith('ai_insight_'))
    dp.callback_query.register(ai_back_to_tokens, F.data == "ai_back_to_tokens")

    try:
        # Start FastAPI app in background
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        api_task = asyncio.create_task(server.serve())

        # Start bot polling
        chromedriver_autoinstaller.install()
        logger.info('Starting bot...')
        logger.info(f'httpx version: {httpx.__version__}')
        logger.info(f'openai version: {openai.__version__}')
        
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Error in main loop")
        sentry_sdk.capture_exception(e)
        raise
    finally:
        await shutdown(dp)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
