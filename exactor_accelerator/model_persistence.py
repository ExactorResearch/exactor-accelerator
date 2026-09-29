"""
Model Artifact Persistence, Serialization and Serving for ExactorAccelerator.
Enables exactor_accelerator.save_model("model.ej"), exactor_accelerator.load_model("model.ej"),
MLflow / Weights & Biases logging, and standalone REST deployment.
"""

from typing import Dict, Any, Optional, Union
import pickle
import json
import gzip
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger("exactor_accelerator.serialization")


def save_model(model: Any, filepath: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Serializes and saves an ExactorAccelerator or ExactorAcceleratorClassifier model to a compact artifact file (.ea / .ej).
    
    Parameters:
    -----------
    model : ExactorAccelerator o ExactorAcceleratorClassifier
        Trained model instance.
    filepath : str
        Destination file path (e.g. 'fraud_detector_v1.ea').
    metadata : dict, optional
        Additional metadata (author, environment, metrics, tags).
    """
    if not filepath.endswith(".ej"):
        filepath += ".ej"

    payload = {
        "format_version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_type": model.__class__.__name__,
        "metadata": metadata or {},
        "model_state": model,
    }

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with gzip.open(filepath, "wb") as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

    logger.info(f"ExactorAccelerator model successfully saved at: {filepath}")
    return filepath


def load_model(filepath: str) -> Any:
    """
    Loads a previously saved ExactorAccelerator model from an artifact file (.ea / .ej).
    """
    if not os.path.exists(filepath):
        if os.path.exists(filepath + ".ej"):
            filepath += ".ej"
        else:
            raise FileNotFoundError(f"Model file not found: {filepath}")

    with gzip.open(filepath, "rb") as f:
        payload = pickle.load(f)

    logger.info(f"Model {payload.get('model_type')} v{payload.get('format_version')} loaded from: {filepath}")
    return payload["model_state"]


# =============================================================================
# INTEGRACIONES CON MLFLOW Y WEIGHTS & BIASES (WANDB)
# =============================================================================

def log_to_mlflow(model: Any, run_name: Optional[str] = None, metrics: Optional[Dict[str, float]] = None):
    """Logs the ExactorAccelerator model, its boolean formula, and metrics to MLflow."""
    try:
        import mlflow
        with mlflow.start_run(run_name=run_name or "ExactorAccelerator-Run"):
            # Log parameters
            params = model.get_params() if hasattr(model, "get_params") else {}
            mlflow.log_params(params)
            
            # Log logical formula
            formula = getattr(model, "formula_expr_", None)
            if not formula and hasattr(model, "runtime") and model.runtime.current_rule:
                formula = model.runtime.current_rule.formula_expr
            if formula:
                mlflow.log_text(formula, "exactor_boolean_formula.txt")

            # Log metrics
            if metrics:
                mlflow.log_metrics(metrics)

            # Save artifact
            tmp_path = "model_artifact.ea"
            save_model(model, tmp_path)
            mlflow.log_artifact(tmp_path, artifact_path="model")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            logger.info("ExactorAccelerator model successfully logged to MLflow.")
    except ImportError:
        logger.warning("MLflow is not installed. Install with `pip install mlflow` to enable tracking.")


def log_to_wandb(model: Any, project: str = "exactor-accelerator", run_name: Optional[str] = None, metrics: Optional[Dict[str, float]] = None):
    """Logs the ExactorAccelerator model and metrics to Weights & Biases (wandb)."""
    try:
        import wandb
        run = wandb.init(project=project, name=run_name, reinit=True)
        # Log config
        params = model.get_params() if hasattr(model, "get_params") else {}
        wandb.config.update(params)
        
        formula = getattr(model, "formula_expr_", None)
        if not formula and hasattr(model, "runtime") and model.runtime.current_rule:
            formula = model.runtime.current_rule.formula_expr
        if formula:
            wandb.summary["formula_booleana"] = formula

        if metrics:
            wandb.log(metrics)
            
        wandb.finish()
        logger.info("ExactorAccelerator model successfully logged to Weights & Biases.")
    except ImportError:
        logger.warning("Weights & Biases (wandb) is not installed. Install with `pip install wandb`.")
