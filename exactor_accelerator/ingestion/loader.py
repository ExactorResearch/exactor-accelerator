"""
Data Ingestion and Sample Generator for EXACTOR + Jev Hybrid Architecture.
Parses CSV and JSON data into pandas DataFrames and generates rich enterprise datasets
capable of producing up to 32 discrete Boolean propositions on the hypercube B^k.
"""

from typing import Dict, Any, Union, Optional
import json
import io
import pandas as pd
import numpy as np


class DataLoader:
    """Utility class to parse and generate datasets for Phase A onboarding."""

    @staticmethod
    def load_from_bytes(content: bytes, filename: str) -> pd.DataFrame:
        """Parses in-memory bytes into a pandas DataFrame."""
        if filename.lower().endswith(".csv"):
            return pd.read_csv(io.BytesIO(content))
        elif filename.lower().endswith(".json"):
            return pd.read_json(io.BytesIO(content))
        else:
            raise ValueError(f"Formato no soportado para archivo: {filename}. Usa CSV o JSON.")

    @staticmethod
    def load_from_json_string(json_str_or_obj: Union[str, Dict, list]) -> pd.DataFrame:
        """Loads JSON strings or parsed Python objects into DataFrame."""
        if isinstance(json_str_or_obj, str):
            data = json.loads(json_str_or_obj)
        else:
            data = json_str_or_obj

        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            return pd.DataFrame([data])
        raise ValueError("Invalid JSON for tabular ingestion.")

    @staticmethod
    def generate_fintech_fraud_sample(n_records: int = 500, seed: int = 42) -> pd.DataFrame:
        """
        Generates realistic Fintech Fraud Detection dataset for Phase A onboarding.
        Produces rich enterprise telemetry to enable up to 32 Boolean propositions.
        """
        np.random.seed(seed)
        amounts = np.random.exponential(scale=180.0, size=n_records) + 5.0
        spike_indices = np.random.choice(n_records, size=int(n_records * 0.15), replace=False)
        amounts[spike_indices] += np.random.uniform(1200.0, 4500.0, size=len(spike_indices))

        velocity_1h = np.random.poisson(lam=1.8, size=n_records)
        velocity_24h = velocity_1h + np.random.poisson(lam=4.2, size=n_records)
        country_risk = np.random.choice(["LOW", "MEDIUM", "HIGH"], size=n_records, p=[0.70, 0.20, 0.10])
        merchant_cat = np.random.choice(
            ["GROCERY", "ELECTRONICS", "CRYPTO", "LUXURY", "TRAVEL", "GAMBLING"],
            size=n_records,
            p=[0.35, 0.25, 0.10, 0.10, 0.10, 0.10]
        )
        device_trust = np.clip(np.random.beta(a=5, b=2, size=n_records), 0.05, 0.99)
        ip_risk_score = np.clip(np.random.beta(a=2, b=5, size=n_records), 0.01, 0.99)
        failed_pins = np.random.choice([0, 1, 2, 3], size=n_records, p=[0.82, 0.11, 0.05, 0.02])
        is_new_dev = np.random.choice([0, 1], size=n_records, p=[0.78, 0.22])
        card_present = np.random.choice([0, 1], size=n_records, p=[0.40, 0.60])
        is_intl = np.random.choice([0, 1], size=n_records, p=[0.85, 0.15])
        user_age = np.random.randint(18, 78, size=n_records)
        billing_match = np.random.choice([0, 1], size=n_records, p=[0.12, 0.88])
        days_since_pwd_reset = np.random.randint(1, 360, size=n_records)

        # Target generation: multi-clause logical rule with XOR behavior
        is_fraud = np.zeros(n_records, dtype=int)
        for i in range(n_records):
            clause_a = 1 if (amounts[i] > 1200.0 and velocity_1h[i] >= 3) else 0
            clause_b = 1 if (country_risk[i] == "HIGH" and is_new_dev[i] == 1) else 0
            clause_c = 1 if (device_trust[i] < 0.35 and failed_pins[i] >= 2) else 0
            clause_d = 1 if (merchant_cat[i] in ["CRYPTO", "LUXURY"] and ip_risk_score[i] > 0.70) else 0
            clause_e = 1 if (card_present[i] == 0 and billing_match[i] == 0 and is_intl[i] == 1) else 0

            combined = ((clause_a | clause_b) ^ clause_c) | (clause_d & clause_e)
            is_fraud[i] = 1 if combined else 0

        return pd.DataFrame({
            "amount": np.round(amounts, 2),
            "velocity_1h": velocity_1h,
            "velocity_24h": velocity_24h,
            "country_risk": country_risk,
            "merchant_category": merchant_cat,
            "device_trust": np.round(device_trust, 3),
            "ip_risk_score": np.round(ip_risk_score, 3),
            "failed_pin_attempts": failed_pins,
            "is_new_device": is_new_dev,
            "card_present": card_present,
            "is_international_txn": is_intl,
            "user_age": user_age,
            "billing_address_match": billing_match,
            "days_since_pwd_reset": days_since_pwd_reset,
            "is_fraud": is_fraud
        })

    @staticmethod
    def generate_sre_incident_sample(n_records: int = 500, seed: int = 101) -> pd.DataFrame:
        """
        Generates Cloud Microservices Incident Telemetry dataset with high dimensionality.
        Target: trigger_mitigation (0 or 1).
        """
        np.random.seed(seed)
        latency = np.random.gamma(shape=2.0, scale=45.0, size=n_records) + 20.0
        error_rate = np.clip(np.random.beta(a=1, b=20, size=n_records) * 100.0, 0.0, 45.0)
        cpu_usage = np.clip(np.random.normal(loc=55.0, scale=20.0, size=n_records), 5.0, 99.0)
        memory_usage = np.clip(np.random.normal(loc=60.0, scale=18.0, size=n_records), 10.0, 99.0)
        retry_bursts = np.random.poisson(lam=1.2, size=n_records)
        disk_io_iops = np.random.randint(150, 4800, size=n_records)
        network_egress = np.round(np.random.exponential(scale=120.0, size=n_records) + 15.0, 1)
        open_tcp = np.random.randint(80, 5500, size=n_records)
        db_pool_sat = np.clip(np.random.beta(a=2, b=4, size=n_records) * 100.0, 2.0, 99.0)
        service_tier = np.random.choice(["TIER_1_CRITICAL", "TIER_2_CORE", "TIER_3_BATCH"], size=n_records, p=[0.4, 0.4, 0.2])
        cloud_region = np.random.choice(["US_EAST", "EU_WEST", "AP_SOUTH", "SA_EAST"], size=n_records)

        trigger_mitigation = np.zeros(n_records, dtype=int)
        for i in range(n_records):
            c1 = (latency[i] > 280.0 and error_rate[i] > 5.0)
            c2 = (cpu_usage[i] > 85.0 and retry_bursts[i] >= 3)
            c3 = (service_tier[i] == "TIER_1_CRITICAL" and error_rate[i] > 2.0)
            c4 = (db_pool_sat[i] > 88.0 and open_tcp[i] > 3500)
            c5 = (memory_usage[i] > 92.0 and disk_io_iops[i] > 4000)
            trigger_mitigation[i] = 1 if (c1 or c2 or c3 or c4 or c5) else 0

        return pd.DataFrame({
            "latency_ms": np.round(latency, 1),
            "error_rate_pct": np.round(error_rate, 2),
            "cpu_usage_pct": np.round(cpu_usage, 1),
            "memory_usage_pct": np.round(memory_usage, 1),
            "retry_bursts": retry_bursts,
            "disk_io_iops": disk_io_iops,
            "network_egress_mbps": network_egress,
            "open_tcp_connections": open_tcp,
            "db_pool_saturation_pct": np.round(db_pool_sat, 1),
            "service_tier": service_tier,
            "cloud_region": cloud_region,
            "trigger_mitigation": trigger_mitigation
        })

    @staticmethod
    def generate_customer_churn_sample(n_records: int = 500, seed: int = 202) -> pd.DataFrame:
        """
        Generates Customer Retention & Churn Prediction dataset.
        Target: churn (0 or 1).
        """
        np.random.seed(seed)
        tenure = np.random.randint(1, 72, size=n_records)
        monthly_charges = np.round(np.random.uniform(20.0, 115.0, size=n_records), 2)
        support_tickets = np.random.poisson(lam=1.3, size=n_records)
        weekly_usage_hours = np.round(np.clip(np.random.normal(loc=14.0, scale=8.0, size=n_records), 0.5, 45.0), 1)
        features_adopted = np.random.randint(1, 15, size=n_records)
        nps_score = np.random.randint(0, 11, size=n_records)
        contracts = np.random.choice(["MONTH_TO_MONTH", "ONE_YEAR", "TWO_YEAR"], size=n_records, p=[0.55, 0.25, 0.20])
        tech_support = np.random.choice([0, 1], size=n_records, p=[0.60, 0.40])
        auto_renew = np.random.choice([0, 1], size=n_records, p=[0.45, 0.55])
        payment_method = np.random.choice(["ELECTRONIC_CHECK", "CREDIT_CARD", "BANK_TRANSFER"], size=n_records, p=[0.45, 0.35, 0.20])

        churn = np.zeros(n_records, dtype=int)
        for i in range(n_records):
            c1 = (tenure[i] < 12 and monthly_charges[i] > 70.0)
            c2 = (contracts[i] == "MONTH_TO_MONTH" and support_tickets[i] >= 3)
            c3 = (tech_support[i] == 0 and monthly_charges[i] > 85.0)
            c4 = (weekly_usage_hours[i] < 3.0 and nps_score[i] < 5)
            churn[i] = 1 if (c1 or c2 or c3 or c4) else 0

        return pd.DataFrame({
            "tenure_months": tenure,
            "monthly_charges": monthly_charges,
            "weekly_usage_hours": weekly_usage_hours,
            "features_adopted": features_adopted,
            "support_tickets_30d": support_tickets,
            "nps_score": nps_score,
            "contract_type": contracts,
            "has_tech_support": tech_support,
            "has_auto_renew": auto_renew,
            "payment_method": payment_method,
            "churn": churn
        })

    @staticmethod
    def generate_cybersecurity_soc_sample(n_records: int = 500, seed: int = 303) -> pd.DataFrame:
        """
        Generates Cybersecurity SOC SIEM Network Intrusion Alarms.
        Target: block_ip_address (0 or 1).
        """
        np.random.seed(seed)
        failed_logins = np.random.poisson(lam=1.5, size=n_records)
        spike_logins = np.random.choice(n_records, size=int(n_records * 0.18), replace=False)
        failed_logins[spike_logins] += np.random.randint(8, 25, size=len(spike_logins))

        packet_rate = np.random.exponential(scale=25.0, size=n_records) + 2.0
        spike_packets = np.random.choice(n_records, size=int(n_records * 0.15), replace=False)
        packet_rate[spike_packets] += np.random.uniform(80.0, 250.0, size=len(spike_packets))

        port_scans = np.random.choice([0, 1, 5, 20, 95], size=n_records, p=[0.75, 0.12, 0.05, 0.04, 0.04])
        bytes_out_mb = np.round(np.random.exponential(scale=45.0, size=n_records) + 0.5, 2)
        dns_queries_sec = np.random.randint(1, 450, size=n_records)
        ssh_failed_count = np.random.poisson(lam=0.8, size=n_records)
        country_rep = np.random.choice(["TRUSTED", "NEUTRAL", "SUSPICIOUS", "MALICIOUS"], size=n_records, p=[0.55, 0.25, 0.12, 0.08])
        protocol = np.random.choice(["TCP", "UDP", "HTTPS", "ICMP"], size=n_records, p=[0.45, 0.20, 0.30, 0.05])
        is_tor = np.random.choice([0, 1], size=n_records, p=[0.92, 0.08])
        priv_account = np.random.choice([0, 1], size=n_records, p=[0.85, 0.15])

        block_ip = np.zeros(n_records, dtype=int)
        for i in range(n_records):
            c1 = (failed_logins[i] >= 8 and priv_account[i] == 1)
            c2 = (packet_rate[i] > 90.0 and port_scans[i] > 15)
            c3 = (country_rep[i] == "MALICIOUS" and is_tor[i] == 1)
            c4 = (dns_queries_sec[i] > 300 and bytes_out_mb[i] > 120.0)
            block_ip[i] = 1 if (c1 or c2 or c3 or c4) else 0

        return pd.DataFrame({
            "failed_logins_5m": failed_logins,
            "packet_rate_kpps": np.round(packet_rate, 1),
            "port_scan_count": port_scans,
            "bytes_out_mb": bytes_out_mb,
            "dns_queries_sec": dns_queries_sec,
            "ssh_failed_count": ssh_failed_count,
            "country_reputation": country_rep,
            "protocol": protocol,
            "is_tor_exit_node": is_tor,
            "privileged_account_targeted": priv_account,
            "block_ip_address": block_ip
        })

    @staticmethod
    def generate_clinical_triage_sample(n_records: int = 500, seed: int = 404) -> pd.DataFrame:
        """
        Generates Hospital Emergency Room Clinical Triage records.
        Target: urgent_icu_triage (0 or 1).
        """
        np.random.seed(seed)
        heart_rate = np.clip(np.random.normal(loc=82.0, scale=24.0, size=n_records).astype(int), 45, 180)
        systolic_bp = np.clip(np.random.normal(loc=125.0, scale=28.0, size=n_records).astype(int), 75, 230)
        spo2 = np.clip(np.random.normal(loc=97.0, scale=3.5, size=n_records).astype(int), 75, 100)
        pain_score = np.random.choice(range(11), size=n_records)
        temp_c = np.round(np.random.normal(loc=37.0, scale=0.9, size=n_records), 1)
        resp_rate = np.clip(np.random.normal(loc=18.0, scale=5.0, size=n_records).astype(int), 8, 42)
        glucose = np.random.randint(65, 380, size=n_records)
        age_group = np.random.choice(["PEDIATRIC", "ADULT", "GERIATRIC"], size=n_records, p=[0.20, 0.55, 0.25])

        urgent_icu = np.zeros(n_records, dtype=int)
        for i in range(n_records):
            c1 = (spo2[i] < 90)
            c2 = (systolic_bp[i] > 180 and heart_rate[i] > 120)
            c3 = (age_group[i] == "GERIATRIC" and systolic_bp[i] < 90 and heart_rate[i] > 110)
            c4 = (temp_c[i] > 39.5 and resp_rate[i] > 30)
            c5 = (glucose[i] > 320 and heart_rate[i] > 115)
            urgent_icu[i] = 1 if (c1 or c2 or c3 or c4 or c5) else 0

        return pd.DataFrame({
            "heart_rate_bpm": heart_rate,
            "systolic_bp": systolic_bp,
            "spo2_pct": spo2,
            "pain_score": pain_score,
            "temperature_c": temp_c,
            "respiratory_rate": resp_rate,
            "blood_glucose_mg_dl": glucose,
            "age_group": age_group,
            "urgent_icu_triage": urgent_icu
        })

    @staticmethod
    def generate_support_conversations_sample(n_records: int = 500, seed: int = 505) -> pd.DataFrame:
        """
        Generates realistic unstructured customer support dialogue sessions and user messages.
        Target: escalate_to_supervisor (0 or 1).
        """
        np.random.seed(seed)

        escalation_templates = [
            "I was charged twice for the subscription this month on my credit card and nobody is answering my emails. This is a scam, cancel my account and refund my money immediately or I will take legal action.",
            "The system is completely down, returning error 500 when trying to invoice my clients. This is critical, our business operations are completely halted right now!",
            "I want to cancel the service immediately. The support is terrible and I have been waiting a week for someone to resolve a billing issue.",
            "This is the third time I contact support regarding the same bug on the main dashboard. Nobody gives a clear answer and I still cannot work. I demand to speak with a supervisor.",
            "Unauthorized charge on my card for $180.00. I did not authorize this charge and demand an immediate refund. This is unacceptable!",
            "The platform crashes every 5 minutes and we lost all session data. This is critical, we are in the middle of an urgent accounting close!",
            "Terrible customer service. My account has been blocked for 3 days without reason. If you do not resolve it today I will initiate legal action with my lawyer.",
            "Critical server error. All orders today were duplicated. I need an immediate solution before they are dispatched.",
            "Nobody is answering on chat and my access is still blocked since yesterday. This service is awful, I demand to speak with a manager right now!",
            "My subscription fee was changed without prior notice and I was charged double. You are scammers, cancel everything and I want my money back.",
        ]

        standard_templates = [
            "Hello, good morning. Could you please tell me what payment methods are available and your phone support hours? Thank you very much.",
            "Thank you so much for the quick help, everything is resolved and the system works great. Best regards.",
            "Hello! I wanted to inquire if you have a guide to export reports into Excel or PDF format. Looking forward to your response.",
            "Good afternoon, I would like to update the email address associated with my user. Which section in the dashboard can I do this in?",
            "Thank you very much for the support received on the previous ticket, the agent was very kind and resolved my inquiry quickly.",
            "Hello, I just wanted to confirm if you will be answering live chat inquiries next Monday during the holiday. Thanks!",
            "Dear team, I wanted to congratulate you on the new dashboards feature, it has been extremely helpful for our team.",
            "Good afternoon, could you please send me a copy of last month's payment receipt for our accounting department? Thank you very much.",
            "Hello, how can I invite another member of my team to access the admin panel? Thanks in advance.",
            "Good morning, I received the monthly invoice correctly. Do you have automated bank direct debit available? Best regards.",
        ]

        records = []
        for i in range(n_records):
            is_escalate = np.random.choice([0, 1], p=[0.52, 0.48])
            if is_escalate == 1:
                base_text = np.random.choice(escalation_templates)
                channel = np.random.choice(["CHAT_WEB", "EMAIL", "WHATSAPP", "PHONE"], p=[0.40, 0.30, 0.20, 0.10])
                turns = np.random.randint(2, 7)
                customer_tier = np.random.choice(["FREE", "STANDARD", "PREMIUM", "VIP", "ENTERPRISE"], p=[0.25, 0.35, 0.20, 0.12, 0.08])
                account_age_months = np.random.randint(1, 36)
                pending_invoices = np.random.choice([0, 1, 2, 3], p=[0.60, 0.25, 0.10, 0.05])
                response_wait_min = np.round(np.random.uniform(15.0, 180.0), 1)
                sentiment_score = np.round(np.random.uniform(0.05, 0.35), 2)
            else:
                base_text = np.random.choice(standard_templates)
                channel = np.random.choice(["CHAT_WEB", "EMAIL", "WHATSAPP", "PHONE"], p=[0.45, 0.30, 0.20, 0.05])
                turns = np.random.randint(1, 4)
                customer_tier = np.random.choice(["FREE", "STANDARD", "PREMIUM", "VIP", "ENTERPRISE"], p=[0.30, 0.40, 0.18, 0.08, 0.04])
                account_age_months = np.random.randint(1, 48)
                pending_invoices = np.random.choice([0, 1], p=[0.92, 0.08])
                response_wait_min = np.round(np.random.uniform(1.0, 25.0), 1)
                sentiment_score = np.round(np.random.uniform(0.65, 0.98), 2)

            records.append({
                "conversation_id": f"conv-{1000 + i}",
                "channel": channel,
                "customer_tier": customer_tier,
                "turn_count": turns,
                "account_age_months": account_age_months,
                "pending_invoices": pending_invoices,
                "response_wait_min": response_wait_min,
                "sentiment_score": sentiment_score,
                "user_message": base_text,
                "escalate_to_supervisor": is_escalate,
            })

        return pd.DataFrame(records)
