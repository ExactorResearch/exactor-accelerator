"""
Exactor Accelerator: High-Speed Boolean Logic Layer for TypeSafe AI

Combines EXACTOR boolean minimization (Rust) with Jev (TypeSafe AI)
to accelerate decisions by 4,770-24,000x with 95-100% accuracy.
"""

__version__ = "2.0.11"
__author__ = "Exactor Contributors"
__license__ = "MIT"

from .config import configure, get_config
from .ingestion import AdaptiveBinarizer, DataLoader, Proposition, BinarizationResult, SemanticPropositionDiscovery
from .core import ExactorBridge, ExactorHypercubeReducer, ExactorSimplificationResult
from .adapter import ExactorToJevTranslator, JevPayload, NoulQuestion, ChoiceQuestion, ScoreQuestion
from .ledger import MemoryLedger
from .engine import JevClient, HybridRuntime, QueryResult
from .sklearn_interface import ExactorAcceleratorClassifier, ExactorAcceleratorMultiLabelClassifier
from .model_persistence import save_model, load_model, log_to_mlflow, log_to_wandb
from .sdk import ExactorAccelerator
from .feature_engine import get_feature_engine, DomainFeatureEngine
from .regime_detector import get_regime_detector, DomainRegimeDetector


__all__ = [
    # Top-level API
    "configure",
    "get_config",
    "ExactorAccelerator",
    "ExactorAcceleratorClassifier",
    "ExactorAcceleratorMultiLabelClassifier",
    "get_feature_engine",
    "DomainFeatureEngine",
    "get_regime_detector",
    "DomainRegimeDetector",
    # Model persistence
    "save_model",
    "load_model",
    "log_to_mlflow",
    "log_to_wandb",
    # Ingestion
    "SemanticPropositionDiscovery",
    "AdaptiveBinarizer",
    "DataLoader",
    "Proposition",
    "BinarizationResult",
    # Core
    "ExactorBridge",
    "ExactorHypercubeReducer",
    "ExactorSimplificationResult",
    # Adapter
    "ExactorToJevTranslator",
    "JevPayload",
    "NoulQuestion",
    "ChoiceQuestion",
    "ScoreQuestion",
    # Ledger & Engine
    "MemoryLedger",
    "JevClient",
    "HybridRuntime",
    "QueryResult",
]
