# Set Fly.io secrets
$secrets = @{
    "TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token"
    "OPENAI_API_KEY" = "your_openai_api_key"
    "OKX_API_KEY" = "your_okx_api_key"
    "OKX_API_SECRET" = "your_okx_api_secret"
    "OKX_PASSPHRASE" = "your_okx_passphrase"
    "HELIUS_API_KEY" = "your_helius_api_key"
    "DATABASE_URL" = "sqlite:///backend/db/mipilot.db"
    "OPENAI_MODEL" = "gpt-3.5-turbo"
    "CHROMEDRIVER_PATH" = "/usr/bin/chromedriver"
}

foreach ($key in $secrets.Keys) {
    Write-Host "Setting $key..."
    fly secrets set "$key=`"$($secrets[$key])`""
} 