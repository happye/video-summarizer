# Video Summarization System Run Script
# Version: v1.1.0
# Date: 2026-04-24

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

# Select LLM provider
Write-Host "==============================="
Write-Host "Select LLM Provider:"
Write-Host "==============================="
Write-Host "1) Kimi (Moonshot AI) - Default, supports long context"
Write-Host "2) DeepSeek - Requires DEEPSEEK_API_KEY in config.py"
Write-Host "3) Ollama - Local model, requires Ollama running"
Write-Host

$llmChoice = Read-Host "Enter your choice (1-3, default: 1)"

$llmProvider = "kimi"
switch ($llmChoice) {
    "2" { $llmProvider = "deepseek" }
    "3" { $llmProvider = "ollama" }
    default { $llmProvider = "kimi" }
}

Write-Host "Using LLM provider: $llmProvider"
Write-Host

# Check API key configuration for selected provider
Write-Host "Checking API key configuration..."
try {
    $configContent = Get-Content -Path "config.py" -Raw

    if ($llmProvider -eq "kimi") {
        if ($configContent -match "KIMI_API_KEY\s*=\s*['\"]\s*['\"]|KIMI_API_KEY\s*=\s*['\"]sk-.*['\"]") {
            if ($configContent -match "KIMI_API_KEY\s*=\s*['\"]\s*['\"]") {
                Write-Host "Warning: KIMI_API_KEY is empty. Please edit config.py and enter your Kimi API key."
                Read-Host "Press any key to continue, or Ctrl+C to exit..."
            } else {
                Write-Host "Kimi API key configured."
            }
        }
    } elseif ($llmProvider -eq "deepseek") {
        if ($configContent -match "DEEPSEEK_API_KEY\s*=\s*['\"]\s*['\"]") {
            Write-Host "Warning: DEEPSEEK_API_KEY is empty. Please edit config.py and enter your DeepSeek API key."
            Write-Host "Get your API key from: https://platform.deepseek.com/"
            Read-Host "Press any key to continue, or Ctrl+C to exit..."
        } else {
            Write-Host "DeepSeek API key configured."
        }
    } elseif ($llmProvider -eq "ollama") {
        Write-Host "Using Ollama local model. Make sure Ollama is running."
    }

    Write-Host "API key configuration checked."
    Write-Host
} catch {
    Write-Host "Error reading configuration file."
    Read-Host "Press any key to exit..."
    exit 1
}

# Select summarization mode
Write-Host "==============================="
Write-Host "Select Summarization Mode:"
Write-Host "==============================="
Write-Host "1) Outline - Structured hierarchical summary (default)"
Write-Host "2) Timeline - Chronological summary"
Write-Host "3) MapReduce - Parallel processing summary"
Write-Host

$modeChoice = Read-Host "Enter your choice (1-3, default: 1)"

$mode = "outline"
switch ($modeChoice) {
    "2" { $mode = "timeline" }
    "3" { $mode = "mapreduce" }
    default { $mode = "outline" }
}

Write-Host "Using mode: $mode"
Write-Host

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

# Run main script with selected provider and mode
python main.py --url "$url" --llm $llmProvider --mode $mode

Write-Host
Write-Host "Processing completed! Press any key to exit."
Read-Host
