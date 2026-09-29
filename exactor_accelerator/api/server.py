"""
FastAPI Server for EXACTOR + Jev Hybrid System.
Exposes REST endpoints for Phase A Ingestion, Phase B Real-time Jev decisions,
Memory Ledger streaming, and Differential Hot Updates.
"""

from typing import Dict, Any, Optional, List
import os
import io
import json
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from ..engine.runtime import HybridRuntime
from ..ingestion.loader import DataLoader

logger = logging.getLogger("exactor_accelerator.api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="EXACTOR + Jev Hybrid Architecture API",
    description="Live Memory and Incremental Decision Engine combining Boolean Minimization with TypeSafe AI System One Models",
    version="1.0.0",
)

class ConfigCredentialsRequest(BaseModel):
    exactor_token: Optional[str] = Field(None, description="EXACTOR API key or token")
    exactor_base_url: Optional[str] = Field(None, description="EXACTOR service URL")
    use_cloud_exactor: Optional[bool] = Field(None, description="Enable remote EXACTOR cloud calls")
    jev_token: Optional[str] = Field(None, description="TypeSafe AI Jev API key")
    deepseek_api_key: Optional[str] = Field(None, description="DeepSeek LLM API key")


class CustomChoicesRequest(BaseModel):
    choices: Dict[str, Optional[str]] = Field(..., description="Map of action choice name to criteria description")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize master runtime
