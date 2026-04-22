# Video Summarization System Run Script
# Version: v1.0.0
# Date: 2026-03-14

Write-Host "==============================="
Write-Host "Video Summarization System"
Write-Host "==============================="
Write-Host

# Check and activate virtual environment
Write-Host "Checking virtual environment..."
$venvPath = ".\venv"
if (Test-Path $venvPath) {
    Write-Host "Virtual environment found, activating..."
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Host "Virtual environment activated."
    } else {
        Write-Host "Warning: Virtual environment found but activation script not found."
    }
} else {
    Write-Host "Virtual environment not found, using system Python."
}
Write-Host

# Check Python installation
Write-Host "Checking Python installation..."
try {
    python --version
    Write-Host "Python is installed"
    Write-Host
} catch {
    Write-Host "Error: Python not detected. Please install Python 3.10 or higher."
    Read-Host "Press any key to exit..."
    exit 1
}

# Check dependencies
Write-Host "Checking dependencies..."
try {
    $deps = pip list | Select-String -Pattern "whisper|torch|langchain"
    if ($deps) {
        Write-Host "Dependencies are installed."
    } else {
        Write-Host "Dependencies not installed, installing..."
        pip install -r requirements.txt
        Write-Host "Dependencies installed successfully!"
    }
    Write-Host
} catch {
    Write-Host "Error checking dependencies."
    Read-Host "Press any key to exit..."
    exit 1
}

# Check API key configuration
Write-Host "Checking API key configuration..."
try {
    $configContent = Get-Content -Path "config.py" -Raw
    if ($configContent -match "KIMI_API_KEY.*your_kimi_api_key_here") {
        Write-Host "Warning: API key not configured. Please edit config.py file and enter your Kimi API key."
        Read-Host "Press any key to continue, or Ctrl+C to exit..."
    }
    Write-Host "API key configuration checked."
    Write-Host
} catch {
    Write-Host "Error reading configuration file."
    Read-Host "Press any key to exit..."
    exit 1
}

# Process online video
Write-Host "Please enter video URL (or press Enter to use default test video):"
$url = Read-Host

if ([string]::IsNullOrEmpty($url)) {
    $url = "https://www.bilibili.com/video/BV1bpQeY2EvH"
    Write-Host "Using default test video: $url"
}

Write-Host
Write-Host "Processing video..."
Write-Host

# Run main script
python main.py --url "$url" --llm kimi --mode outline

Write-Host
Write-Host "Processing completed! Press any key to exit."
Read-Host