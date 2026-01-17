# Helper script to set OpenAI API key in .env file
# Usage: .\set_api_key.ps1 -ApiKey "sk-proj-xxxxxxxxxxxxx"

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiKey
)

$envFile = ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "❌ .env file not found. Creating from template..." -ForegroundColor Red
    Copy-Item "env.example" $envFile
}

# Read the .env file
$content = Get-Content $envFile -Raw

# Replace the OPENAI_API_KEY line
$content = $content -replace "OPENAI_API_KEY=.*", "OPENAI_API_KEY=$ApiKey"

# Write back to file
Set-Content -Path $envFile -Value $content -NoNewline

Write-Host "✅ OpenAI API key has been set in .env file!" -ForegroundColor Green
Write-Host "You can now run: python main.py example_article.txt" -ForegroundColor Cyan