DB_PATH = os.environ.get("exactor_accelerator_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "memory_ledger.db"))
runtime = HybridRuntime(db_path=DB_PATH, default_threshold=0.80)


def _mask_token(token: Optional[str]) -> str:
    if not token:
        return "No configurado"
    if len(token) <= 8:
        return "****"
    return token[:4] + "..." + token[-4:]


@app.get("/api/config/tokens")
def get_config_tokens():
    """Returns current active tokens and credentials status (masked)."""
    return {
        "exactor": {
            "is_configured": bool(runtime.bridge.api_key),
            "masked_token": _mask_token(runtime.bridge.api_key),
            "cloud_base_url": runtime.bridge.cloud_base_url,
            "use_cloud_api": runtime.bridge.use_cloud_api,
            "is_rust_native": runtime.bridge.is_rust_native,
        },
        "jev": {
            "is_configured": bool(runtime.jev_client.api_key) and not runtime.jev_client.use_mock_simulator,
            "masked_token": _mask_token(runtime.jev_client.api_key),
            "use_mock_simulator": runtime.jev_client.use_mock_simulator,
            "base_url": runtime.jev_client.base_url,
        },
        "deepseek": {
            "is_configured": bool(runtime.deepseek_explainer.api_key),
            "masked_token": _mask_token(runtime.deepseek_explainer.api_key),
            "model": runtime.deepseek_explainer.model,
        },
    }


@app.post("/api/config/tokens")
def update_config_tokens(req: ConfigCredentialsRequest):
    """Updates live tokens and endpoints for EXACTOR, Jev, and DeepSeek."""
    runtime.update_credentials(
        exactor_api_key=req.exactor_token,
        exactor_base_url=req.exactor_base_url,
        use_cloud_exactor=req.use_cloud_exactor,
        jev_api_key=req.jev_token,
        deepseek_api_key=req.deepseek_api_key,
    )
    return {
        "status": "SUCCESS",
        "message": "Credenciales y tokens actualizados en vivo.",
        "config": get_config_tokens(),
    }

# Auto-onboard default sample dataset on startup if not initialized
@app.on_event("startup")
def startup_event():
    try:
        sample_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sample_fraud_transactions.csv")
        if os.path.exists(sample_csv):
            import pandas as pd
            df = pd.read_csv(sample_csv)
            runtime.phase_a_onboard(df, target_col="is_fraud", max_variables=32, trigger_reason="STARTUP_DEFAULT_ONBOARDING")
            logger.info("Startup: Auto-onboarded Fintech Fraud dataset successfully.")

            # Seed initial ledger entries if ledger is sparse
            if runtime.ledger.get_total_count() < 8:
                seed_events = [
                    {"amount": 3450.00, "velocity_1h": 6, "country_risk": "HIGH", "device_trust": 0.12, "failed_pin_attempts": 3, "is_new_device": 1},
                    {"amount": 18.50, "velocity_1h": 1, "country_risk": "LOW", "device_trust": 0.98, "failed_pin_attempts": 0, "is_new_device": 0},
                    {"amount": 42.00, "velocity_1h": 1, "country_risk": "LOW", "device_trust": 0.91, "failed_pin_attempts": 0, "is_new_device": 0},
                    {"amount": 1890.00, "velocity_1h": 4, "country_risk": "MEDIUM", "device_trust": 0.31, "failed_pin_attempts": 2, "is_new_device": 1},
                    {"amount": 89.90, "velocity_1h": 2, "country_risk": "LOW", "device_trust": 0.88, "failed_pin_attempts": 0, "is_new_device": 0},
                    {"amount": 4100.00, "velocity_1h": 7, "country_risk": "HIGH", "device_trust": 0.08, "failed_pin_attempts": 3, "is_new_device": 1},
                    {"amount": 650.00, "velocity_1h": 2, "country_risk": "MEDIUM", "device_trust": 0.65, "failed_pin_attempts": 1, "is_new_device": 0},
                    {"amount": 12.00, "velocity_1h": 1, "country_risk": "LOW", "device_trust": 0.99, "failed_pin_attempts": 0, "is_new_device": 0},
                    {"amount": 2750.00, "velocity_1h": 5, "country_risk": "HIGH", "device_trust": 0.22, "failed_pin_attempts": 2, "is_new_device": 1},
                    {"amount": 150.00, "velocity_1h": 1, "country_risk": "LOW", "device_trust": 0.85, "failed_pin_attempts": 0, "is_new_device": 0},
                ]
                for evt in seed_events:
                    runtime.phase_b_query(evt, confidence_threshold=0.80)
                logger.info("Startup: Pre-seeded initial live interactions into WAL memory ledger.")
    except Exception as e:
        logger.warning(f"Could not auto-onboard default sample on startup: {e}")


# Pydantic models
class LiveQueryRequest(BaseModel):
    state: Dict[str, Any] = Field(..., description="Unstructured or structured real-time event state")
    confidence_threshold: Optional[float] = Field(0.80, description="Autonomous execution confidence threshold (0.0 to 1.0)")
    query_id: Optional[str] = Field(None, description="Optional custom query tracking ID")


class ExplainRequest(BaseModel):
    state: Dict[str, Any] = Field(..., description="Raw event state")
    propositions_evaluated: Dict[str, int] = Field(..., description="Boolean evaluated propositions (bit values 0/1)")
    exact_boolean_evaluation: int = Field(0, description="Exactor exact hypercube outcome (0 or 1)")
    criterio_logico_prob: float = Field(..., description="Jev calibrated probability")
    chosen_action: str = Field(..., description="Chosen business action")
    autonomous_action_executed: bool = Field(False, description="Whether action was autonomously executed")


class FeedbackRequest(BaseModel):
    query_id: str
    label: int = Field(..., description="Verified ground truth label (0 or 1)")


class DifferentialUpdateRequest(BaseModel):
    window_size: int = Field(30, description="Sliding window size of recent interactions to evaluate")


# -----------------------------------------------------------------------------
# REST API Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/system/status")
def get_system_status():
    """Returns general runtime health, rule version, and ledger statistics."""
    latest_rule_meta = runtime.ledger.get_latest_rules_version()
    total_ledger = runtime.ledger.get_total_count()

    return {
        "status": "ONLINE",
        "is_initialized": runtime.is_initialized,
        "active_rule_version": runtime.current_rule_version,
        "hypercube_dimension_k": len(runtime.binarizer.variables) if runtime.is_initialized else 0,
        "variables": runtime.binarizer.variables if runtime.is_initialized else [],
        "total_ledger_interactions": total_ledger,
        "jev_model": runtime.jev_client.use_mock_simulator and "jev-latest (RLCD Calibrated Simulator)" or "jev-latest (TypeSafe AI Live API)",
        "engine_type": runtime.bridge.is_rust_native and "exactor-core-rust" or "exactor-hypercube-gray-reduction",
        "latest_rule": latest_rule_meta,
    }


@app.post("/api/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    target_col: str = Form(...),
    max_variables: int = Form(32),
):
    """
    Phase A: Upload historical CSV or JSON file and run Exactor Logic Discovery.
    """
    content = await file.read()
    try:
        df = DataLoader.load_from_bytes(content, file.filename)
        if target_col not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Columna objetivo '{target_col}' no encontrada en el archivo. Columnas disponibles: {list(df.columns)}",
            )
        result = runtime.phase_a_onboard(df, target_col=target_col, max_variables=max_variables, trigger_reason="MANUAL_FILE_UPLOAD")
        return result
    except Exception as e:
        logger.error(f"Error ingesting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/samples/catalog")
