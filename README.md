# OKX Screener AI Bot

A Telegram-based trading assistant that monitors price differences between OKX (CEX) and Jupiter (Solana DEX), providing real-time arbitrage opportunities with AI-powered insights and automated chart screenshots. The bot helps traders identify potential trades by tracking specific token pairs and delivering instant notifications through Telegram.

**Creator:** [@xuryholder](https://x.com/xuryholder)

**Links:**
- GitHub: [OKXscreenerAIbot](https://github.com/modus77/OKXscreenerAIbot)
- Demo Bot: [@OKXScreenerBot](https://t.me/OKXScreenerBot)

This project was created as part of the [OKX Solana Accelerate Hackathon](https://dorahacks.io/hackathon/okx-solana-accelerate/). While it currently functions as OKX Screener AI, it has the potential to evolve into a full-fledged product, either as part of the OKX ecosystem or as an independent Crypto AI project.

## 🚀 Key Features

- **AI-Powered Analysis**
  - Real-time trading signals using OpenAI
  - Market sentiment prediction
  - Risk assessment and spread analysis
  - Detailed token insights with trend analysis

- **Exchange Integration**
  - OKX (CEX) integration for market data and trading
  - Jupiter DEX (Solana) integration for decentralized swaps
  - Real-time price comparison between CEX and DEX
  - Automated arbitrage opportunity detection

- **Blockchain Integration**
  - Helius API integration for Solana token metadata
  - Token holder analytics
  - Real-time blockchain monitoring

- **User Interface**
  - Interactive Telegram bot with rich menu system
  - Real-time price alerts and notifications
  - Customizable spread thresholds
  - Token tracking preferences
  - Chart generation and visualization

- **Backend Infrastructure**
  - FastAPI backend for high-performance API endpoints
  - Prometheus metrics for monitoring
  - Sentry integration for error tracking
  - Automated health checks
  - Scheduled market updates

## 🛠 Technical Stack

- **Backend Framework**: FastAPI
- **Bot Framework**: aiogram 3.x
- **AI Integration**: OpenAI API
- **Database**: SQLite (configurable)
- **Monitoring**: Prometheus + Sentry
- **Container**: Docker + Docker Compose
- **Chart Generation**: Headless Chrome + Selenium
- **Testing**: pytest

## 📋 Prerequisites

Before running the bot, make sure you have:

1. Python 3.9+ installed
2. Docker and Docker Compose (for containerized deployment)
3. Chrome/Chromium (for chart screenshots)
4. Required API Keys:
   - Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
   - OpenAI API Key
   - OKX API Credentials (API Key, Secret, Passphrase)

## 🛠 Installation

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/modus77/OKXscreenerAIbot.git
   cd OKXscreenerAIbot
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

### Docker Setup

1. Build and run with Docker Compose:
   ```bash
   docker compose up -d
   ```

2. Check logs:
   ```bash
   docker compose logs -f
   ```

## 🚀 Usage

1. Start the bot:
   ```bash
   # Local
   python -m telegram.bot

   # Or with Docker
   docker compose up -d
   ```

2. Open Telegram and start chatting with your bot

3. Available commands:
   - `/start` - Start the bot and see available options
   - `/help` - Show help message
   - `/settings` - Configure your preferences
+ Buttons
  - `Refresh` - showing market opportunities
  - `Top Arbitrage` - TON-3 arbitrage opportunities
  - `AI Insight` - Artificial Intilegens Insights

## 🔧 Configuration

The bot can be configured through environment variables in the `.env` file:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `OPENAI_API_KEY`: OpenAI API key for AI insights
- `OKX_API_KEY`: OKX API key
- `OKX_API_SECRET`: OKX API secret
- `OKX_PASSPHRASE`: OKX API passphrase
- `DATABASE_URL`: SQLite database path
- `LOG_LEVEL`: Logging level (default: INFO)
- `PORT`: Server port (default: 8000)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔄 Updates

- Added support for aiogram 3.x
- Improved error handling and monitoring
- Enhanced AI insights with trend analysis
- Added chart generation capabilities
- Implemented customizable notifications

## 📁 Project Structure

```
okx-screener-ai/
├── backend/                # Backend services
│   ├── ai/                # AI services and models
│   ├── api/               # API endpoints
│   ├── clients/           # External API clients
│   ├── config/            # Configuration
│   ├── db/                # Database
│   └── services/          # Business logic
├── telegram/              # Telegram bot
│   ├── bot.py            # Main bot logic
│   └── health.py         # Health checks
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── docker-compose.yml     # Container orchestration
└── Dockerfile            # Container build
```

## 🔍 Monitoring & Metrics

The bot provides several monitoring endpoints:
- `/health` - Service health status
- `/metrics` - Prometheus metrics
  - Bot message count
  - Error count
  - System metrics
  - API latencies

## 🚀 Deployment

### Fly.io Deployment

1. Install flyctl
2. Initialize:
   ```bash
   fly launch
   ```
3. Set secrets:
   ```
