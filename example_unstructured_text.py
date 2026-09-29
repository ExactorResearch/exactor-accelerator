"""
EXAMPLE: UNSTRUCTURED TEXT AND CUSTOMER SUPPORT DIALOGUES WITH EXACTOR ACCELERATOR

This script demonstrates how ExactorAccelerator ingests:
1. Free-form text columns (emails, support tickets, complaints, WhatsApp chats).
2. Multi-turn dialogues in JSON/list format.
3. Automated semantic intent extraction (churn, billing, frustration, bugs, legal threats).
4. Projection onto the boolean hypercube B^k and exact rule discovery.
5. Real-time inference with calibrated JEV decisions and DeepSeek audit explanation.
"""

import pandas as pd
from exactor_accelerator import ExactorAcceleratorClassifier
from exactor_accelerator.sdk import ExactorAccelerator


def main():
    print("=" * 85)
    print("DEMO: INGESTION OF UNSTRUCTURED TEXT AND CUSTOMER CHAT TRANSCRIPTS")
    print("=" * 85)

    # -------------------------------------------------------------------------
    # 1. HISTORICAL DATASET WITH UNSTRUCTURED TEXT AND CUSTOMER STATE
    # -------------------------------------------------------------------------
    print("\n[STEP 1] Creating historical dataset with customer messages and transcripts:")

    conversations_data = [
        # Critical Cases (Churn / Escalation / Fraud)
        {
            "customer_id": "CLI-101",
            "account_age_months": 4,
            "invoice_amount": 220.0,
            "chat_transcript": "Terrible service!! This is the third time you charge me twice on my credit card and nobody answers. I want immediate cancellation or I am going to consumer protection with a lawyer!",
            "requires_urgent_escalation": 1
        },
        {
            "customer_id": "CLI-102",
            "account_age_months": 2,
            "invoice_amount": 450.0,
            "chat_transcript": "URGENT: My account was hacked, password was changed, and money was transferred without authorization. I need a supervisor immediately!!",
            "requires_urgent_escalation": 1
        },
        {
            "customer_id": "CLI-103",
            "account_age_months": 14,
            "invoice_amount": 190.0,
            "chat_transcript": "I have been waiting for two weeks for a refund on an unauthorized charge. I am sick of this scam, cancel my subscription now.",
            "requires_urgent_escalation": 1
        },
        # Standard / Safe Cases
        {
            "customer_id": "CLI-201",
            "account_age_months": 24,
            "invoice_amount": 35.0,
            "chat_transcript": "Hello, thank you so much for the assistance the other day. I just wanted to ask when my next invoice is due.",
            "requires_urgent_escalation": 0
        },
        {
            "customer_id": "CLI-202",
            "account_age_months": 18,
            "invoice_amount": 60.0,
            "chat_transcript": "Good afternoon, could you please send me a PDF receipt for last month's payment? Thanks in advance.",
            "requires_urgent_escalation": 0
        },
        {
            "customer_id": "CLI-203",
            "account_age_months": 36,
            "invoice_amount": 45.0,
            "chat_transcript": "Great support as always, everything is working smoothly now. Have a nice day!",
            "requires_urgent_escalation": 0
        },
    ] * 8  # Replicate to simulate representative historical dataset

    df = pd.DataFrame(conversations_data)
    print(f" -> Total dialogue records: {len(df)}")
    print(f" -> Sample input text:\n    \"{df['chat_transcript'].iloc[0]}\"")

    # -------------------------------------------------------------------------
    # 2. TRAINING SCIKIT-LEARN CLASSIFIER DIRECTLY ON RAW TEXT
    # -------------------------------------------------------------------------
    print("\n[STEP 2] Fitting ExactorAcceleratorClassifier on raw text data:")
    
    clf = ExactorAcceleratorClassifier(
        max_variables=12,
        fast_path=True
    )
    
    # Notice: We pass raw text directly, without manual regexes or vectorizers!
    X = df[["account_age_months", "invoice_amount", "chat_transcript"]]
    y = df["requires_urgent_escalation"]
    
    clf.fit(X, y)

    print(" -> Model successfully fitted!")
    print(f" -> Automatically Discovered Boolean Variables ({len(clf.variables_)}):")
    for i, var_name in enumerate(clf.variables_):
        print(f"    [{i:02d}] {var_name}")

    print(f"\n -> Discovered Exact Boolean Formula:")
    print(f"    {clf.formula_expr_}")

    # -------------------------------------------------------------------------
    # 3. REAL-TIME INFERENCE ON UNSEEN LIVE CONVERSATIONS
    # -------------------------------------------------------------------------
    print("\n[STEP 3] Real-time inference on new incoming live messages:")

    test_samples = [
        {
            "description": "Incoming angry customer message (Charge error & cancellation)",
            "data": {
                "account_age_months": 3,
                "invoice_amount": 310.0,
                "chat_transcript": "You charged me double this month and nobody answers my emails. This is a scam, refund my money immediately or I will take legal action!"
            }
        },
        {
            "description": "Critical security incident message (Hacked password)",
            "data": {
                "account_age_months": 1,
                "invoice_amount": 500.0,
                "chat_transcript": "Help, my account was hacked and unauthorized transactions were made! Urgent supervisor needed!"
            }
        },
        {
            "description": "Standard friendly query",
            "data": {
                "account_age_months": 28,
                "invoice_amount": 40.0,
                "chat_transcript": "Hello, good morning! Just wanted to verify if my monthly payment cleared properly. Thanks!"
            }
        }
    ]

    for item in test_samples:
        df_test = pd.DataFrame([item["data"]])
        pred = clf.predict(df_test)[0]
        prob = clf.predict_proba(df_test)[0][1]

        print(f"\nScenario: {item['description']}")
        print(f"Text: \"{item['data']['chat_transcript']}\"")
        print(f"Ruling: {'[ESCALATE TO SUPERVISOR]' if pred == 1 else '[STANDARD BOT/AGENT RESOLUTION]'}")
        print(f"Certainty: {prob * 100:.1f}%")

    print("\n" + "=" * 85)
    print("UNSTRUCTURED TEXT PIPELINE TEST COMPLETED SUCCESSFULLY")
    print("=" * 85)


if __name__ == "__main__":
    main()
