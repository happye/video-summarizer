# Video Summarization System Run Script
# Version: v1.4.0
# Date: 2026-05-09

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

# Select run mode
Write-Host "==============================="
Write-Host "Select Run Mode:"
Write-Host "==============================="
Write-Host "1) Interactive mode (keep running, process multiple videos) [Recommended]"
Write-Host "2) Single mode (process one video then exit)"
Write-Host

$runChoice = Read-Host "Enter your choice (1-2, default: 1)"

if ($runChoice -ne "2") {
    # Interactive mode - select LLM and mode, then enter interactive loop
    Write-Host

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

    # Check API key configuration
    Write-Host "Checking API key configuration..."
    try {
        $configContent = Get-Content -Path "config.py" -Raw

        if ($llmProvider -eq "kimi") {
            if ($configContent -match 'KIMI_API_KEY\s*=\s*["\x27]\s*["\x27]') {
                Write-Host "Warning: KIMI_API_KEY is empty. Please edit config.py and enter your Kimi API key."
                Read-Host "Press any key to continue, or Ctrl+C to exit..."
            } else {
                Write-Host "Kimi API key configured."
            }
        } elseif ($llmProvider -eq "deepseek") {
            if ($configContent -match 'DEEPSEEK_API_KEY\s*=\s*["\x27]\s*["\x27]') {
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

    # Launch interactive mode
    python main.py -i --llm $llmProvider --mode $mode
} else {
    # Single mode - original behavior
    Write-Host

    # Select input mode
    Write-Host "==============================="
    Write-Host "Select Input Mode:"
    Write-Host "==============================="
    Write-Host "1) Online video URL (download from YouTube, Bilibili, etc.)"
    Write-Host "2) Local video directory (process already downloaded videos)"
    Write-Host "3) Local video file"
    Write-Host

    $inputChoice = Read-Host "Enter your choice (1-3, default: 1)"

    $localDir = ""
    $localFile = ""
    $url = ""

    if ($inputChoice -eq "2") {
        Write-Host
        Write-Host "Enter local video directory path:"
        Write-Host "(e.g., D:\Videos\my_video or .\output\my_video)"
        $localDir = Read-Host

        if ([string]::IsNullOrEmpty($localDir)) {
            Write-Host "Error: No directory specified."
            Read-Host "Press any key to exit..."
            exit 1
        }

        if (-not (Test-Path $localDir)) {
            Write-Host "Error: Directory not found: $localDir"
            Read-Host "Press any key to exit..."
            exit 1
        }

        Write-Host "Using local directory: $localDir"
    } elseif ($inputChoice -eq "3") {
        Write-Host
        Write-Host "Enter local video file path:"
        $localFile = Read-Host

        if ([string]::IsNullOrEmpty($localFile)) {
            Write-Host "Error: No file specified."
            Read-Host "Press any key to exit..."
            exit 1
        }

        if (-not (Test-Path $localFile)) {
            Write-Host "Error: File not found: $localFile"
            Read-Host "Press any key to exit..."
            exit 1
        }

        Write-Host "Using local file: $localFile"
    } else {
        Write-Host
        Write-Host "Please enter video URL (or press Enter to use default test video):"
        $url = Read-Host

        if ([string]::IsNullOrEmpty($url)) {
            $url = "https://www.bilibili.com/video/BV1bpQeY2EvH"
            Write-Host "Using default test video: $url"
        }
    }

    Write-Host

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

    # Check API key configuration
    Write-Host "Checking API key configuration..."
    try {
        $configContent = Get-Content -Path "config.py" -Raw

        if ($llmProvider -eq "kimi") {
            if ($configContent -match 'KIMI_API_KEY\s*=\s*["\x27]\s*["\x27]') {
                Write-Host "Warning: KIMI_API_KEY is empty. Please edit config.py and enter your Kimi API key."
                Read-Host "Press any key to continue, or Ctrl+C to exit..."
            } else {
                Write-Host "Kimi API key configured."
            }
        } elseif ($llmProvider -eq "deepseek") {
            if ($configContent -match 'DEEPSEEK_API_KEY\s*=\s*["\x27]\s*["\x27]') {
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

    # Process video
    Write-Host "Processing video..."
    Write-Host

    if ($inputChoice -eq "2") {
        python main.py --local "$localDir" --llm $llmProvider --mode $mode
    } elseif ($inputChoice -eq "3") {
        python main.py --file "$localFile" --llm $llmProvider --mode $mode
    } else {
        python main.py --url "$url" --llm $llmProvider --mode $mode
    }

    Write-Host
    Write-Host "Processing completed! Press any key to exit."
    Read-Host
}
