#!/bin/bash
# Quick one-liner to set up scraper on AMD server
# Usage: ./quick_setup_scraper.sh

echo "🚀 Setting up LexisNexis Scraper on AMD Server..."
echo ""
echo "Run these commands on the AMD server:"
echo ""
echo "ssh amd-knights@134.199.202.8"
echo "cd ~/Paralegal && git pull"
echo "cd setup && chmod +x setup_scraper.sh && ./setup_scraper.sh"
echo ""
echo "After setup completes, test it:"
echo "cd ~/Paralegal/scraper && python test_database.py"
echo ""
