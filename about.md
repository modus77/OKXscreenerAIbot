# About

**Creator:** [@xuryholder](https://x.com/xuryholder)

**Links:**
- GitHub: [OKXscreenerAIbot](https://github.com/modus77/OKXscreenerAIbot)
- Demo Bot: [@OKXScreenerBot](https://t.me/OKXScreenerBot)

This project was developed as part of the [OKX Solana Accelerate Hackathon](https://dorahacks.io/hackathon/okx-solana-accelerate/). While currently operating as OKX Screener AI, the project has the potential to evolve into a comprehensive product, either integrated within the OKX ecosystem or as a standalone Crypto AI platform.

**OKX Screener AI bot** is a specialized Telegram bot that focuses on tracking price differences between OKX exchange and Solana's Jupiter DEX. The bot monitors specific token pairs (like JUP, WIF, PYTH, PNUT, MOODENG), provides real-time price spread notifications, and generates instant chart screenshots from OKX. It helps traders spot arbitrage opportunities by combining price monitoring with AI-enhanced market analysis, all accessible through a simple Telegram interface.

- **Purpose:**  
  To bridge the gap between CEX and DEX trading, making arbitrage and market analysis accessible to everyone, directly in Telegram.

- **Problem Solved:**  
  Manual monitoring of price spreads, liquidity, and market trends across multiple platforms is time-consuming and error-prone. OKX Screener AI bot automates this process, providing actionable signals, AI insights, and instant charting in one place.

- **Key Features:**  
  - Real-time price and spread monitoring between OKX and Solana DEX.
  - AI-generated trading insights and risk analysis.
  - Instant chart screenshots from OKX.
  - Customizable notifications and tracked tokens.
  - Simple, intuitive Telegram interface.
  - Multi-platform deployment (Docker, Fly.io).

- **How It Works:**  
  The bot fetches live price and volume data from OKX and Jupiter, analyzes spreads and trends, and delivers actionable signals and AI insights to users in Telegram. Users can customize tracked tokens, set notification thresholds, and receive instant chart screenshots.

- **Tech Stack:**  
  - Python (aiogram, FastAPI)
  - Selenium (for chart screenshots)
  - Docker (for deployment)
  - Fly.io (cloud hosting)
  - OpenAI API (for AI insights)
  - OKX & Jupiter APIs (market data)
  - SQLite (default DB, can be swapped)

- **Market Opportunity:**  
  As cross-exchange arbitrage and DeFi/CeFi integration become more popular, tools that simplify and automate these workflows are in high demand. OKX Screener AI bot addresses this need for both retail and professional traders.

- **Scalability:**  
  The architecture supports easy addition of new exchanges, tokens, and analytics modules. The bot can be scaled horizontally via Docker/Fly.io and supports multi-user, multi-chat operation.

- **Business Model:**  
  - Freemium: Basic features free, advanced analytics/alerts as paid add-ons.
  - White-label: Custom bots for trading communities or funds.
  - Affiliate/referral integration with OKX and Solana DEXs.

- **Roadmap:**  
  - [x] Core arbitrage and AI insight features  
  - [x] Chart screenshot integration  
  - [x] Multi-token, multi-user support  
  - [x] English-only, global-ready interface  
  - [ ] Advanced analytics (order book, on-chain data)  
  - [ ] Web dashboard  
  - [ ] More exchanges and DeFi protocols  
  - [ ] Mobile app integration

- **Benefits for OKX and Solana:**  
  - Drives trading volume and user engagement.
  - Educates users about arbitrage and DeFi opportunities.
  - Bridges CEX and DEX ecosystems, increasing liquidity and market efficiency.

- **Why Telegram:**  
  Telegram is the most popular platform for crypto communities, offering instant access, bot support, and a familiar interface for traders worldwide.

## Vision

**To make advanced crypto trading intelligence accessible to everyone, everywhere — instantly, securely, and with zero friction.** 