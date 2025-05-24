# AI-powered insight service (moved from services)
import os
import logging
from openai import AsyncOpenAI
from typing import Optional

logger = logging.getLogger(__name__)

class AlphaInsightService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)
        
    async def get_insight(self, price_cex: float, price_dex: float, spread: float, token: str, volume: float, slippage: float = None, trend: float = None, detailed: bool = False) -> str:
        if not self.client:
            return f"Spread {spread:+.2f}% with ${volume:.0f} volume"

        if detailed:
            prompt = (
                f"""
You are a professional crypto trading assistant. Analyze the following market data and generate a structured, concise, actionable trading insight for the token {token}.

Format your response exactly as below, using clear sections and emojis:

🤖 AI Insight: {token}

📉 Market Overview
CEX: ${price_cex:.4f} | DEX: ${price_dex:.4f}
Spread: {spread:+.2f}%
24h Trend: {trend:+.2f}%

💧 Liquidity
Volume: ${volume:,.1f} — describe activity (e.g. strong/weak)
Slippage: {slippage:.2f}% — describe entry/exit (e.g. smooth/high impact)

⚠️ Risk Level
Describe risk (trend, spread, volatility, etc.)

📈 Short-Term Outlook
Describe likely price action and what to watch for

🎯 Entry Recommendation
Give a clear, actionable recommendation (e.g. Hold off, Buy after confirmation, etc.)

Keep each section 1-2 lines. Be objective, avoid hype, and use only English.
"""
            )
            max_tokens = 500
        else:
            prompt = (
                f"""
You are a professional crypto trading assistant. Based on the following data, give a concise, actionable trading insight for {token}.
CEX price: ${price_cex:.4f} | DEX price: ${price_dex:.4f} | Spread: {spread:+.2f}% | Volume: ${volume:,.0f} | 24h Trend: {trend:+.2f}% | Slippage: {slippage:.2f}%
Format: 1-2 sentences, no section headers, no emojis, no preamble, just the main idea in English.
"""
            )
            max_tokens = 80
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.5,
            )
            ai_text = response.choices[0].message.content.strip()
            if not ai_text:
                ai_text = f"Spread {spread:+.2f}% with ${volume:.0f} volume"
            return ai_text
        except Exception as e:
            logger.error(f"Error generating insight: {e}")
            return f"Spread {spread:+.2f}% with ${volume:.0f} volume"
