# Setup script for LexisNexis Scraper
# Run this in PowerShell to set up the environment

Write-Host "=== LexisNexis Scraper Setup ===" -ForegroundColor Cyan

# Check Python installation
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check PostgreSQL installation
Write-Host "`nChecking PostgreSQL..." -ForegroundColor Yellow
try {
    $pgVersion = psql --version 2>&1
    Write-Host "✓ PostgreSQL found: $pgVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠ PostgreSQL not found in PATH" -ForegroundColor Yellow
    Write-Host "  Please install PostgreSQL 12+ if not already installed" -ForegroundColor Yellow
}

# Install Python dependencies
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
$requirementsPath = Join-Path (Get-Location) ".." "requirements.txt"

if (Test-Path $requirementsPath) {
    pip install -r $requirementsPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✗ requirements.txt not found at $requirementsPath" -ForegroundColor Red
    exit 1
}

# Check for ChromeDriver
Write-Host "`nChecking ChromeDriver..." -ForegroundColor Yellow
try {
    $chromeDriverVersion = chromedriver --version 2>&1
    Write-Host "✓ ChromeDriver found: $chromeDriverVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠ ChromeDriver not found" -ForegroundColor Yellow
    Write-Host "  Install it with: choco install chromedriver" -ForegroundColor Yellow
    Write-Host "  Or download from: https://chromedriver.chromium.org/downloads" -ForegroundColor Yellow
}

# Create config file from example
Write-Host "`nSetting up configuration..." -ForegroundColor Yellow
$configExample = "config.ini.example"
$configFile = "config.ini"

if (-not (Test-Path $configFile)) {
    if (Test-Path $configExample) {
        Copy-Item $configExample $configFile
        Write-Host "✓ Created $configFile from example" -ForegroundColor Green
        Write-Host "  ⚠ IMPORTANT: Edit config.ini with your credentials!" -ForegroundColor Yellow
    } else {
        Write-Host "✗ $configExample not found" -ForegroundColor Red
    }
} else {
    Write-Host "✓ config.ini already exists" -ForegroundColor Green
}

# Prompt for database setup
Write-Host "`n=== Database Setup ===" -ForegroundColor Cyan
$setupDb = Read-Host "Do you want to set up the PostgreSQL database now? (y/n)"

if ($setupDb -eq 'y' -or $setupDb -eq 'Y') {
    $dbName = Read-Host "Enter database name (default: paralegal_db)"
    if ([string]::IsNullOrWhiteSpace($dbName)) {
        $dbName = "paralegal_db"
    }
    
    $dbUser = Read-Host "Enter PostgreSQL username (default: postgres)"
    if ([string]::IsNullOrWhiteSpace($dbUser)) {
        $dbUser = "postgres"
    }
    
    Write-Host "`nCreating database..." -ForegroundColor Yellow
    
    # Check if database exists
    $checkDb = "SELECT 1 FROM pg_database WHERE datname='$dbName'" 
    $dbExists = psql -U $dbUser -tAc $checkDb 2>$null
    
    if ($dbExists -eq "1") {
        Write-Host "✓ Database '$dbName' already exists" -ForegroundColor Green
    } else {
        psql -U $dbUser -c "CREATE DATABASE $dbName;"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Database '$dbName' created" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to create database" -ForegroundColor Red
            Write-Host "  You may need to create it manually" -ForegroundColor Yellow
        }
    }
    
    # Initialize schema
    $schemaFile = "database_schema.sql"
    if (Test-Path $schemaFile) {
        Write-Host "`nInitializing database schema..." -ForegroundColor Yellow
        psql -U $dbUser -d $dbName -f $schemaFile
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Schema initialized successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to initialize schema" -ForegroundColor Red
        }
    }
}

# Display next steps
Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Edit config.ini with your LexisNexis credentials" -ForegroundColor White
Write-Host "2. Update database settings in config.ini" -ForegroundColor White
Write-Host "3. Run the scraper:" -ForegroundColor White
Write-Host "   python scrape.py --query `"your search query`" --max-results 10" -ForegroundColor Gray
Write-Host "`nFor more information, see README.md" -ForegroundColor Yellow

Write-Host "`n✓ Setup script completed!" -ForegroundColor Green
