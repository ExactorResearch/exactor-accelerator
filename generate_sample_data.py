import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exactor_accelerator.ingestion.loader import DataLoader

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exactor_accelerator", "data")
os.makedirs(data_dir, exist_ok=True)

# 1. Fintech Fraud
df_fraud = DataLoader.generate_fintech_fraud_sample(n_records=500)
p_fraud = os.path.join(data_dir, "sample_fraud_transactions.csv")
df_fraud.to_csv(p_fraud, index=False)
print(f"Generated {p_fraud} ({len(df_fraud)} rows)")

# 2. SRE Incident Telemetry
df_sre = DataLoader.generate_sre_incident_sample(n_records=500)
p_sre = os.path.join(data_dir, "sample_sre_incidents.json")
df_sre.to_json(p_sre, orient="records", indent=2)
print(f"Generated {p_sre} ({len(df_sre)} rows)")

# 3. Customer Churn
df_churn = DataLoader.generate_customer_churn_sample(n_records=500)
p_churn = os.path.join(data_dir, "sample_customer_churn.csv")
df_churn.to_csv(p_churn, index=False)
print(f"Generated {p_churn} ({len(df_churn)} rows)")

# 4. SOC Cybersecurity Intrusion
df_soc = DataLoader.generate_cybersecurity_soc_sample(n_records=500)
p_soc = os.path.join(data_dir, "sample_soc_intrusion.json")
df_soc.to_json(p_soc, orient="records", indent=2)
print(f"Generated {p_soc} ({len(df_soc)} rows)")

# 5. Clinical Triage Emergency
df_triage = DataLoader.generate_clinical_triage_sample(n_records=500)
p_triage = os.path.join(data_dir, "sample_clinical_triage.csv")
df_triage.to_csv(p_triage, index=False)
print(f"Generated {p_triage} ({len(df_triage)} rows)")

# 6. Unstructured Support Conversations & Dialogues
df_convs = DataLoader.generate_support_conversations_sample(n_records=500)
p_convs_json = os.path.join(data_dir, "sample_support_conversations.json")
df_convs.to_json(p_convs_json, orient="records", indent=2, force_ascii=False)
p_convs_csv = os.path.join(data_dir, "sample_support_conversations.csv")
df_convs.to_csv(p_convs_csv, index=False)
print(f"Generated {p_convs_json} & CSV ({len(df_convs)} rows)")