def get_samples_catalog():
    """Returns catalog of all available domain sample datasets with metadata and test events."""
    return {
        "samples": [
            {
                "id": "fraud",
                "name": "Fintech: Fraud Detection",
                "description": "Banking transactions with continuous amounts, velocity, and risk indicators.",
                "target_col": "is_fraud",
                "records": 500,
                "file": "sample_fraud_transactions.csv",
                "test_events": {
                    "anomalous": {"amount": 3400.0, "velocity_1h": 6, "country_risk": "HIGH", "device_trust": 0.12, "failed_pin_attempts": 3, "is_new_device": 1},
                    "legitimate": {"amount": 25.50, "velocity_1h": 1, "country_risk": "LOW", "device_trust": 0.95, "failed_pin_attempts": 0, "is_new_device": 0},
                    "borderline": {"amount": 850.0, "velocity_1h": 2, "country_risk": "MEDIUM", "device_trust": 0.50, "failed_pin_attempts": 1, "is_new_device": 1},
                }
            },
            {
                "id": "sre",
                "name": "Cloud SRE: Latency & Incident Telemetry",
                "description": "Microservice metrics, p99 latency, HTTP error rate, and CPU saturation.",
                "target_col": "trigger_mitigation",
                "records": 500,
                "file": "sample_sre_incidents.json",
                "test_events": {
                    "anomalous": {"latency_ms": 420.0, "error_rate_pct": 14.5, "cpu_usage_pct": 94.0, "retry_bursts": 5, "service_tier": "TIER_1_CRITICAL"},
                    "legitimate": {"latency_ms": 35.0, "error_rate_pct": 0.05, "cpu_usage_pct": 42.0, "retry_bursts": 0, "service_tier": "TIER_2_CORE"},
                    "borderline": {"latency_ms": 180.0, "error_rate_pct": 2.8, "cpu_usage_pct": 78.0, "retry_bursts": 2, "service_tier": "TIER_1_CRITICAL"},
                }
            },
            {
                "id": "churn",
                "name": "SaaS / E-Commerce: Customer Churn",
                "description": "Subscription churn prediction based on tenure, tickets, and contract terms.",
                "target_col": "churn",
                "records": 500,
                "file": "sample_customer_churn.csv",
                "test_events": {
                    "anomalous": {"tenure_months": 3, "monthly_charges": 98.50, "support_tickets_30d": 4, "contract_type": "MONTH_TO_MONTH", "has_tech_support": 0, "payment_method": "ELECTRONIC_CHECK"},
                    "legitimate": {"tenure_months": 48, "monthly_charges": 45.00, "support_tickets_30d": 0, "contract_type": "TWO_YEAR", "has_tech_support": 1, "payment_method": "BANK_TRANSFER"},
                    "borderline": {"tenure_months": 11, "monthly_charges": 68.00, "support_tickets_30d": 2, "contract_type": "ONE_YEAR", "has_tech_support": 0, "payment_method": "CREDIT_CARD"},
                }
            },
            {
                "id": "soc",
                "name": "Cybersecurity SOC: Network Intrusion",
                "description": "SIEM telemetry from failed logins, packet rate, and port scanning.",
                "target_col": "block_ip_address",
                "records": 500,
                "file": "sample_soc_intrusion.json",
                "test_events": {
                    "anomalous": {"failed_logins_5m": 12, "packet_rate_kpps": 140.0, "port_scan_count": 85, "country_reputation": "MALICIOUS", "is_tor_exit_node": 1, "privileged_account_targeted": 1},
                    "legitimate": {"failed_logins_5m": 0, "packet_rate_kpps": 15.0, "port_scan_count": 0, "country_reputation": "TRUSTED", "is_tor_exit_node": 0, "privileged_account_targeted": 0},
                    "borderline": {"failed_logins_5m": 3, "packet_rate_kpps": 48.0, "port_scan_count": 2, "country_reputation": "NEUTRAL", "is_tor_exit_node": 0, "privileged_account_targeted": 1},
                }
            },
            {
                "id": "triage",
                "name": "Healthcare: Emergency Clinical Triage",
                "description": "Patient vital signs (SpO2, blood pressure, heart rate, and pain score).",
                "target_col": "urgent_icu_triage",
                "records": 500,
                "file": "sample_clinical_triage.csv",
                "test_events": {
                    "anomalous": {"heart_rate_bpm": 145, "systolic_bp": 195, "spo2_pct": 84, "pain_score": 9, "age_group": "GERIATRIC"},
                    "legitimate": {"heart_rate_bpm": 72, "systolic_bp": 118, "spo2_pct": 99, "pain_score": 2, "age_group": "ADULT"},
                    "borderline": {"heart_rate_bpm": 105, "systolic_bp": 145, "spo2_pct": 93, "pain_score": 5, "age_group": "PEDIATRIC"},
                }
            },
            {
                "id": "conversations",
                "name": "💬 Customer Support: Dialogues & Unstructured Text",
                "description": "Unstructured chat text extracting intent matrices, billing issues, and urgency for Boolean acceleration.",
                "target_col": "escalate_to_supervisor",
                "records": 500,
                "file": "sample_support_conversations.json",
                "test_events": {
                    "anomalous": {"user_message": "I was charged twice for the subscription this month on my credit card and nobody answers my emails. This is a scam, cancel my account and refund my money immediately or I will take legal action."},
                    "legitimate": {"user_message": "Hello, good morning. Could you tell me what payment methods are available and what your telephone support hours are? Thank you very much."},
                    "borderline": {"user_message": "Good afternoon, I wanted to check if you will be available for live chat support next Monday during the holiday. Thank you!"},
                }
            }
        ]
    }


