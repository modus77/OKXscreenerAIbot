# FastAPI routes for OKX Screener AI bot API
from fastapi import APIRouter
from backend.services.price_comparator_service import PriceComparatorService
from backend.ai.alpha_insight_service import AlphaInsightService
from backend.services.price_history import PriceHistoryService

router = APIRouter()

price_service = PriceComparatorService()
ai_service = AlphaInsightService()
history_service = PriceHistoryService()

@router.get("/spreads", summary="Get spreads for all supported tokens")
async def get_spreads():
    results = []
    for symbol in price_service.tokens.keys():
        try:
            data = await price_service.compare(symbol)
            if 'spread_pct' in data:
                results.append({
                    'symbol': symbol,
                    'spread_pct': data['spread_pct'],
                    'price_cex': data['price_cex'],
                    'price_dex': data['price_dex']
                })
        except Exception:
            continue
    return sorted(results, key=lambda x: abs(x['spread_pct']), reverse=True)

@router.get("/insight/{symbol}", summary="Get AI insight for a token")
async def get_insight(symbol: str):
    data = await price_service.compare(symbol)
    insight = await ai_service.get_insight(
        price_cex=data['price_cex'],
        price_dex=data['price_dex'],
        spread=data['spread_pct'],
        token=symbol,
        volume=0,
        trend=0
    )
    return {"symbol": symbol, "insight": insight}

@router.get("/history/{symbol}", summary="Get price history for a token (last 100 points)")
def get_history(symbol: str):
    """Returns the latest 100 price history points for the given symbol."""
    return history_service.get_history(symbol)
