#!/usr/bin/env python3
"""
Email Response Demonstration

Shows what the email processing system would generate in response to
Dominick Dupuy's email about PIP coverage and settlement offer.
"""

import json
from datetime import datetime


def classify_email(subject: str, body: str) -> str:
    """Classify the email type."""
    text = (subject + " " + body).lower()

    if any(word in text for word in ['pip', 'coverage', 'insurance', 'claim', 'accident']):
        return 'CLIENT_COMMUNICATION'
    elif any(word in text for word in ['settlement', 'offer', 'negotiate', 'compensation']):
        return 'SETTLEMENT_DISCUSSION'
    else:
        return 'CLIENT_COMMUNICATION'


def calculate_urgency(subject: str, body: str) -> float:
    """Calculate urgency score (0.0 - 1.0)."""
    text = (subject + " " + body).lower()
    score = 0.0

    # High urgency keywords
    if any(word in text for word in ['urgent', 'pressuring', 'quickly', 'stress', 'need', 'asap']):
        score += 0.4

    # Question marks indicate need for response
    score += min(text.count('?') * 0.05, 0.2)

    # Exclamation marks
    score += min(text.count('!') * 0.05, 0.1)

    return min(score, 1.0)


def analyze_sentiment(body: str) -> str:
    """Analyze email sentiment."""
    text = body.lower()

    negative_words = ['confused', 'pressuring', 'stress', 'not sure', 'worried']
    positive_words = ['thank', 'hope', 'well', 'appreciate']

    neg_count = sum(1 for word in negative_words if word in text)
    pos_count = sum(1 for word in positive_words if word in text)

    if neg_count > pos_count:
        return 'NEGATIVE'
    elif pos_count > neg_count:
        return 'POSITIVE'
    else:
        return 'NEUTRAL'


def generate_response(sender: str, subject: str, body: str) -> dict:
    """Generate email response."""

    # Extract sender name
    sender_name = "Dominick Dupuy" if "Dominick" in sender else sender.split('@')[0]

    # Classify and analyze
    classification = classify_email(subject, body)
    urgency = calculate_urgency(subject, body)
    sentiment = analyze_sentiment(body)

    # Check if it's a PIP-related email
    is_pip_related = 'pip' in body.lower() or 'personal injury protection' in body.lower()

    if is_pip_related:
        response_body = f"""Dear {sender_name},

Thank you for reaching out with your questions about PIP coverage and your settlement offer.

I understand you have concerns about:
- Your PIP (Personal Injury Protection) coverage details
- The settlement offer you've received
- Your accident from March 20, 2022

To provide you with accurate information, I will need to:

1. Review your insurance policy documents
2. Examine the settlement offer details
3. Consult with the supervising attorney regarding your specific situation

Could you please provide or confirm:
- Your insurance policy number
- Copy of the settlement offer (if available)
- Any recent correspondence from the insurance company

I will work on gathering this information and will have a detailed response for you within 24 hours.

If this is urgent, please don't hesitate to call our office directly.

Best regards,
Paralegal AI Assistant"""
    else:
        response_body = f"""Dear {sender_name},

Thank you for your email.

I have received your message and will review it carefully. I will get back to you with a detailed response within 24 hours.

If you need immediate assistance, please don't hesitate to call our office.

Best regards,
Paralegal AI Assistant"""

    # Create response subject
    response_subject = subject
    if not response_subject.lower().startswith('re:'):
        response_subject = f"Re: {response_subject}"

    return {
        "analysis": {
            "classification": classification,
            "urgency_score": round(urgency, 3),
            "sentiment": sentiment,
            "action_required": True,
            "has_settlement_offer": "settlement" in body.lower(),
            "has_pip_questions": "pip" in body.lower()
        },
        "suggested_response": {
            "to": sender,
            "subject": response_subject,
            "body": response_body,
            "send": False,
            "classification": classification,
            "urgency": urgency
        }
    }


def main():
    """Demonstrate email processing."""

    # Sample email from Dominick Dupuy
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
Email: domdd305@gmail.com"""
    }

    print("="*80)
    print("EMAIL PROCESSING DEMONSTRATION")
    print("="*80)
    print("\n📨 INCOMING EMAIL:")
    print("-"*80)
    print(f"From:    {email_data['from']}")
    print(f"Subject: {email_data['subject']}")
    print(f"\nBody:\n{email_data['body']}")
    print("-"*80)

    # Process email
    result = generate_response(
        email_data['from'],
        email_data['subject'],
        email_data['body']
    )

    # Display analysis
    print("\n📊 EMAIL ANALYSIS:")
    print("="*80)
    analysis = result['analysis']
    print(f"Classification:           {analysis['classification']}")
    print(f"Urgency Score:            {analysis['urgency_score']}")
    print(f"Sentiment:                {analysis['sentiment']}")
    print(f"Action Required:          {analysis['action_required']}")
    print(f"Has Settlement Offer:     {analysis['has_settlement_offer']}")
    print(f"Has PIP Questions:        {analysis['has_pip_questions']}")

    # Display suggested response
    print("\n📧 SUGGESTED RESPONSE EMAIL:")
    print("="*80)
    suggested = result['suggested_response']
    print(f"To:      {suggested['to']}")
    print(f"Subject: {suggested['subject']}")
    print(f"\nBody:\n{'-'*80}\n{suggested['body']}\n{'-'*80}")

    print(f"\nClassification:  {suggested['classification']}")
    print(f"Urgency Score:   {suggested['urgency']:.3f}")
    print(f"Auto-send:       {suggested['send']}")

    # Save to file
    output_file = "/tmp/email_response_demo.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print("\n" + "="*80)
    print("✓ EMAIL PROCESSING COMPLETE")
    print("="*80)
    print(f"\n📄 Full results saved to: {output_file}")

    # Show how to use with server
    print("\n" + "="*80)
    print("TO TEST WITH SERVER:")
    print("="*80)
    print("""
1. Start the AMD server:
   cd ~/Paralegal/AMD_server
   source ~/venv/bin/activate
   python server.py

2. In another terminal, run:
   python test_email_processing.py

3. Or use curl:
   curl -X POST http://localhost:8080/email \\
     -H "Content-Type: application/json" \\
     -d '{
       "from": "Dominick Dupuy <domdd305@gmail.com>",
       "subject": "Questions About My PIP Coverage",
       "body": "I have questions about my PIP coverage..."
     }'
""")


if __name__ == "__main__":
    main()