@app.post("/api/ingest/sample")
def ingest_sample(
    sample_type: str = Query("fraud", description="'fraud', 'sre', 'churn', 'soc', 'triage', or 'conversations'"),
    max_variables: int = Query(32, description="Max boolean propositions for hypercube"),
):
    """
    Phase A: Onboard pre-packaged sample dataset for instant testing.
    """
    try:
        sample_lower = sample_type.lower()
        if sample_lower == "sre":
            df = DataLoader.generate_sre_incident_sample(n_records=500)
            target = "trigger_mitigation"
        elif sample_lower == "churn":
            df = DataLoader.generate_customer_churn_sample(n_records=500)
            target = "churn"
        elif sample_lower == "soc":
            df = DataLoader.generate_cybersecurity_soc_sample(n_records=500)
            target = "block_ip_address"
        elif sample_lower == "triage":
            df = DataLoader.generate_clinical_triage_sample(n_records=500)
            target = "urgent_icu_triage"
        elif sample_lower in ("conversations", "support", "chat", "texto"):
            df = DataLoader.generate_support_conversations_sample(n_records=500)
            target = "escalate_to_supervisor"
        else:
            df = DataLoader.generate_fintech_fraud_sample(n_records=500)
            target = "is_fraud"

        result = runtime.phase_a_onboard(
            df,
            target_col=target,
            max_variables=max_variables,
            trigger_reason=f"SAMPLE_{sample_lower.upper()}_ONBOARDING"
        )
        return result
    except Exception as e:
        logger.error(f"Error onboarding sample: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/exactor/rules")
def get_exactor_rules():
    """Returns the active synthesized Boolean rules and Hypercube statistics."""
    if not runtime.is_initialized or runtime.current_rule is None:
        raise HTTPException(status_code=400, detail="El motor Exactor no ha sido inicializado con datos.")

    return {
        "rule_version": runtime.current_rule_version,
        "formula_expr": runtime.current_rule.formula_expr,
        "xor_clauses": runtime.current_rule.xor_clauses,
        "terms": [t.to_string(runtime.current_rule.variables) for t in runtime.current_rule.terms],
        "variables": runtime.current_rule.variables,
        "propositions": [p.to_dict() for p in runtime.binarizer.propositions],
        "initial_minterms": runtime.current_rule.initial_minterm_count,
        "final_terms": runtime.current_rule.final_term_count,
        "compression_ratio": round(1.0 - (runtime.current_rule.final_term_count / max(1, runtime.current_rule.initial_minterm_count)), 4),
        "stats": runtime.current_rule.stats,
        "explanation": runtime.translator.generate_human_explanation(runtime.current_rule, runtime.propositions_map),
    }


