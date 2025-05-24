import os
from typing import Optional
import openai

class AlphaInsightService:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.AsyncOpenAI(api_key=self.api_key)

    async def get_insight(self, *, price_cex: float, price_dex: float, spread: float, token: str, volume: float, trend: float) -> str:
        prompt = (
            f"Based on the price difference between CEX and DEX, volume, and trend, provide a brief trader's insight for {token}. "
            f"\n\n"
            f"CEX price: {price_cex}\n"
            f"DEX price: {price_dex}\n"
            f"Spread: {spread:.2f}%\n"
            f"Volume: {volume}\n"
            f"Trend (24h): {trend:+.2f}%\n"
            f"\n"
            f"Response format: 1-2 sentences, concise, in English, no fluff."
        )
        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()

# (moved to backend/ai/alpha_insight_service.py)
