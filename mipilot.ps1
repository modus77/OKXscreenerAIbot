# MiPilot PowerShell Script
# Launch and manage the MiPilot project

# Function to display the menu
function Show-Menu {
    Clear-Host
    Write-Host "==========================" -ForegroundColor Cyan
    Write-Host "    MiPilot Control Panel    " -ForegroundColor Cyan
    Write-Host "==========================" -ForegroundColor Cyan
    Write-Host "1. Initialize Database"
    Write-Host "2. Add Solana Tokens"
    Write-Host "3. Start Backend Server"
    Write-Host "4. Start Telegram Bot"
    Write-Host "5. Start All Services (Docker)"
    Write-Host "6. Stop All Services (Docker)"
    Write-Host "7. Show Logs (Docker)"
    Write-Host "8. Open Documentation"
    Write-Host "9. Create Virtual Environment"
    Write-Host "10. Install Requirements"
    Write-Host "Q. Exit"
    Write-Host "==========================" -ForegroundColor Cyan
}

# Function to initialize the database
function Initialize-Database {
    Write-Host "Initializing database..." -ForegroundColor Yellow
    python scripts\db\init_db.py
    Write-Host "Database initialized." -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

# Function to add Solana tokens
function Add-SolanaTokens {
    Write-Host "Adding Solana tokens..." -ForegroundColor Yellow
    python scripts\db\add_solana_tokens.py
    Write-Host "Solana tokens added." -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

# Function to start the backend server
function Start-Backend {
    Write-Host "Starting backend server..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-Command python -m backend.main"
    Write-Host "Backend server started. Press Ctrl+C to stop." -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

# Function to start the Telegram bot
function Start-TelegramBot {
    Write-Host "Starting Telegram bot..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-Command python -m telegram.bot"
    Write-Host "Telegram bot started. Press Ctrl+C to stop." -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

# Function to start all services with Docker
function Start-DockerServices {
    Write-Host "Starting all services with Docker..." -ForegroundColor Yellow
    docker-compose up -d
    Write-Host "All services started." -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

# Function to stop all Docker services
function Stop-DockerServices {
    Write-Host "Stopping all services..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "All services stopped." -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

# Function to show Docker logs
function Show-DockerLogs {
    Write-Host "Showing Docker logs (press Ctrl+C to exit)..." -ForegroundColor Yellow
    docker-compose logs -f
}

# Function to open documentation
function Open-Documentation {
    Write-Host "Opening documentation..." -ForegroundColor Yellow
    notepad.exe README.md
}

# Function to create a virtual environment
function Create-VirtualEnvironment {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Virtual environment created." -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

# Function to install requirements
function Install-Requirements {
    Write-Host "Installing requirements..." -ForegroundColor Yellow
    if (Test-Path -Path ".\venv\Scripts\Activate.ps1") {
        & .\venv\Scripts\Activate.ps1
        pip install -r requirements.txt
        deactivate
    } else {
        pip install -r requirements.txt
    }
    Write-Host "Requirements installed." -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

# Main program loop
do {
    Show-Menu
    $choice = Read-Host "Enter your choice"
    
    switch ($choice) {
        '1' { Initialize-Database }
        '2' { Add-SolanaTokens }
        '3' { Start-Backend }
        '4' { Start-TelegramBot }
        '5' { Start-DockerServices }
        '6' { Stop-DockerServices }
        '7' { Show-DockerLogs }
        '8' { Open-Documentation }
        '9' { Create-VirtualEnvironment }
        '10' { Install-Requirements }
        'Q' { exit }
        'q' { exit }
        default { Write-Host "Invalid choice. Try again." -ForegroundColor Red; Read-Host "Press Enter to continue" }
    }
} while ($true)
