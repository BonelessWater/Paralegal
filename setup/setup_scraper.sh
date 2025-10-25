#!/bin/bash

# =============================================================================
# LexisNexis Scraper Setup for AMD Server (Ubuntu)
# =============================================================================
# This script sets up PostgreSQL database and Selenium Chrome for web scraping
# Run on AMD server: ./setup_scraper.sh
# =============================================================================

set -e  # Exit on error

echo "============================================"
echo "LexisNexis Scraper Setup"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =============================================================================
# Step 1: Update system and install PostgreSQL
# =============================================================================
echo -e "${YELLOW}[1/6] Installing PostgreSQL...${NC}"

sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

echo -e "${GREEN}✓ PostgreSQL installed${NC}"
echo ""

# =============================================================================
# Step 2: Create PostgreSQL database and user
# =============================================================================
echo -e "${YELLOW}[2/6] Setting up database...${NC}"

# Create database user and database
sudo -u postgres psql <<EOF
-- Create user if not exists
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'paralegal_user') THEN
    CREATE USER paralegal_user WITH PASSWORD 'hackathon2024';
  END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE paralegal_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'paralegal_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE paralegal_db TO paralegal_user;

\c paralegal_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO paralegal_user;

\q
EOF

echo -e "${GREEN}✓ Database created: paralegal_db${NC}"
echo -e "${GREEN}✓ User created: paralegal_user${NC}"
echo ""

# =============================================================================
# Step 3: Initialize database schema
# =============================================================================
echo -e "${YELLOW}[3/6] Initializing database schema...${NC}"

# Run the schema SQL file
sudo -u postgres psql -d paralegal_db -f ~/Paralegal/scraper/database_schema.sql

echo -e "${GREEN}✓ Database schema initialized${NC}"
echo ""

# =============================================================================
# Step 4: Install Chrome and ChromeDriver for Selenium
# =============================================================================
echo -e "${YELLOW}[4/6] Installing Chrome and ChromeDriver...${NC}"

# Add Google Chrome repository
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# Install Chrome
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Get Chrome version
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)

# Install ChromeDriver
echo "Installing ChromeDriver for Chrome version ${CHROME_VERSION}..."
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -N "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" -P ~/
unzip -o ~/chromedriver_linux64.zip -d ~/
sudo mv -f ~/chromedriver /usr/local/bin/chromedriver
sudo chmod +x /usr/local/bin/chromedriver
rm ~/chromedriver_linux64.zip

echo -e "${GREEN}✓ Chrome installed: $(google-chrome --version)${NC}"
echo -e "${GREEN}✓ ChromeDriver installed: $(chromedriver --version | head -1)${NC}"
echo ""

# =============================================================================
# Step 5: Install Python dependencies
# =============================================================================
echo -e "${YELLOW}[5/6] Installing Python dependencies...${NC}"

cd ~/Paralegal
pip install selenium beautifulsoup4 lxml psycopg2-binary

echo -e "${GREEN}✓ Python packages installed${NC}"
echo ""

# =============================================================================
# Step 6: Create scraper configuration file
# =============================================================================
echo -e "${YELLOW}[6/6] Creating configuration file...${NC}"

cd ~/Paralegal/scraper

# Copy config example file
if [ ! -f config.ini ]; then
    cp config.ini.example config.ini
    echo -e "${GREEN}✓ Configuration file created: scraper/config.ini${NC}"
    echo -e "${YELLOW}⚠ IMPORTANT: Edit scraper/config.ini and add your credentials!${NC}"
else
    echo -e "${GREEN}✓ Configuration file already exists${NC}"
fi

echo ""

# =============================================================================
# Summary and Next Steps
# =============================================================================
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ Scraper Setup Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Database Information:"
echo "  Host:     localhost"
echo "  Port:     5432"
echo "  Database: paralegal_db"
echo "  User:     paralegal_user"
echo "  Password: hackathon2024"
echo ""
echo "Next Steps:"
echo "  1. IMPORTANT: Edit scraper/config.ini and add your LexisNexis credentials"
echo "  2. Test the scraper:"
echo "     cd ~/Paralegal/scraper"
echo "     python test_scraper.py"
echo ""
echo "  3. Run the scraper:"
echo "     python scrape.py"
echo ""
echo -e "${YELLOW}Note: Make sure you have a valid LexisNexis subscription!${NC}"
echo ""
