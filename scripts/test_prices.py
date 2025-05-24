import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from backend.services.price_comparator_service import PriceComparatorService
from backend.ai.alpha_insight_service import AlphaInsightService

async def test_prices():
    price_service = PriceComparatorService()
    ai_service = None
    if os.getenv("OPENAI_API_KEY"):
        ai_service = AlphaInsightService()
    tokens = list(price_service.tokens.keys())
    print("🔍 Testing real-time prices...")
    print("\nSupported tokens:", ", ".join(tokens))
    summary = []
    for symbol in tokens:
        print(f"\n📊 Testing {symbol}...")
        try:
            result = await price_service.compare(symbol)
            if result and result.get('is_valid'):
                print(f"✅ {symbol} prices:")
                print(f"  CEX (OKX): ${result['price_cex']:.4f} (Vol: {result.get('volume_cex')})")
                print(f"  DEX (Jupiter): ${result['price_dex']:.4f} (Vol: {result.get('volume_dex')})")
                print(f"  Spread: {result['spread_pct']:+.4f}%")
                print(f"  Source DEX: {result.get('source_dex')}")
                print(f"  Timestamp: {result.get('timestamp')}")
                # AI insight
                if ai_service:
                    ai_comment = await ai_service.get_insight(
                        price_cex=result['price_cex'],
                        price_dex=result['price_dex'],
                        spread=result['spread_pct'],
                        token=symbol,
                        volume=result.get('volume_dex') or 0,
                        trend=0
                    )
                    print(f"  AI Insight: {ai_comment}")
                summary.append((symbol, result['spread_pct'], True, None))
            else:
                print(f"❌ Error getting {symbol} prices:", result.get("error", "Unknown error"))
                print(f"  is_valid: {result.get('is_valid')}  error_message: {result.get('error_message')}")
                summary.append((symbol, None, False, result.get('error', 'Unknown error')))
        except Exception as e:
            print(f"❌ Error testing {symbol}:", str(e))
            summary.append((symbol, None, False, str(e)))
    print("\n===== SUMMARY =====")
    for symbol, spread, ok, err in summary:
        if ok:
            print(f"{symbol}: OK, spread={spread:+.4f}%")
        else:
            print(f"{symbol}: ERROR, {err}")

if __name__ == "__main__":
    asyncio.run(test_prices()) 