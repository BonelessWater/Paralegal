# Legal Database Access Guide

## What You Have Access To

### 🔍 Quick Summary

You currently have:
1. **LexisNexis Advance** - Credentials stored in `AMD_server/scraper/config.ini`
2. **CourtListener** - Need to check access level

---

## How to Check Your Access

### Option 1: Quick CourtListener API Check (Recommended - Fast!)

This checks if you have CourtListener API access **without** needing Selenium:

```bash
# On your AMD server
cd /home/amd-knights/Paralegal/AMD_server/ml_pipeline
python quick_access_check.py
```

This will show:
- ✅ Whether you have an API token
- ✅ Which endpoints are accessible
- ✅ How many legal cases you can access
- ✅ Your rate limits

**No API token? No problem!** CourtListener is **FREE** for web scraping.

---

### Option 2: Full Access Check (Comprehensive)

This checks **everything** - both CourtListener AND LexisNexis:

```bash
# On your AMD server (requires ChromeDriver)
cd /home/amd-knights/Paralegal/AMD_server/ml_pipeline
python check_access.py
```

This will:
1. Test CourtListener API (if you have token)
2. Test CourtListener web access (with/without login)
3. Test LexisNexis login (using credentials from config.ini)
4. Generate detailed JSON report

---

## What the Scripts Will Tell You

### CourtListener Access Levels

| Access Level | What You Get | Cost |
|-------------|--------------|------|
| **No Account** | Web scraping, basic API (5000/hour) | FREE |
| **Free Account** | Web scraping, API (5000/hour), saved searches | FREE |
| **With API Token** | Same as above + easier programmatic access | FREE |

### LexisNexis Access Levels

Based on your credentials in `AMD_server/scraper/config.ini`:
- Username: `Albert0898`
- The script will test if this account is active
- Will identify your subscription type (Academic/Professional/etc.)
- Will show which databases you can access

---

## Getting CourtListener API Access (Optional)

If you want an API token for CourtListener:

1. **Create Account** (30 seconds):
   ```
   https://www.courtlistener.com/sign-in/register/
   ```

2. **Get API Token** (instant):
   ```
   https://www.courtlistener.com/help/api/rest/
   ```
   - Login → Profile → API → Generate Token

3. **Set Token** (on AMD server):
   ```bash
   # Add to ~/.bashrc
   echo 'export COURTLISTENER_API_TOKEN="your_token_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

**But remember:** You DON'T need this for web scraping! We can scrape without any account.

---

## What Data Sources Are Available

### CourtListener (FREE - No Login Required!)

- **Coverage**: 
  - 🏛️ All Federal Courts
  - 🏛️ All State Courts (most)
  - 📚 Millions of opinions going back to 1750s
  - 📄 Full text + PDFs

- **Access Methods**:
  1. ✅ Web Scraping (Selenium) - **Unlimited**, just rate limit
  2. ✅ API (optional) - 5000 requests/hour
  3. ✅ Bulk Data Downloads - Free academic datasets

- **Best For**:
  - Case law research
  - Building RAG database
  - Training ML models
  - Finding similar cases

### LexisNexis Advance (Requires Subscription)

- **Coverage**:
  - 🏛️ All courts + international
  - 📚 Secondary sources
  - 📰 News + journals
  - 📊 Analytics

- **Your Account Status**: 
  - Run `check_access.py` to verify
  - Credentials in `AMD_server/scraper/config.ini`

- **Best For**:
  - Premium legal research
  - Shepardizing
  - Treatises + practice guides

---

## Recommendations for Your Hackathon

### Strategy: Dual-Source Scraping

1. **Primary Source: CourtListener** (FREE!)
   - Use for building initial RAG database
   - Scrape 100s of cases quickly
   - No cost, no limits (with rate limiting)
   - Perfect for demo

2. **Secondary Source: LexisNexis** (if active)
   - Use for premium/recent cases
   - Supplement CourtListener data
   - Show multi-source capability

### Why This Works

- ✅ **Free**: CourtListener costs $0
- ✅ **Fast**: Can scrape hundreds of cases in minutes
- ✅ **Legal**: CourtListener is explicitly open access
- ✅ **Comprehensive**: Millions of opinions available
- ✅ **Demo-Ready**: No authentication needed for basic scraping

---

## Run Quick Check Now

Let's find out what you have access to:

```bash
# SSH to AMD server
ssh amd-knights@134.199.202.8

# Activate venv
cd /home/amd-knights/Paralegal
source venv/bin/activate

# Quick check (30 seconds)
cd AMD_server/ml_pipeline
python quick_access_check.py

# Full check (2 minutes) - optional
python check_access.py
```

---

## What Happens Next

After running the check, you'll know:
1. ✅ Can you use CourtListener API? (optional)
2. ✅ Can you scrape CourtListener web? (almost certainly yes)
3. ✅ Is your LexisNexis account active? (will test)
4. ✅ What's your best strategy for the hackathon?

Then we'll build the intelligent scraper to use whichever source works best for you!

---

## Questions?

- **Do I need to pay for CourtListener?** No! It's free.
- **Do I need an API token?** No, web scraping works without it.
- **Will my LexisNexis account work?** Run the check to find out!
- **Which should I use?** CourtListener is easier and free - perfect for hackathon.

**Next Step**: Run `quick_access_check.py` on your server to see what you have! 🚀
