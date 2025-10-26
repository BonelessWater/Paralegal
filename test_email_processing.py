#!/usr/bin/env python3
"""
Test Email Processing - Simulate incoming email to /email endpoint

Tests the email processing endpoint with a sample email from Dominick Dupuy
about PIP coverage and settlement offer.
"""

import requests
import json


def test_email_endpoint():
    """Test the /email endpoint with a sample email."""

    # Sample email data from Dominick Dupuy
    email_data = {
        "from": "Dominick Dupuy <domdd305@gmail.com>",
        "subject": "Fwd: Questions About My PIP Coverage and Settlement Offer – March 20, 2022 Accident",
        "body": """Hi,

I hope this email finds you well. I have some questions about my case from the March 20, 2022 accident.

I recently received a settlement offer from the insurance company, but I'm confused about my PIP (Personal Injury Protection) coverage. Specifically:

1. How much PIP coverage do I have left?
2. Will the settlement affect my PIP benefits?
3. Should I accept the current offer or negotiate for more?

The insurance company is pressuring me to respond quickly, and I'm not sure what to do. This is causing me a lot of stress and I really need guidance on the best path forward.

I've attached some documents related to my case (including the settlement letter and my insurance policy).

Could you please review these and let me know what you recommend?

Thank you for your help!

Best regards,
Dominick Dupuy
Phone: 305-555-1234
Email: domdd305@gmail.com""",
        "attachments": []
    }

    # Server URL
    server_url = "http://localhost:8080/email"

    print("="*80)
    print("TESTING EMAIL PROCESSING ENDPOINT")
    print("="*80)
    print(f"\nSending email to: {server_url}")
    print(f"From: {email_data['from']}")
    print(f"Subject: {email_data['subject']}")
    print(f"\nBody preview: {email_data['body'][:150]}...")
    print("\n" + "-"*80)

    try:
        # Send POST request to /email endpoint
        response = requests.post(
            server_url,
            json=email_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        print(f"\nResponse Status Code: {response.status_code}")
        print("-"*80)

        if response.status_code == 200:
            result = response.json()

            # Display analysis
            print("\n📊 EMAIL ANALYSIS:")
            print("="*80)
            analysis = result.get('analysis', {})

            print(f"Classification:    {analysis.get('classification', 'N/A')}")
            print(f"Urgency Score:     {analysis.get('urgency_score', 'N/A')}")
            print(f"Sentiment:         {analysis.get('sentiment', 'N/A')}")
            print(f"Action Required:   {analysis.get('action_required', 'N/A')}")

            if 'entities' in analysis and analysis['entities']:
                print(f"\nExtracted Entities:")
                for entity_type, values in analysis['entities'].items():
                    print(f"  {entity_type}: {values}")

            # Display suggested response
            print("\n" + "="*80)
            print("📧 SUGGESTED RESPONSE EMAIL:")
            print("="*80)

            suggested = result.get('suggested_response', {})

            print(f"To:      {suggested.get('to', 'N/A')}")
            print(f"Subject: {suggested.get('subject', 'N/A')}")
            print(f"\nBody:\n{'-'*80}")
            print(suggested.get('body', 'N/A'))
            print("-"*80)

            print(f"\nClassification: {suggested.get('classification', 'N/A')}")
            print(f"Urgency:        {suggested.get('urgency', 'N/A')}")
            print(f"Auto-send:      {suggested.get('send', 'N/A')}")

            print("\n" + "="*80)
            print("✓ EMAIL PROCESSING SUCCESSFUL")
            print("="*80)

            # Save results to file
            output_file = "/tmp/email_processing_result.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n📄 Full results saved to: {output_file}")

        else:
            print(f"\n✗ ERROR: Server returned status code {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to server")
        print("Make sure the AMD server is running:")
        print("  cd ~/Paralegal/AMD_server")
        print("  source ~/venv/bin/activate")
        print("  python server.py")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_email_endpoint()