@app.get("/api/jev/schema")
def get_jev_schema():
    """Returns the calibrated TypeSafe AI Jev questions schema."""
    if not runtime.is_initialized or runtime.current_rule is None:
        raise HTTPException(status_code=400, detail="The system is not initialized.")

    questions = runtime.translator.create_questions_schema(
        result=runtime.current_rule,
        propositions_map=runtime.propositions_map,
        custom_action_choices=runtime.custom_action_choices,
    )
    serialized_q = {k: getattr(v, "to_dict", lambda: v)() for k, v in questions.items()}

    # Sample payload preview
    sample_state = {"monto": 2450.0, "intentos_fallidos": 2, "pais_riesgoso": "HIGH"}
    sample_payload = runtime.translator.build_payload(
        raw_event_state=sample_state,
        result=runtime.current_rule,
        propositions_map=runtime.propositions_map,
        custom_action_choices=runtime.custom_action_choices,
    )

    return {
        "model": "jev-latest",
        "questions_schema": serialized_q,
        "sample_payload_preview": sample_payload.to_dict(),
        "custom_choices": runtime.custom_action_choices,
    }


@app.post("/api/jev/choices")
def update_jev_choices(req: CustomChoicesRequest):
    """
    Updates custom business Choice actions for JEV evaluation.
    Noul logic evaluation remains reserved for EXACTOR hypercube governance.
    """
    try:
        runtime.set_choices(req.choices)
        return {
            "status": "SUCCESS",
            "message": f"Catalog of {len(req.choices)} Choice options updated successfully.",
            "choices": runtime.custom_action_choices,
        }
    except Exception as e:
        logger.error(f"Error updating Jev choices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
def execute_query(req: LiveQueryRequest):
    """
    Phase B: Real-Time Event Evaluation.
    Processes state through Jev in milliseconds, triggers autonomous action,
    and logs immediately into the SQLite WAL Memory Ledger.
    """
    if not runtime.is_initialized:
        raise HTTPException(status_code=400, detail="Sistema no inicializado. Ejecute la Fase A primero.")

    try:
        res = runtime.phase_b_query(
            raw_state=req.state,
            confidence_threshold=req.confidence_threshold,
            query_id=req.query_id,
        )
        return res.to_dict()
    except Exception as e:
        logger.error(f"Error in Phase B query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/explain")
def explain_decision(req: ExplainRequest):
    """
    Generates rich Causal & Audit Explanation using DeepSeek LLM,
    grounding the reasoning strictly on active B^32 propositions and Exactor/Jev outcomes.
    """
    try:
        rule_formula = runtime.current_rule.formula_expr if runtime.current_rule else None
        explanation = runtime.deepseek_explainer.generate_explanation(
            event_state=req.state,
            active_propositions=req.propositions_evaluated,
            exact_eval=req.exact_boolean_evaluation,
            criterio_prob=req.criterio_logico_prob,
            chosen_action=req.chosen_action,
            autonomous_executed=req.autonomous_action_executed,
            rule_formula=rule_formula,
        )
        return explanation
    except Exception as e:
        logger.error(f"Error generating DeepSeek explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ledger")
def get_ledger(limit: int = 50, offset: int = 0):
    """Returns the recent stream of live queries from SQLite WAL."""
    entries = runtime.ledger.get_recent_entries(limit=limit, offset=offset)
    total = runtime.ledger.get_total_count()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "entries": entries,
    }


@app.post("/api/ledger/feedback")
def submit_feedback(req: FeedbackRequest):
    """Records human verification or ground truth for a previous query."""
    runtime.ledger.record_feedback(query_id=req.query_id, label=req.label)
    return {"status": "SUCCESS", "query_id": req.query_id, "label": req.label}


@app.post("/api/differential/update")
def trigger_differential_update(req: DifferentialUpdateRequest):
    """
    Triggers incremental differential Exactor rule update on the sliding window
    without offline retraining.
    """
    try:
        res = runtime.trigger_differential_update(window_size=req.window_size)
        return res
    except Exception as e:
        logger.error(f"Differential update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Static frontend hosting
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))
