"""
Quick CourtListener API Access Check
Tests API access without Selenium (faster, lighter)
"""

import os
import requests
import json
from datetime import datetime


def check_courtlistener_api():
    """Quick check of CourtListener API access"""
    
    print("\n" + "=" * 70)
    print("COURTLISTENER API ACCESS CHECK")
    print("=" * 70)
    
    api_token = os.getenv('COURTLISTENER_API_TOKEN', '')
    base_url = "https://www.courtlistener.com/api/rest/v3"
    
    print(f"\n1. API Token Status:")
    if api_token:
        print(f"   ✅ Token found: {api_token[:20]}...")
    else:
        print(f"   ❌ No token found")
        print(f"   💡 Set environment variable: export COURTLISTENER_API_TOKEN='your_token'")
        print(f"   💡 Or get one at: https://www.courtlistener.com/help/api/rest/")
    
    # Set up session
    session = requests.Session()
    if api_token:
        session.headers.update({'Authorization': f'Token {api_token}'})
    
    print(f"\n2. Testing API Endpoints:")
    
    endpoints = [
        ('Search Opinions', '/search/', {'q': 'employment discrimination', 'type': 'o'}),
        ('Courts', '/courts/', {}),
        ('Opinions', '/opinions/', {'page_size': 5}),
    ]
    
    results = {}
    
    for name, endpoint, params in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n   Testing: {name}")
            print(f"   URL: {url}")
            
            response = session.get(url, params=params, timeout=10)
            
            results[name] = {
                'status': response.status_code,
                'accessible': response.status_code == 200
            }
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 'N/A')
                results_returned = len(data.get('results', []))
                
                print(f"   ✅ SUCCESS - Status: {response.status_code}")
                print(f"   📊 Total available: {count}")
                print(f"   📄 Results returned: {results_returned}")
                
                # Show rate limits
                if 'X-RateLimit-Limit' in response.headers:
                    print(f"   ⏱️  Rate limit: {response.headers['X-RateLimit-Limit']}/hour")
                    print(f"   ⏱️  Remaining: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
                
                # Show first result as example
                if results_returned > 0:
                    first = data['results'][0]
                    print(f"\n   📋 Example result:")
                    if 'caseName' in first:
                        print(f"      Case: {first.get('caseName', 'N/A')[:80]}")
                    if 'court' in first:
                        print(f"      Court: {first.get('court', 'N/A')}")
                    if 'dateFiled' in first:
                        print(f"      Date: {first.get('dateFiled', 'N/A')}")
                
            elif response.status_code == 401:
                print(f"   ❌ UNAUTHORIZED - Need API token")
            elif response.status_code == 403:
                print(f"   ❌ FORBIDDEN - May require premium access")
            elif response.status_code == 429:
                print(f"   ⚠️  RATE LIMITED - Too many requests")
            else:
                print(f"   ⚠️  Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT - Request took too long")
            results[name] = {'status': 'timeout', 'accessible': False}
        except requests.exceptions.RequestException as e:
            print(f"   ❌ ERROR - {e}")
            results[name] = {'status': 'error', 'accessible': False}
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    accessible = sum(1 for r in results.values() if r.get('accessible'))
    total = len(results)
    
    print(f"\n✅ Accessible endpoints: {accessible}/{total}")
    
    if accessible == 0:
        print("\n⚠️  NO ACCESS - Possible reasons:")
        print("   1. No API token provided")
        print("   2. Invalid or expired token")
        print("   3. Network connectivity issues")
        print("\n💡 To get started:")
        print("   1. Create free account: https://www.courtlistener.com/sign-in/register/")
        print("   2. Get API token: https://www.courtlistener.com/help/api/rest/")
        print("   3. Set token: export COURTLISTENER_API_TOKEN='your_token'")
        print("\n💡 Alternative: CourtListener allows FREE public web scraping without login!")
    elif accessible < total:
        print("\n✅ PARTIAL ACCESS - Some endpoints work")
        print("   Working endpoints sufficient for basic scraping")
    else:
        print("\n✅ FULL ACCESS - All endpoints working!")
        print("   Ready to scrape legal cases")
    
    # CourtListener Free Tier Info
    print("\n" + "=" * 70)
    print("COURTLISTENER FREE TIER (No Login Required)")
    print("=" * 70)
    print("""
CourtListener is FREE and OPEN ACCESS! You can:
  ✅ Search millions of court opinions
  ✅ Access full case text
  ✅ Download PDFs
  ✅ Use basic API (5,000 requests/hour without token)
  ✅ Use web scraping (unlimited with rate limiting)

No subscription or payment required!

API Token (optional but recommended):
  • Increases rate limit to 5,000/hour
  • Enables saved searches
  • Free forever - just create an account

Get started: https://www.courtlistener.com/
    """)
    
    return results


def save_results(results):
    """Save results to JSON file"""
    output = {
        'timestamp': datetime.now().isoformat(),
        'results': results
    }
    
    with open('courtlistener_access.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Results saved to: courtlistener_access.json")


if __name__ == "__main__":
    results = check_courtlistener_api()
    save_results(results)
    
    print("\n" + "=" * 70)
    print("✅ CHECK COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. If you have no token: CourtListener is FREE - just use web scraping!")
    print("  2. If you want API access: Get token at https://www.courtlistener.com/help/api/")
    print("  3. Test web scraping: We'll use Selenium like your LexisNexis scraper")
    print("\n")
